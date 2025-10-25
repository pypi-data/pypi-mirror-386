"""Session implementation backed by :mod:`pycurl`."""

from __future__ import annotations

import base64
import io
import json as jsonlib
import os
import urllib.parse
import urllib.request
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from http.client import HTTPMessage
from http.cookiejar import CookieJar

from .adapters import HTTPAdapter
from .exceptions import InvalidSchema, MissingSchema, TooManyRedirects
from .models import PreparedRequest, Request, Response
from .utils import CaseInsensitiveDict

_DEFAULT_HEADERS = CaseInsensitiveDict(
    {
        "User-Agent": "req2/0.1.0",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "*/*",
    }
)

_REDIRECT_STATUSES = {301, 302, 303, 307, 308}


@dataclass
class _MultipartItem:
    name: str
    body: bytes
    filename: str | None = None
    content_type: str | None = None
    headers: Mapping[str, str] | None = None


class Session:
    """Requests-compatible session that executes requests via :mod:`pycurl`."""

    def __init__(self) -> None:
        self.headers = _DEFAULT_HEADERS.copy()
        self.params: dict[str, Any] = {}
        self.max_redirects = 30
        self.cookies = CookieJar()
        self.auth: Any = None
        self.proxies: dict[str, str] = {}
        self.trust_env = True
        self.verify: bool | str = True
        self.cert: str | tuple[str, str] | None = None
        self.hooks: dict[str, list[Any]] = {"response": []}
        self.adapters: dict[str, HTTPAdapter] = {}
        default_adapter = HTTPAdapter()
        self.mount("http://", default_adapter)
        self.mount("https://", default_adapter)

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------
    def __enter__(self) -> "Session":  # pragma: no cover - trivial
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - trivial
        self.close()

    # ------------------------------------------------------------------
    # Public request API
    # ------------------------------------------------------------------
    def request(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        data: Any | None = None,
        json: Any | None = None,
        files: Mapping[str, Any] | Iterable[tuple[str, Any]] | None = None,
        headers: Mapping[str, str] | None = None,
        cookies: Mapping[str, str] | CookieJar | None = None,
        timeout: float | tuple[float | None, float | None] | None = None,
        allow_redirects: bool | None = None,
        verify: bool | str | None = None,
        cert: str | tuple[str, str] | None = None,
        stream: bool = False,
        proxies: Mapping[str, str] | None = None,
        auth: Any = None,
        hooks: Mapping[str, Iterable[Any]] | None = None,
        **kwargs: Any,
    ) -> Response:
        if kwargs:
            # Consume unsupported kwargs silently for compatibility
            kwargs.clear()

        if allow_redirects is None:
            allow_redirects = method.upper() != "HEAD"

        hooks = self._merge_hooks(hooks)
        prepared = self._prepare_request(
            method,
            url,
            params=params,
            data=data,
            json=json,
            files=files,
            headers=headers,
            cookies=cookies,
            hooks=hooks,
        )

        request_auth = auth if auth is not None else self.auth
        auth_tuple: tuple[str, str] | None = None
        if request_auth:
            if callable(request_auth) and not isinstance(request_auth, tuple):
                request_auth(prepared)
            else:
                auth_tuple = request_auth  # type: ignore[assignment]
                if (
                    auth_tuple is not None
                    and len(auth_tuple) == 2
                    and "Authorization" not in prepared.headers
                ):
                    user, password = auth_tuple
                    # RFC 7617 requires the credential string to be encoded as ISO-8859-1
                    # prior to base64 encoding. ``str`` values are assumed to already be
                    # unicode, so we encode using latin-1 to preserve byte values.
                    credentials = f"{user}:{password}".encode("latin-1")
                    token = base64.b64encode(credentials).decode("ascii")
                    prepared.headers["Authorization"] = f"Basic {token}"

        settings = self.merge_environment_settings(
            prepared.url,
            proxies,
            stream,
            verify if verify is not None else self.verify,
            cert if cert is not None else self.cert,
        )

        response = self.send(
            prepared,
            timeout=timeout,
            allow_redirects=allow_redirects,
            verify=settings["verify"],
            cert=settings["cert"],
            stream=stream,
            proxies=settings["proxies"],
            auth=auth_tuple,
        )
        return response

    def get(self, url: str, **kwargs: Any) -> Response:
        kwargs.setdefault("allow_redirects", True)
        return self.request("GET", url, **kwargs)

    def options(self, url: str, **kwargs: Any) -> Response:
        kwargs.setdefault("allow_redirects", True)
        return self.request("OPTIONS", url, **kwargs)

    def head(self, url: str, **kwargs: Any) -> Response:
        kwargs.setdefault("allow_redirects", False)
        return self.request("HEAD", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> Response:
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs: Any) -> Response:
        return self.request("PUT", url, **kwargs)

    def patch(self, url: str, **kwargs: Any) -> Response:
        return self.request("PATCH", url, **kwargs)

    def delete(self, url: str, **kwargs: Any) -> Response:
        return self.request("DELETE", url, **kwargs)

    def prepare_request(self, request: Request) -> PreparedRequest:
        hooks = self._merge_hooks(request.hooks)
        return self._prepare_request(
            request.method,
            request.url,
            params=request.params,
            data=request.data,
            json=request.json,
            files=request.files,
            headers=request.headers,
            cookies=None,
            hooks=hooks,
        )

    # ------------------------------------------------------------------
    # Adapter compatibility stubs
    # ------------------------------------------------------------------
    def get_adapter(self, url: str) -> HTTPAdapter:  # pragma: no cover - compatibility hook
        if not self.adapters:
            raise InvalidSchema("No adapters registered")
        lowered = url.lower()
        matches = [prefix for prefix in self.adapters if lowered.startswith(prefix.lower())]
        if not matches:
            if "http://" in self.adapters:
                return self.adapters["http://"]
            if "https://" in self.adapters:
                return self.adapters["https://"]
            raise InvalidSchema(f"No adapter found for {url}")
        best = max(matches, key=len)
        return self.adapters[best]

    def mount(self, prefix: str, adapter: HTTPAdapter) -> None:
        self.adapters[prefix] = adapter

    # ------------------------------------------------------------------
    # Core sending logic
    # ------------------------------------------------------------------
    def send(
        self,
        request: PreparedRequest,
        *,
        timeout: float | tuple[float | None, float | None] | None = None,
        allow_redirects: bool = True,
        verify: bool | str = True,
        cert: str | tuple[str, str] | None = None,
        stream: bool = False,
        proxies: Mapping[str, str] | None = None,
        auth: tuple[str, str] | None = None,
    ) -> Response:
        redirects_remaining = self.max_redirects
        current_request = request.copy()
        history: list[Response] = []

        while True:
            adapter = self.get_adapter(current_request.url)
            proxy = self._get_proxy(current_request.url, proxies)
            proxy_map: dict[str, str] = {}
            if proxy:
                scheme = urllib.parse.urlsplit(current_request.url).scheme.lower()
                proxy_map[scheme] = proxy
            response, header_pairs = adapter.send(
                current_request,
                timeout=timeout,
                verify=verify,
                cert=cert,
                stream=stream,
                proxies=proxy_map,
                auth=auth,
            )

            self._extract_cookies(header_pairs, current_request, response)
            response.history = list(history)

            for hook in current_request.hooks.get("response", []):
                hook(response)
            for hook in self.hooks.get("response", []):
                hook(response)

            if not allow_redirects or response.status_code not in _REDIRECT_STATUSES:
                return response

            location = response.headers.get("location")
            if not location:
                return response

            if redirects_remaining <= 0:
                raise TooManyRedirects("Exceeded maximum redirect count")
            redirects_remaining -= 1

            redirect_url = urllib.parse.urljoin(current_request.url, location)
            if not urllib.parse.urlsplit(redirect_url).scheme:
                raise MissingSchema("Redirect location missing scheme")

            new_method = current_request.method
            new_body = None
            if response.status_code in {303} and current_request.method != "HEAD":
                new_method = "GET"
            elif response.status_code in {301, 302} and current_request.method == "POST":
                new_method = "GET"
            else:
                new_body = current_request.body

            redirected = self._prepare_request(
                new_method,
                redirect_url,
                params=None,
                data=new_body,
                json=None,
                files=None,
                headers=current_request.headers,
                cookies=None,
                hooks=current_request.hooks,
            )

            old_host = urllib.parse.urlsplit(current_request.url).netloc
            new_host = urllib.parse.urlsplit(redirect_url).netloc
            if old_host != new_host:
                redirected.headers.pop("Authorization", None)
                redirected.headers.pop("authorization", None)

            history.append(response)
            current_request = redirected

    def close(self) -> None:  # pragma: no cover - provided for API compatibility
        seen: set[int] = set()
        for adapter in list(self.adapters.values()):
            if id(adapter) in seen:
                continue
            seen.add(id(adapter))
            close = getattr(adapter, "close", None)
            if callable(close):
                close()
        self.adapters.clear()

    # ------------------------------------------------------------------
    # Preparation helpers
    # ------------------------------------------------------------------
    def _merge_hooks(self, request_hooks: Mapping[str, Iterable[Any]] | None) -> dict[str, list[Any]]:
        merged: dict[str, list[Any]] = {"response": []}
        if not request_hooks:
            return merged
        for event, handlers in request_hooks.items():
            if not handlers:
                continue
            if isinstance(handlers, Iterable) and not isinstance(handlers, (str, bytes)):
                merged.setdefault(event, []).extend(handlers)
            else:
                merged.setdefault(event, []).append(handlers)  # type: ignore[arg-type]
        return merged

    def _prepare_request(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, Any] | None,
        data: Any | None,
        json: Any | None,
        files: Mapping[str, Any] | Iterable[tuple[str, Any]] | None,
        headers: Mapping[str, str] | None,
        cookies: Mapping[str, str] | CookieJar | None,
        hooks: Mapping[str, Iterable[Any]] | None,
    ) -> PreparedRequest:
        base_url = self._merge_params(url, self.params)
        full_url = self._merge_params(base_url, params)
        parsed = urllib.parse.urlsplit(full_url)
        if not parsed.scheme:
            raise MissingSchema("Invalid URL: No schema supplied")
        if parsed.scheme not in {"http", "https"}:
            raise InvalidSchema(f"Unsupported scheme {parsed.scheme}")

        merged_headers = self.headers.copy()
        if headers:
            merged_headers.update(headers)

        body, merged_headers, body_type = self._merge_body(data, json, files, merged_headers)

        request = Request(
            method,
            full_url,
            merged_headers,
            body,
            hooks=hooks,
        )
        prepared = request.prepare()
        prepared.headers = merged_headers
        prepared._body_type = body_type

        if cookies:
            if isinstance(cookies, CookieJar):
                cookie_items = {cookie.name: cookie.value for cookie in cookies}
            else:
                cookie_items = dict(cookies)
            prepared.prepare_cookies(cookie_items)

        self._prepare_cookies(prepared)
        return prepared

    def _merge_params(
        self, url: str, params: Mapping[str, Any] | None
    ) -> str:
        if not params:
            return url
        split = urllib.parse.urlsplit(url)
        query = urllib.parse.parse_qsl(split.query, keep_blank_values=True)
        iterable: Iterable[tuple[str, Any]]
        if hasattr(params, "items"):
            iterable = params.items()  # type: ignore[assignment]
        else:
            iterable = params  # type: ignore[assignment]
        for key, value in iterable:
            if isinstance(value, (list, tuple)):
                for item in value:
                    query.append((key, str(item)))
            else:
                query.append((key, "" if value is None else str(value)))
        encoded = urllib.parse.urlencode(query)
        return urllib.parse.urlunsplit((split.scheme, split.netloc, split.path, encoded, split.fragment))

    def _merge_body(
        self,
        data: Any | None,
        json: Any | None,
        files: Mapping[str, Any] | Iterable[tuple[str, Any]] | None,
        headers: CaseInsensitiveDict,
    ) -> tuple[bytes | None, CaseInsensitiveDict, str | None]:
        headers = headers.copy()
        body_type: str | None = None

        if files:
            return self._encode_multipart(data, files, headers)

        if json is not None:
            body = jsonlib.dumps(json).encode("utf-8")
            headers.setdefault("Content-Type", "application/json")
            return body, headers, body_type

        if data is None:
            return None, headers, body_type

        if isinstance(data, (bytes, bytearray)):
            body = bytes(data)
        elif isinstance(data, str):
            body = data.encode("utf-8")
        elif hasattr(data, "read"):
            body = data.read()
        elif isinstance(data, Mapping) or isinstance(data, (list, tuple)):
            body = urllib.parse.urlencode(data, doseq=True).encode("utf-8")
            headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
        else:
            raise TypeError("Unsupported data type for request body")

        return body, headers, body_type

    def _encode_multipart(
        self,
        data: Any,
        files: Mapping[str, Any] | Iterable[tuple[str, Any]],
        headers: CaseInsensitiveDict,
    ) -> tuple[bytes, CaseInsensitiveDict, str | None]:
        boundary = f"req2-{os.urandom(8).hex()}"
        body = io.BytesIO()

        def write_field(name: str, value: str) -> None:
            body.write(f"--{boundary}\r\n".encode("ascii"))
            disposition = f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
            body.write(disposition.encode("utf-8"))
            body.write(value.encode("utf-8"))
            body.write(b"\r\n")

        if data:
            if hasattr(data, "items"):
                data_iter = data.items()
            else:
                data_iter = data
            for key, value in data_iter:
                if isinstance(value, (list, tuple)):
                    for item in value:
                        write_field(key, str(item))
                else:
                    write_field(key, "" if value is None else str(value))

        for item in self._normalize_files(files):
            body.write(f"--{boundary}\r\n".encode("ascii"))
            disposition = f'Content-Disposition: form-data; name="{item.name}"'
            if item.filename:
                disposition += f'; filename="{item.filename}"'
            body.write((disposition + "\r\n").encode("utf-8"))
            if item.content_type:
                body.write(f"Content-Type: {item.content_type}\r\n".encode("utf-8"))
            if item.headers:
                for header_name, header_value in item.headers.items():
                    body.write(f"{header_name}: {header_value}\r\n".encode("utf-8"))
            body.write(b"\r\n")
            body.write(item.body)
            body.write(b"\r\n")

        body.write(f"--{boundary}--\r\n".encode("ascii"))
        payload = body.getvalue()
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        headers["Content-Length"] = str(len(payload))
        return payload, headers, "multipart"

    def _normalize_files(
        self, files: Mapping[str, Any] | Iterable[tuple[str, Any]]
    ) -> list[_MultipartItem]:
        if hasattr(files, "items"):
            iterable = files.items()
        else:
            iterable = files  # type: ignore[assignment]

        normalized: list[_MultipartItem] = []
        for field, value in iterable:
            filename: str | None = None
            content_type: str | None = None
            extra_headers: Mapping[str, str] | None = None
            data: bytes

            if isinstance(value, (tuple, list)):
                parts = list(value)
                if not parts:
                    raise ValueError("Invalid file tuple supplied")
                filename = parts[0]
                file_obj = parts[1] if len(parts) > 1 else None
                if len(parts) > 2:
                    third = parts[2]
                    if isinstance(third, Mapping):
                        extra_headers = third
                    else:
                        content_type = third
                if len(parts) > 3 and isinstance(parts[3], Mapping):
                    extra_headers = parts[3]
                if hasattr(file_obj, "read"):
                    data = file_obj.read()
                    if hasattr(file_obj, "seek"):
                        try:
                            file_obj.seek(0)
                        except OSError:
                            pass
                elif isinstance(file_obj, (bytes, bytearray)):
                    data = bytes(file_obj)
                elif isinstance(file_obj, str):
                    with open(file_obj, "rb") as fh:
                        data = fh.read()
                    if filename is None:
                        filename = os.path.basename(file_obj)
                else:
                    raise TypeError("Unsupported file object type")
                if filename is None and hasattr(file_obj, "name"):
                    filename = os.path.basename(file_obj.name)
            else:
                file_obj = value
                if hasattr(file_obj, "read"):
                    data = file_obj.read()
                    if hasattr(file_obj, "seek"):
                        try:
                            file_obj.seek(0)
                        except OSError:
                            pass
                    filename = os.path.basename(getattr(file_obj, "name", field))
                elif isinstance(file_obj, (bytes, bytearray)):
                    data = bytes(file_obj)
                    filename = field
                elif isinstance(file_obj, str):
                    with open(file_obj, "rb") as fh:
                        data = fh.read()
                    filename = os.path.basename(file_obj)
                else:
                    raise TypeError("Unsupported file value for files parameter")

            normalized.append(
                _MultipartItem(
                    field,
                    data,
                    filename=filename,
                    content_type=content_type,
                    headers=extra_headers,
                )
            )

        return normalized

    def _prepare_cookies(self, request: PreparedRequest) -> None:
        if not self.cookies:
            return

        jar_request = _CookieRequestAdapter(request.url, request.headers)
        self.cookies.add_cookie_header(jar_request)
        for name, value in jar_request.unredirected_headers.items():
            request.headers[name] = value

    def _extract_cookies(
        self,
        header_pairs: list[tuple[str, str]],
        request: PreparedRequest,
        response: Response,
    ) -> None:
        if not header_pairs:
            response_cookies = CookieJar()
            for cookie in self.cookies:
                response_cookies.set_cookie(cookie)
            response.cookies = response_cookies
            return

        message = HTTPMessage()
        for name, value in header_pairs:
            message.add_header(name, value)

        jar_request = _CookieRequestAdapter(request.url, request.headers)
        jar_response = _CookieResponseAdapter(message, response.url)
        self.cookies.extract_cookies(jar_response, jar_request)
        response_cookies = CookieJar()
        for cookie in self.cookies:
            response_cookies.set_cookie(cookie)
        response.cookies = response_cookies

    def _get_proxy(
        self, url: str, overrides: Mapping[str, str] | None = None
    ) -> str | None:
        proxies: dict[str, str] = {}
        proxies.update(self.proxies)
        if overrides:
            proxies.update(overrides)
        if self.trust_env:
            for scheme, proxy in urllib.request.getproxies().items():
                proxies.setdefault(scheme, proxy)

        parsed = urllib.parse.urlsplit(url)
        scheme = parsed.scheme.lower()
        proxy = proxies.get(scheme)
        if not proxy:
            return None
        if urllib.request.proxy_bypass(parsed.hostname or ""):
            return None
        return proxy

    def merge_environment_settings(
        self,
        url: str,
        proxies: Mapping[str, str] | None,
        stream: bool,
        verify: bool | str,
        cert: str | tuple[str, str] | None,
    ) -> dict[str, Any]:
        del stream  # unused but kept for compatibility with Requests signature
        del url
        merged_proxies = dict(self.proxies)
        if self.trust_env:
            for scheme, proxy in urllib.request.getproxies().items():
                merged_proxies.setdefault(scheme, proxy)
        if proxies:
            merged_proxies.update(proxies)
        return {"verify": verify, "cert": cert, "proxies": merged_proxies}


class _CookieRequestAdapter:
    def __init__(self, url: str, headers: Mapping[str, str]) -> None:
        self._url = url
        self.headers = CaseInsensitiveDict(headers)
        self.unredirected_headers: dict[str, str] = {}

    def get_full_url(self) -> str:
        return self._url

    def get_host(self) -> str:
        return urllib.parse.urlsplit(self._url).netloc

    def get_origin_req_host(self) -> str:
        return self.get_host()

    def get_type(self) -> str:
        return urllib.parse.urlsplit(self._url).scheme

    def has_header(self, header: str) -> bool:
        return header in self.headers

    def get_header(self, header: str, default: str | None = None) -> str | None:
        return self.headers.get(header, default)

    def add_unredirected_header(self, name: str, value: str) -> None:
        self.unredirected_headers[name] = value

    @property
    def unverifiable(self) -> bool:
        return False

    def is_unverifiable(self) -> bool:
        return False


class _CookieResponseAdapter:
    def __init__(self, message: HTTPMessage, url: str) -> None:
        self._message = message
        self._url = url

    def info(self) -> HTTPMessage:
        return self._message

    def geturl(self) -> str:
        return self._url


def request(method: str, url: str, **kwargs: Any) -> Response:
    session = Session()
    try:
        return session.request(method, url, **kwargs)
    finally:
        session.close()
