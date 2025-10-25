"""Request and response models providing Requests compatibility."""

from __future__ import annotations

import io
import json
from collections.abc import Callable, Iterable, Iterator, Mapping
from datetime import timedelta
from types import MappingProxyType
from typing import Any, TYPE_CHECKING

from http.cookiejar import CookieJar

from .utils import CaseInsensitiveDict

if TYPE_CHECKING:  # pragma: no cover - import cycle safe
    from .sessions import ResponseHooks


Hook = Callable[["Response"], Any]


def _ensure_hook_structure(hooks: Mapping[str, Iterable[Hook]] | None) -> dict[str, list[Hook]]:
    """Normalize hook input to a mutable mapping of event -> list of callables."""

    normalized: dict[str, list[Hook]] = {"response": []}
    if not hooks:
        return normalized
    for event, handlers in hooks.items():
        if not handlers:
            continue
        if isinstance(handlers, Iterable) and not isinstance(handlers, (bytes, str)):
            normalized.setdefault(event, []).extend(handlers)
        else:
            normalized.setdefault(event, []).append(handlers)  # type: ignore[arg-type]
    normalized.setdefault("response", [])
    return normalized


class Response:
    """Response container closely mirroring :class:`requests.Response`."""

    def __init__(
        self,
        *,
        status_code: int,
        headers: Mapping[str, str],
        raw: io.BufferedIOBase,
        content: bytes | None,
        url: str,
        reason: str | None,
        elapsed_seconds: float,
        timings: Mapping[str, float],
        request: "PreparedRequest",
        cookies: CookieJar | None = None,
        history: Iterable["Response"] | None = None,
        stream_consumed: bool = False,
    ) -> None:
        self.status_code = status_code
        self.headers = CaseInsensitiveDict(headers)
        self.url = url
        self.reason = reason or ""
        self.elapsed = timedelta(seconds=elapsed_seconds)
        self._timings = MappingProxyType(dict(timings))
        self.request = request
        self.history = list(history or [])
        self.cookies = cookies if cookies is not None else CookieJar()
        self.encoding: str | None = self._determine_encoding()
        if not hasattr(raw, "seek"):
            raw = io.BytesIO(raw.read())  # type: ignore[assignment]
        self._raw = raw
        try:
            self._raw.seek(0)
        except (OSError, io.UnsupportedOperation):  # pragma: no cover - defensive
            pass
        self._content: bytes | None = content
        self._content_consumed = stream_consumed

    # ------------------------------------------------------------------
    # Introspection helpers
    # ------------------------------------------------------------------
    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 400

    @property
    def is_redirect(self) -> bool:
        return "location" in self.headers and self.status_code in {301, 302, 303, 307, 308}

    @property
    def is_permanent_redirect(self) -> bool:
        return "location" in self.headers and self.status_code in {301, 308}

    @property
    def is_redirectable(self) -> bool:
        return self.is_redirect

    @property
    def timings(self) -> Mapping[str, float]:
        return self._timings

    # ------------------------------------------------------------------
    # Content helpers
    # ------------------------------------------------------------------
    @property
    def content(self) -> bytes:
        if self._content is None:
            self._raw.seek(0)
            self._content = self._raw.read()
            self._content_consumed = True
        return self._content

    @property
    def text(self) -> str:
        encoding = self.encoding or "utf-8"
        return self.content.decode(encoding, errors="replace")

    @property
    def raw(self) -> io.BufferedIOBase:
        self._raw.seek(0)
        return self._raw

    def iter_content(self, chunk_size: int = 1024, decode_unicode: bool = False) -> Iterator[Any]:
        if chunk_size is not None and chunk_size <= 0:
            raise ValueError("chunk_size must be positive or None")
        self._raw.seek(0)
        while True:
            chunk = self._raw.read(chunk_size or -1)
            if not chunk:
                break
            if decode_unicode:
                yield chunk.decode(self.encoding or "utf-8", errors="replace")
            else:
                yield chunk

    def iter_lines(
        self,
        chunk_size: int = 512,
        decode_unicode: bool | None = None,
        delimiter: bytes | None = None,
    ) -> Iterator[Any]:
        pending = b""
        for chunk in self.iter_content(chunk_size=chunk_size, decode_unicode=False):
            pending += chunk
            if delimiter:
                while True:
                    try:
                        line, pending = pending.split(delimiter, 1)
                    except ValueError:
                        break
                    yield _decode_line(line, decode_unicode, self.encoding)
            else:
                while b"\n" in pending:
                    line, pending = pending.split(b"\n", 1)
                    yield _decode_line(line, decode_unicode, self.encoding)
        if pending:
            yield _decode_line(pending, decode_unicode, self.encoding)

    def json(self, **kwargs: Any) -> Any:
        text = self.text
        return json.loads(text, **kwargs)

    def raise_for_status(self) -> None:
        if 400 <= self.status_code:
            http_error_msg = f"{self.status_code} {self.reason or ''}".strip()
            http_error = HTTPError(f"{http_error_msg} for url: {self.url}")
            http_error.response = self  # type: ignore[attr-defined]
            raise http_error

    def close(self) -> None:
        self._raw.close()

    # Context manager API -------------------------------------------------
    def __enter__(self) -> "Response":  # pragma: no cover - trivial context manager
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def __bool__(self) -> bool:
        return self.ok

    def __repr__(self) -> str:  # pragma: no cover - representational helper
        return f"<Response [{self.status_code}]>"

    # Internal helpers ----------------------------------------------------
    def _determine_encoding(self) -> str | None:
        content_type = self.headers.get("content-type")
        if not content_type:
            return None
        if "charset=" in content_type:
            charset = content_type.split("charset=")[-1]
            return charset.split(";")[0].strip()
        return None


def _decode_line(line: bytes, decode_unicode: bool | None, encoding: str | None) -> Any:
    if decode_unicode is None:
        decode_unicode = True
    if decode_unicode:
        return line.decode(encoding or "utf-8", errors="replace")
    return line


class Request:
    """High-level request container mirroring :class:`requests.Request`."""

    def __init__(
        self,
        method: str,
        url: str,
        headers: Mapping[str, str] | None = None,
        data: Any = None,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
        files: Any = None,
        hooks: Mapping[str, Iterable[Hook]] | None = None,
    ) -> None:
        self.method = method.upper()
        self.url = url
        self.headers = CaseInsensitiveDict(headers or {})
        self.data = data
        self.params = params
        self.json = json
        self.files = files
        self.hooks = _ensure_hook_structure(hooks)

    def prepare(self) -> "PreparedRequest":
        return PreparedRequest(
            self.method,
            self.url,
            self.headers.copy(),
            self.data,
            params=self.params,
            json=self.json,
            files=self.files,
            hooks=self.hooks,
        )


class PreparedRequest:
    """Prepared request ready for sending."""

    def __init__(
        self,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: Any,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
        files: Any = None,
        hooks: Mapping[str, Iterable[Hook]] | None = None,
    ) -> None:
        self.method = method.upper()
        self.url = url
        self.headers = CaseInsensitiveDict(headers)
        self.body = body
        self.params = params
        self.json = json
        self.files = files
        self.hooks = _ensure_hook_structure(hooks)
        self._body_type: str | None = None
        self._multipart: Any = None

    def copy(self) -> "PreparedRequest":
        new = PreparedRequest(
            self.method,
            self.url,
            self.headers.copy(),
            self.body,
            params=self.params,
            json=self.json,
            files=self.files,
            hooks=self.hooks,
        )
        new._body_type = self._body_type
        new._multipart = self._multipart
        return new

    def prepare_cookies(self, cookies: Mapping[str, str]) -> None:
        if not cookies:
            return
        cookie_pairs = [f"{name}={value}" for name, value in cookies.items()]
        if cookie_pairs:
            existing = self.headers.get("Cookie")
            if existing:
                cookie_pairs.insert(0, existing)
            self.headers["Cookie"] = "; ".join(cookie_pairs)

    def register_hook(self, event: str, hook: Hook) -> None:
        self.hooks.setdefault(event, []).append(hook)

