import json

import pytest

from smart_search import private_search
from smart_search.config import config


@pytest.fixture
def isolated(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "_config_file", tmp_path / "config.json")
    monkeypatch.setattr(config, "_cached_model", None)
    for key, value in {
        "XHS_API_URL": "",
        "XHS_API_KEY": "",
        "XHS_MODE": "live",
        "WECHAT_API_URL": "",
        "WECHAT_API_KEY": "",
        "WECHAT_MODE": "live",
    }.items():
        config.set_config_value(key, value)
    return tmp_path


def test_fixture_returns_structured_results(isolated):
    data = private_search.search("xhs", "露营装备", fixture=True)
    assert data["ok"] is True
    assert data["provider"] == "xhs"
    assert data["results"]
    assert data["sources"] == data["results"]
    item = data["results"][0]
    assert {"title", "url", "snippet", "source", "published_date", "author", "id"} <= set(item)
    wechat = private_search.search("wechat", "某品牌财报解读", fixture=True)
    assert wechat["ok"] is True and wechat["results"][0]["source"] == "wechat"


def test_unconfigured_is_auth_required(isolated):
    data = private_search.search("xhs", "露营装备")
    assert data["ok"] is False
    assert data["results"] == []
    assert data["error"]["code"] == "auth_required"


def test_http_error_mapping(isolated, monkeypatch):
    config.set_config_value("XHS_API_URL", "https://example.invalid")
    config.set_config_value("XHS_API_KEY", "secret-value")

    def boom(*_args, **_kwargs):
        raise private_search.PrivateSearchError("rate_limited", "HTTP 429")

    monkeypatch.setattr(private_search, "_http_json", boom)
    data = private_search.search("xhs", "露营装备")
    assert data["error"]["code"] == "rate_limited"
    assert "secret-value" not in json.dumps(data)


def test_empty_upstream(isolated, monkeypatch):
    config.set_config_value("WECHAT_API_URL", "https://example.invalid")
    config.set_config_value("WECHAT_API_KEY", "secret-value")
    monkeypatch.setattr(private_search, "_http_json", lambda *args, **kwargs: (200, {"results": []}))
    data = private_search.search("wechat", "某品牌财报解读")
    assert data["error"]["code"] == "empty"


def test_browser_mode_is_upstream(isolated):
    config.set_config_value("XHS_MODE", "browser")
    data = private_search.search("xhs", "露营装备")
    assert data["error"]["code"] == "upstream"
    status = private_search.channel_status("xhs")
    assert status["experimental"] is True


def test_doctor_attachment_lists_channels(isolated):
    info = private_search.attach_private_status({"provider_health": {"providers": []}, "capability_status": {}})
    assert set(info["private_search"]) == {"xhs", "wechat"}
    assert {item["provider"] for item in info["provider_health"]["providers"]} == {"xhs", "wechat"}
    assert info["capability_status"]["private_search"]["explicit_only"] == ["xhs", "wechat"]
