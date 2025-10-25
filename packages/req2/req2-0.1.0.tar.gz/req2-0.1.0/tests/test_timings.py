from __future__ import annotations

import pytest

pytest.importorskip("pycurl", reason="pycurl is required for req2 tests")

import req2 as requests


@pytest.mark.parametrize("method", ["get", "request"])
def test_response_timings_exposed(http_server, method):
    url = f"http://127.0.0.1:{http_server.server_port}/delayed"
    if method == "get":
        response = requests.get(url)
    else:
        response = requests.request("GET", url)

    assert response.status_code == 200
    assert response.text == "hello world"

    required_keys = {
        "dns",
        "tcp_connect",
        "ssl_handshake",
        "pretransfer",
        "ttfb",
        "content_transfer",
        "total",
    }
    assert required_keys.issubset(response.timings.keys())

    assert response.timings["total"] >= response.timings["ttfb"]
    assert response.timings["content_transfer"] == pytest.approx(
        response.timings["total"] - response.timings["ttfb"], rel=1e-2, abs=1e-3
    )
    assert response.elapsed.total_seconds() == pytest.approx(response.timings["total"], rel=1e-2, abs=1e-3)


def test_session_request_timings(http_server):
    session = requests.Session()
    url = f"http://127.0.0.1:{http_server.server_port}/delayed"
    response = session.get(url)

    assert response.status_code == 200
    assert response.timings["total"] >= 0
    assert response.elapsed.total_seconds() == pytest.approx(response.timings["total"], rel=1e-2, abs=1e-3)


def test_redirect_history(http_server):
    base = f"http://127.0.0.1:{http_server.server_port}"
    response = requests.get(f"{base}/redirect")

    assert response.status_code == 200
    assert response.text == "final"
    assert response.history
    assert response.history[0].status_code == 302
    assert response.url.endswith("/final")


def test_session_cookies_persist(http_server):
    base = f"http://127.0.0.1:{http_server.server_port}"
    session = requests.Session()
    first = session.get(f"{base}/set-cookie")
    assert any(cookie.name == "flavor" for cookie in session.cookies)
    second = session.get(f"{base}/cookie-check")
    assert second.status_code == 200
    data = second.json()
    assert data["cookie"] == "flavor=chocolate"
    assert first.cookies


def test_basic_auth(http_server):
    base = f"http://127.0.0.1:{http_server.server_port}"
    session = requests.Session()
    session.auth = ("user", "pass")

    response = session.get(f"{base}/auth")
    assert response.status_code == 200
    assert response.text == "ok"


def test_json_post(http_server):
    base = f"http://127.0.0.1:{http_server.server_port}"
    payload = {"hello": "world"}
    response = requests.post(f"{base}/echo-json", json=payload)
    assert response.status_code == 200
    assert response.json() == payload


def test_iter_content_and_lines(http_server):
    base = f"http://127.0.0.1:{http_server.server_port}"
    response = requests.get(f"{base}/final")

    collected = b"".join(response.iter_content(chunk_size=2))
    assert collected == b"final"
    assert list(response.iter_lines()) == ["final"]


def test_query_params_round_trip(http_server):
    base = f"http://127.0.0.1:{http_server.server_port}"
    response = requests.get(f"{base}/query", params={"a": "1", "b": ["2", "3"]})
    assert response.status_code == 200
    payload = response.json()
    assert payload["a"] == ["1"]
    assert payload["b"] == ["2", "3"]
