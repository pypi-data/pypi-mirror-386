"""Adapter implementations for :mod:`req2` sessions."""

from __future__ import annotations

import io
from tempfile import SpooledTemporaryFile
from typing import Any

import pycurl

from .exceptions import map_pycurl_error
from .models import PreparedRequest, Response
from .utils import CaseInsensitiveDict


class _CurlHandlePool:
    """Maintain a small pool of reusable :class:`pycurl.Curl` handles."""

    def __init__(self, maxsize: int = 10) -> None:
        self._available: list[pycurl.Curl] = []
        self._maxsize = maxsize

    def acquire(self) -> pycurl.Curl:
        if self._available:
            curl = self._available.pop()
        else:
            curl = pycurl.Curl()
        curl.setopt(pycurl.NOSIGNAL, 1)
        return curl

    def release(self, curl: pycurl.Curl, *, reusable: bool = True) -> None:
        if not reusable:
            curl.close()
            return

        try:
            curl.reset()
        except AttributeError:
            # Older versions of pycurl may not provide ``reset``; fall back to
            # closing the handle in those rare cases.
            curl.close()
            return

        curl.setopt(pycurl.NOSIGNAL, 1)
        if len(self._available) >= self._maxsize:
            curl.close()
        else:
            self._available.append(curl)

    def close(self) -> None:
        while self._available:
            curl = self._available.pop()
            curl.close()


class HTTPAdapter:
    """Basic HTTP adapter that drives requests through :mod:`pycurl`."""

    def __init__(
        self,
        *,
        pool_connections: int = 10,
        pool_maxsize: int | None = None,
        spool_max_size: int = 1024 * 1024,
    ) -> None:
        maxsize = pool_maxsize if pool_maxsize is not None else pool_connections
        self._pool = _CurlHandlePool(maxsize=maxsize)
        self._spool_max_size = spool_max_size

    # ------------------------------------------------------------------
    # Public API expected by :class:`req2.sessions.Session`
    # ------------------------------------------------------------------
    def send(
        self,
        request: PreparedRequest,
        *,
        timeout: float | tuple[float | None, float | None] | None = None,
        verify: bool | str = True,
        cert: str | tuple[str, str] | None = None,
        stream: bool = False,
        proxies: dict[str, str] | None = None,
        auth: tuple[str, str] | None = None,
    ) -> tuple[Response, list[tuple[str, str]]]:
        curl = self._pool.acquire()
        header_blocks: list[list[str]] = []
        current_block: list[str] = []

        if stream:
            body_buffer: io.BufferedRandom = SpooledTemporaryFile(
                max_size=self._spool_max_size, mode="w+b"
            )
        else:
            body_buffer = io.BytesIO()

        def header_function(line: bytes) -> None:
            text = line.decode("iso-8859-1")
            if text.startswith("HTTP/"):
                if current_block:
                    header_blocks.append(current_block.copy())
                    current_block.clear()
                current_block.append(text.strip())
            elif text in ("\r\n", "\n"):
                if current_block:
                    header_blocks.append(current_block.copy())
                    current_block.clear()
            else:
                current_block.append(text.strip())

        try:
            self._configure_handle(
                curl,
                request,
                body_buffer,
                header_function,
                timeout=timeout,
                verify=verify,
                cert=cert,
                proxies=proxies,
                auth=auth,
            )

            curl.perform()
            if current_block:
                header_blocks.append(current_block.copy())

            response_code = curl.getinfo(pycurl.RESPONSE_CODE)
            effective_url = curl.getinfo(pycurl.EFFECTIVE_URL)
            timings = {
                "dns": curl.getinfo(pycurl.NAMELOOKUP_TIME),
                "tcp_connect": curl.getinfo(pycurl.CONNECT_TIME),
                "ssl_handshake": curl.getinfo(pycurl.APPCONNECT_TIME),
                "pretransfer": curl.getinfo(pycurl.PRETRANSFER_TIME),
                "ttfb": curl.getinfo(pycurl.STARTTRANSFER_TIME),
                "total": curl.getinfo(pycurl.TOTAL_TIME),
            }
        except pycurl.error as exc:
            self._pool.release(curl, reusable=False)
            body_buffer.close()
            _, code = exc.args
            raise map_pycurl_error(code)
        else:
            self._pool.release(curl, reusable=True)

        body_buffer.seek(0)
        header_map, header_pairs, reason = self._parse_headers(header_blocks)

        ttfb = timings["ttfb"]
        total = timings["total"]
        timings["content_transfer"] = max(total - ttfb, 0.0)

        if stream:
            raw_body = body_buffer
            content_bytes: bytes | None = None
        else:
            content_bytes = body_buffer.read()
            raw_body = io.BytesIO(content_bytes)
            body_buffer.close()
            raw_body.seek(0)

        response = Response(
            status_code=response_code,
            headers=header_map,
            raw=raw_body,
            content=content_bytes,
            url=effective_url,
            reason=reason,
            elapsed_seconds=total,
            timings=timings,
            request=request,
            stream_consumed=not stream,
        )

        return response, header_pairs

    def close(self) -> None:
        self._pool.close()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _configure_handle(
        self,
        curl: pycurl.Curl,
        request: PreparedRequest,
        body_buffer: io.BufferedIOBase,
        header_function: Any,
        *,
        timeout: float | tuple[float | None, float | None] | None,
        verify: bool | str,
        cert: str | tuple[str, str] | None,
        proxies: dict[str, str] | None,
        auth: tuple[str, str] | None,
    ) -> None:
        curl.setopt(pycurl.URL, request.url)
        curl.setopt(pycurl.NOPROGRESS, True)
        curl.setopt(pycurl.WRITEDATA, body_buffer)
        curl.setopt(pycurl.HEADERFUNCTION, header_function)
        curl.setopt(pycurl.ACCEPT_ENCODING, "")

        self._apply_method(curl, request)

        if request.headers:
            header_list = [f"{k}: {v}" for k, v in request.headers.items()]
            curl.setopt(pycurl.HTTPHEADER, header_list)

        if timeout is not None:
            if isinstance(timeout, tuple):
                connect, read = timeout
                if connect is not None:
                    curl.setopt(pycurl.CONNECTTIMEOUT, float(connect))
                if read is not None:
                    curl.setopt(pycurl.TIMEOUT, float(read))
            else:
                curl.setopt(pycurl.TIMEOUT, float(timeout))

        if isinstance(verify, str):
            curl.setopt(pycurl.CAINFO, verify)
        elif not verify:
            curl.setopt(pycurl.SSL_VERIFYPEER, 0)
            curl.setopt(pycurl.SSL_VERIFYHOST, 0)

        if cert:
            if isinstance(cert, tuple):
                cert_file, key_file = cert
                curl.setopt(pycurl.SSLCERT, cert_file)
                curl.setopt(pycurl.SSLKEY, key_file)
            else:
                curl.setopt(pycurl.SSLCERT, cert)

        if auth and len(auth) == 2:
            user, password = auth
            curl.setopt(pycurl.HTTPAUTH, pycurl.HTTPAUTH_BASIC | pycurl.HTTPAUTH_DIGEST)
            curl.setopt(pycurl.USERPWD, f"{user}:{password}")

        if proxies:
            scheme = request.url.split(":", 1)[0].lower()
            proxy = proxies.get(scheme)
            if proxy:
                curl.setopt(pycurl.PROXY, proxy)

    def _apply_method(self, curl: pycurl.Curl, request: PreparedRequest) -> None:
        method = request.method.upper()
        if method == "GET":
            curl.setopt(pycurl.HTTPGET, True)
        elif method == "POST":
            curl.setopt(pycurl.POST, True)
            if request.body is not None:
                curl.setopt(pycurl.POSTFIELDS, request.body)
        elif method == "HEAD":
            curl.setopt(pycurl.NOBODY, True)
            curl.setopt(pycurl.CUSTOMREQUEST, "HEAD")
        elif method in {"PUT", "PATCH", "DELETE"}:
            curl.setopt(pycurl.CUSTOMREQUEST, method)
            if request.body is not None:
                curl.setopt(pycurl.POSTFIELDS, request.body)
        else:
            curl.setopt(pycurl.CUSTOMREQUEST, method)
            if request.body is not None:
                curl.setopt(pycurl.POSTFIELDS, request.body)

    def _parse_headers(
        self, header_blocks: list[list[str]]
    ) -> tuple[CaseInsensitiveDict, list[tuple[str, str]], str]:
        headers = CaseInsensitiveDict()
        header_pairs: list[tuple[str, str]] = []
        reason = ""
        for block in header_blocks:
            if not block:
                continue
            status_line = block[0]
            if status_line.startswith("HTTP/"):
                parts = status_line.split(" ", 2)
                if len(parts) >= 3:
                    reason = parts[2].strip()
                elif len(parts) == 2:
                    reason = parts[1].strip()
                else:
                    reason = ""
            for header in block[1:]:
                if ":" not in header:
                    continue
                name, value = header.split(":", 1)
                name = name.strip()
                value = value.strip()
                headers[name] = value
                header_pairs.append((name, value))
        return headers, header_pairs, reason


AdapterType = HTTPAdapter

