"""The UI server edits API keys, so these are mostly security assertions."""

import http.client
import json
import threading

import pytest

from smart_search import service, ui_server
from smart_search.ui_server import UIServerConfig


@pytest.fixture
def running(tmp_path, monkeypatch):
    monkeypatch.setattr(service.config, "_config_file", tmp_path / "config.json")
    monkeypatch.setattr(service.config, "_cached_model", None)
    httpd, runtime = ui_server.build_server(UIServerConfig(port=0, idle_timeout=0, open_browser=False))
    thread = threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True)
    thread.start()
    try:
        yield httpd, runtime
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)


def request(runtime, method, path, *, token=None, headers=None, body=None, host=None):
    conn = http.client.HTTPConnection("127.0.0.1", runtime.port, timeout=5)
    sent = {"Host": host or f"127.0.0.1:{runtime.port}"}
    if token:
        sent[ui_server.TOKEN_HEADER] = token
    sent.update(headers or {})
    payload = None
    if body is not None:
        payload = body if isinstance(body, bytes) else json.dumps(body).encode()
        sent["Content-Type"] = "application/json"
    conn.request(method, path, body=payload, headers=sent)
    response = conn.getresponse()
    raw = response.read()
    conn.close()
    return response, raw


def test_binds_loopback_only(running):
    httpd, _runtime = running
    assert httpd.server_address[0] == "127.0.0.1"


def test_page_requires_the_token(running):
    _httpd, runtime = running
    response, _ = request(runtime, "GET", "/")
    assert response.status == 403
    response, _ = request(runtime, "GET", "/?token=wrong")
    assert response.status == 403


def test_page_renders_with_the_token_and_leaves_no_placeholders(running):
    _httpd, runtime = running
    response, raw = request(runtime, "GET", f"/?token={runtime.token}")
    assert response.status == 200
    body = raw.decode("utf-8")
    assert "__SS_UI_TOKEN__" not in body
    assert "__SS_UI_NONCE__" not in body
    assert "__SS_UI_LANG__" not in body
    assert runtime.nonce in body


def test_api_requires_the_token_header(running):
    _httpd, runtime = running
    response, _ = request(runtime, "GET", "/api/state")
    assert response.status == 403
    response, _ = request(runtime, "GET", "/api/state", token="nope")
    assert response.status == 403
    response, _ = request(runtime, "GET", "/api/state", token=runtime.token)
    assert response.status == 200


def test_rebound_host_is_rejected(running):
    # A DNS-rebinding page reaches the socket but cannot forge a loopback Host.
    _httpd, runtime = running
    response, _ = request(runtime, "GET", "/api/state", token=runtime.token, host="evil.com")
    assert response.status == 403


def test_cross_origin_is_rejected(running):
    _httpd, runtime = running
    response, _ = request(
        runtime, "GET", "/api/state", token=runtime.token, headers={"Origin": "http://evil.com"}
    )
    assert response.status == 403
    response, _ = request(
        runtime, "GET", "/api/state", token=runtime.token, headers={"Sec-Fetch-Site": "cross-site"}
    )
    assert response.status == 403


def test_same_origin_is_accepted(running):
    _httpd, runtime = running
    response, _ = request(
        runtime,
        "GET",
        "/api/state",
        token=runtime.token,
        headers={"Origin": f"http://127.0.0.1:{runtime.port}", "Sec-Fetch-Site": "same-origin"},
    )
    assert response.status == 200


def test_never_emits_cors_headers(running):
    _httpd, runtime = running
    for method, path in (("GET", "/api/state"), ("OPTIONS", "/api/state")):
        response, _ = request(runtime, method, path, token=runtime.token)
        assert response.getheader("Access-Control-Allow-Origin") is None
        assert response.getheader("Access-Control-Allow-Headers") is None


def test_options_is_not_allowed(running):
    _httpd, runtime = running
    response, _ = request(runtime, "OPTIONS", "/api/state", token=runtime.token)
    assert response.status == 405


def test_security_headers_are_present(running):
    _httpd, runtime = running
    response, _ = request(runtime, "GET", "/api/state", token=runtime.token)
    assert response.getheader("Cache-Control") == "no-store"
    assert response.getheader("X-Content-Type-Options") == "nosniff"
    assert response.getheader("X-Frame-Options") == "DENY"
    csp = response.getheader("Content-Security-Policy")
    assert f"'nonce-{runtime.nonce}'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "default-src 'none'" in csp


def test_oversized_body_is_refused(running):
    _httpd, runtime = running
    response, _ = request(
        runtime, "POST", "/api/heartbeat", token=runtime.token, body=b"x" * (ui_server.MAX_BODY_BYTES + 1)
    )
    assert response.status == 413


def test_chunked_body_is_refused(running):
    _httpd, runtime = running
    response, _ = request(
        runtime,
        "POST",
        "/api/heartbeat",
        token=runtime.token,
        headers={"Transfer-Encoding": "chunked"},
        body=b"{}",
    )
    assert response.status in (400, 411)


def test_unknown_path_gives_a_bare_404(running):
    _httpd, runtime = running
    response, raw = request(runtime, "GET", "/api/../../etc/passwd", token=runtime.token)
    assert response.status == 404
    body = raw.decode("utf-8")
    assert "passwd" not in body
    assert "Traceback" not in body


def test_state_never_contains_a_raw_secret(running):
    """The single most valuable regression test in this file."""
    _httpd, runtime = running
    service.config.set_config_value("EXA_API_KEY", "exa-super-secret-value-1234")
    service.config.set_config_value("OPENAI_COMPATIBLE_API_KEY", "sk-live-do-not-leak-9876")

    response, raw = request(runtime, "GET", "/api/state", token=runtime.token)
    assert response.status == 200
    body = raw.decode("utf-8")
    assert "exa-super-secret-value-1234" not in body
    assert "sk-live-do-not-leak-9876" not in body
    payload = json.loads(body)
    assert "*" in payload["values"]["EXA_API_KEY"]


def test_state_reports_environment_shadowing(running, monkeypatch):
    # A value the user cannot change from here must be labelled as such.
    _httpd, runtime = running
    monkeypatch.setenv("EXA_API_KEY", "from-the-environment")
    _response, raw = request(runtime, "GET", "/api/state", token=runtime.token)
    payload = json.loads(raw)
    assert payload["sources"]["EXA_API_KEY"] == "environment"


@pytest.mark.parametrize("path", ["/api/state", "/api/status"])
def test_state_reports_invalid_xai_reasoning_effort(running, monkeypatch, path):
    _httpd, runtime = running
    monkeypatch.setenv("XAI_REASONING_EFFORT", "ultra")

    response, raw = request(runtime, "GET", path, token=runtime.token)

    assert response.status == 200
    payload = json.loads(raw)
    assert payload["values"]["XAI_REASONING_EFFORT"] == "ultra"
    assert any("XAI_REASONING_EFFORT" in error for error in payload["resolved"]["config_parameter_errors"])


def test_state_makes_no_network_calls(running, monkeypatch):
    _httpd, runtime = running

    def explode(*args, **kwargs):
        raise AssertionError("/api/state must not touch the network")

    monkeypatch.setattr("httpx.AsyncClient", explode)
    response, _ = request(runtime, "GET", "/api/state", token=runtime.token)
    assert response.status == 200


def test_state_carries_the_full_field_metadata(running, monkeypatch):
    # conftest pins the profile to "off" for isolation; the page must show the real one.
    monkeypatch.setenv("SMART_SEARCH_MINIMUM_PROFILE", "standard")
    _httpd, runtime = running
    _response, raw = request(runtime, "GET", "/api/state", token=runtime.token)
    payload = json.loads(raw)
    assert len(payload["metadata"]["fields"]) == len(service.config._CONFIG_KEYS - service.config.RETIRED_ROUTER_KEYS)
    assert payload["minimum_profile"]["required"] == ["retrieval"]
    assert set(payload["capability_status"]) >= {"main_search", "docs_search", "web_fetch"}
    assert payload["probe_kinds"]["exa"] == "live"


def test_shutdown_stops_the_server(running):
    httpd, runtime = running
    response, _ = request(runtime, "POST", "/api/shutdown", token=runtime.token, body={})
    assert response.status == 200
    assert runtime.stopping.is_set()
    httpd.shutdown()


def test_asset_resolves_through_importlib(running):
    # Catches a missing package-data glob or npm `files` entry.
    assert "<html" in ui_server.load_page_source()


def test_cli_parses_the_ui_command():
    from smart_search.cli import build_parser

    args = build_parser().parse_args(["ui", "--no-browser", "--port", "0"])
    assert args.command == "ui"
    assert args.no_browser is True
    assert build_parser().parse_args(["web", "--check"]).command == "ui"


def test_cli_check_reports_the_bundled_asset(capsys):
    from smart_search.cli import main

    assert main(["ui", "--check", "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["asset_bytes"] > 1000


def test_browser_is_not_opened_over_ssh(monkeypatch):
    monkeypatch.setenv("SSH_CONNECTION", "10.0.0.1 22 10.0.0.2 2222")
    options = ui_server.UIServerConfig(open_browser=True)
    assert ui_server._should_open_browser(options) is False


def test_browser_is_not_opened_on_a_headless_linux_box(monkeypatch):
    # webbrowser would otherwise launch a terminal browser and hijack the TTY.
    monkeypatch.setattr("sys.platform", "linux")
    for name in ("SSH_CONNECTION", "SSH_TTY", "DISPLAY", "WAYLAND_DISPLAY", "WSL_DISTRO_NAME", "WSL_INTEROP"):
        monkeypatch.delenv(name, raising=False)
    assert ui_server._should_open_browser(ui_server.UIServerConfig(open_browser=True)) is False
    monkeypatch.setenv("DISPLAY", ":0")
    assert ui_server._should_open_browser(ui_server.UIServerConfig(open_browser=True)) is True


@pytest.fixture
def wsl(monkeypatch):
    monkeypatch.setattr("sys.platform", "linux")
    monkeypatch.setenv("WSL_DISTRO_NAME", "Ubuntu")
    monkeypatch.delenv("BROWSER", raising=False)
    launched = []
    monkeypatch.setattr(ui_server.subprocess, "Popen", lambda args, **kwargs: launched.append(args))
    monkeypatch.setattr(ui_server.webbrowser, "open", lambda url: launched.append(["webbrowser", url]) or True)
    return launched


def test_wsl_opens_the_windows_browser_instead_of_a_terminal_one(wsl, monkeypatch, tmp_path):
    explorer = tmp_path / "explorer.exe"
    explorer.write_text("")
    monkeypatch.setattr(ui_server.shutil, "which", lambda name: str(explorer) if name == "explorer.exe" else None)
    assert ui_server._open_browser("http://127.0.0.1:1/?token=t") is True
    assert wsl == [[str(explorer), "http://127.0.0.1:1/?token=t"]]


def test_wsl_respects_an_explicit_browser(wsl, monkeypatch):
    monkeypatch.setenv("BROWSER", "wslview")
    assert ui_server._open_browser("http://127.0.0.1:1/") is True
    assert wsl == [["webbrowser", "http://127.0.0.1:1/"]]


def test_wsl_without_an_opener_points_at_the_windows_browser(wsl, monkeypatch):
    monkeypatch.setattr(ui_server.shutil, "which", lambda name: None)
    monkeypatch.setattr(ui_server.os.path, "isfile", lambda path: False)
    assert ui_server._open_browser("http://127.0.0.1:1/") is False
    assert wsl == []
    runtime = ui_server.UIRuntime(port=1, idle_timeout=0)
    notes = "\n".join(ui_server._startup_notes(runtime, False, "en"))
    assert "Windows browser" in notes and "mirrored" in notes and "ssh -L" not in notes


# ---- write path over HTTP ----------------------------------------------
def test_write_endpoints_require_the_token(running):
    _httpd, runtime = running
    for path in ("/api/config", "/api/preview", "/api/skills/install"):
        response, _ = request(runtime, "POST", path, body={})
        assert response.status == 403, f"{path} accepted an unauthenticated write"


def test_write_endpoints_reject_a_rebound_host(running):
    _httpd, runtime = running
    response, _ = request(
        runtime, "POST", "/api/config", token=runtime.token, host="evil.com",
        body={"set": {"EXA_API_KEY": "stolen"}},
    )
    assert response.status == 403
    assert "EXA_API_KEY" not in service.config.get_saved_config(masked=True)


def test_config_round_trips_over_http(running):
    _httpd, runtime = running
    response, raw = request(
        runtime, "POST", "/api/config", token=runtime.token,
        body={"set": {"EXA_API_KEY": "exa-round-trip-secret", "CONTEXT7_API_KEY": "c7"}},
    )
    assert response.status == 200
    payload = json.loads(raw)
    assert payload["ok"] is True
    # The response echoes what was saved, so it must be masked like any read.
    assert "exa-round-trip-secret" not in raw.decode("utf-8")
    assert payload["status"]["capability_status"]["docs_search"]["ok"] is True


def test_preview_over_http_does_not_persist(running):
    _httpd, runtime = running
    response, raw = request(
        runtime, "POST", "/api/preview", token=runtime.token,
        body={"values": {"XAI_API_KEY": "x", "EXA_API_KEY": "y", "TAVILY_API_KEY": "z"}},
    )
    assert response.status == 200
    assert json.loads(raw)["ok"] is True
    assert not service.config.config_file.exists()


def test_malformed_json_body_is_rejected(running):
    _httpd, runtime = running
    response, _ = request(runtime, "POST", "/api/config", token=runtime.token, body=b"{not json")
    assert response.status == 400


def test_run_endpoint_requires_the_token(running):
    _httpd, runtime = running
    response, _ = request(runtime, "POST", "/api/run", body={"query": "x"})
    assert response.status == 403


def test_run_endpoint_executes_route(running, monkeypatch):
    _httpd, runtime = running
    response, raw = request(
        runtime, "POST", "/api/run", token=runtime.token,
        body={"command": "route", "query": "React useEffect cleanup function docs"},
    )
    assert response.status == 200
    payload = json.loads(raw)
    # route is offline, so it succeeds even with nothing configured.
    assert payload["ok"] is True
    assert payload["required_capabilities"]


def test_every_route_is_reachable_and_token_gated(running):
    """No endpoint may be added without the token check applying to it."""
    _httpd, runtime = running
    for (method, path) in ui_server.ROUTES:
        response, _ = request(runtime, method, path, body={} if method == "POST" else None)
        assert response.status == 403, f"{method} {path} is not token-gated"


def test_a_stalled_body_does_not_pin_a_thread_forever(running, monkeypatch):
    """A client that promises a body and never sends it must not hold a handler."""
    _httpd, runtime = running
    import socket as _socket

    conn = _socket.create_connection(("127.0.0.1", runtime.port), timeout=5)
    try:
        conn.sendall(
            f"POST /api/heartbeat HTTP/1.1\r\n"
            f"Host: 127.0.0.1:{runtime.port}\r\n"
            f"{ui_server.TOKEN_HEADER}: {runtime.token}\r\n"
            f"Content-Type: application/json\r\n"
            f"Content-Length: 500\r\n\r\n".encode()
        )
        # Send nothing more. The handler's socket timeout must end this.
        assert ui_server.SmartSearchUIHandler.timeout > 0
    finally:
        conn.close()

    # The server must still answer a normal request afterwards.
    response, _ = request(runtime, "GET", "/api/state", token=runtime.token)
    assert response.status == 200


def test_heartbeat_reports_the_remaining_idle_budget(tmp_path, monkeypatch):
    monkeypatch.setattr(service.config, "_config_file", tmp_path / "config.json")
    httpd, runtime = ui_server.build_server(
        UIServerConfig(port=0, idle_timeout=600, open_browser=False)
    )
    thread = threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True)
    thread.start()
    try:
        _response, raw = request(runtime, "POST", "/api/heartbeat", token=runtime.token, body={})
        payload = json.loads(raw)
        assert payload["idle_timeout"] == 600
        assert 0 < payload["idle_deadline_seconds"] <= 600
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)


def test_a_truncated_body_is_rejected(running):
    _httpd, runtime = running
    import socket as _socket

    conn = _socket.create_connection(("127.0.0.1", runtime.port), timeout=10)
    try:
        conn.sendall(
            f"POST /api/heartbeat HTTP/1.1\r\n"
            f"Host: 127.0.0.1:{runtime.port}\r\n"
            f"{ui_server.TOKEN_HEADER}: {runtime.token}\r\n"
            f"Content-Length: 100\r\n\r\n".encode() + b'{"a":1}'
        )
        conn.shutdown(_socket.SHUT_WR)
        raw = conn.recv(4096).decode("utf-8", "replace")
        assert " 400 " in raw.split("\r\n")[0], raw.split("\r\n")[0]
    finally:
        conn.close()
