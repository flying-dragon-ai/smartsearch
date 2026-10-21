import sys
from pathlib import Path

import pytest
import httpx

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


@pytest.fixture(autouse=True)
def isolate_smart_search_config(monkeypatch, tmp_path):
    from smart_search.config import Config
    from smart_search import skill_maintenance
    from smart_search import service

    service.reset_runtime_breakers()

    monkeypatch.setattr(skill_maintenance, "state_directory", lambda home=None: (Path(home) if home else tmp_path) / ".local/share/smart-search-tools/skills")

    config = Config()
    monkeypatch.setattr(config, "_config_file", tmp_path / "config.json")
    monkeypatch.setattr(config, "_config_dir_source", "override")
    monkeypatch.setattr(config, "_cached_model", None)
    for key in config._CONFIG_KEYS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.delenv("SMART_SEARCH_CONFIG_DIR", raising=False)
    monkeypatch.setenv("SMART_SEARCH_MINIMUM_PROFILE", "off")


@pytest.fixture(autouse=True)
def reject_unmocked_provider_requests(monkeypatch):
    original = httpx.AsyncClient.send
    blocked = []

    async def send(client, request, **kwargs):
        if request.url.host not in {"127.0.0.1", "localhost", "::1"} and not isinstance(client._transport_for_url(request.url), httpx.MockTransport):
            blocked.append(request.url.host)
            raise AssertionError("Unmocked external HTTP: " + request.url.host)
        return await original(client, request, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "send", send)
    yield
    assert not blocked, f"Tests must mock provider requests: {sorted(set(blocked))}"
