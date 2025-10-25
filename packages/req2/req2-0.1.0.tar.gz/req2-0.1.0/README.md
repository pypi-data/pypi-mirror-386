# req2

A proof-of-concept drop-in style replacement for the popular [`requests`](https://docs.python-requests.org) HTTP client that
uses [`pycurl`](http://pycurl.io) as the transport layer. The library aims to mimic the surface level API of Requests while
providing additional timing data sourced from libcurl metrics.

## Features

* Familiar top-level helpers like `get`, `post`, and `request`.
* A `Session` object with persistent cookies, basic authentication helpers, and redirect handling.
* Response helpers for accessing JSON bodies, streaming content, cookies, and raising for HTTP errors.
* A new `Response.timings` mapping exposing DNS lookup, connection, TLS handshake, TTFB, content transfer, and total times.

## Example

```python
import req2 as requests

response = requests.get("https://httpbin.org/get")
print("Status:", response.status_code)
print("Total time:", response.timings["total"])
print("Body:", response.text[:60])
```

This project is in an early stage and currently focuses on providing the timing API while covering the most commonly used
request options including query parameters, JSON payloads, cookies, redirects, and basic authentication.
