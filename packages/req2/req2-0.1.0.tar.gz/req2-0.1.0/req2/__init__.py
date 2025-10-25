"""Top level API surface compatible with :mod:`requests`."""

from __future__ import annotations

from http import HTTPStatus
from typing import Any

from .adapters import HTTPAdapter
from .exceptions import ConnectionError, HTTPError, RequestException, SSLError, Timeout, TooManyRedirects
from .models import PreparedRequest, Request, Response
from .sessions import Session, request

__all__ = [
    "Session",
    "request",
    "Response",
    "Request",
    "PreparedRequest",
    "RequestException",
    "HTTPError",
    "ConnectionError",
    "Timeout",
    "TooManyRedirects",
    "SSLError",
    "HTTPAdapter",
    "get",
    "options",
    "head",
    "post",
    "put",
    "patch",
    "delete",
    "session",
    "codes",
]


class _Codes(dict):
    """Lookup for common HTTP status codes emulating :data:`requests.codes`."""

    def __init__(self) -> None:
        super().__init__()
        for status in HTTPStatus:
            self[status.name.lower()] = status.value
            normalized = status.phrase.lower().replace(" ", "_")
            self.setdefault(normalized, status.value)

    def __getattr__(self, item: str) -> int:
        try:
            return self[item]
        except KeyError as exc:  # pragma: no cover - attribute access mirrors dict behaviour
            raise AttributeError(item) from exc

    def __setattr__(self, key: str, value: Any) -> None:  # pragma: no cover - maintain dict semantics
        self[key] = value


codes = _Codes()
codes.update({
    "ok": HTTPStatus.OK.value,
    "created": HTTPStatus.CREATED.value,
    "accepted": HTTPStatus.ACCEPTED.value,
})


def get(url: str, **kwargs: Any) -> Response:
    return request("GET", url, **kwargs)


def options(url: str, **kwargs: Any) -> Response:
    return request("OPTIONS", url, **kwargs)


def head(url: str, **kwargs: Any) -> Response:
    kwargs.setdefault("allow_redirects", False)
    return request("HEAD", url, **kwargs)


def post(url: str, **kwargs: Any) -> Response:
    return request("POST", url, **kwargs)


def put(url: str, **kwargs: Any) -> Response:
    return request("PUT", url, **kwargs)


def patch(url: str, **kwargs: Any) -> Response:
    return request("PATCH", url, **kwargs)


def delete(url: str, **kwargs: Any) -> Response:
    return request("DELETE", url, **kwargs)


def session() -> Session:
    return Session()
