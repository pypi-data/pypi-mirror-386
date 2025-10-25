"""Subset of the Requests exception hierarchy."""


class RequestException(Exception):
    """Base exception for all request errors."""


class Timeout(RequestException):
    """The request timed out."""


class HTTPError(RequestException):
    """The HTTP response indicated an error."""


class ConnectionError(RequestException):
    """The connection to the server failed."""


class ProxyError(ConnectionError):
    """Failure occurred when connecting to a proxy."""


class SSLError(RequestException):
    """SSL negotiation failed."""


class TooManyRedirects(RequestException):
    """Exceeded the configured number of redirects."""


class InvalidURL(RequestException):
    """The provided URL was invalid."""


class MissingSchema(InvalidURL):
    """A URL schema was not supplied."""


class InvalidSchema(InvalidURL):
    """The URL schema supplied is invalid or unsupported."""


class ChunkedEncodingError(RequestException):
    """Invalid chunked transfer encoding detected."""


_PYCURL_TIMEOUT_ERRORS = {28}
_PYCURL_SSL_ERRORS = {35, 51, 58, 60, 64}
_PYCURL_PROXY_ERRORS = {5, 7, 56}


def map_pycurl_error(code: int) -> RequestException:
    if code in _PYCURL_TIMEOUT_ERRORS:
        return Timeout(f"pycurl error {code}: operation timed out")
    if code in _PYCURL_SSL_ERRORS:
        return SSLError(f"pycurl error {code}: SSL failure")
    if code in _PYCURL_PROXY_ERRORS:
        return ProxyError(f"pycurl proxy error {code}")
    return ConnectionError(f"pycurl error {code}")
