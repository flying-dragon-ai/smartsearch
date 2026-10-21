import hashlib

import httpx
import pytest

from smart_search import jev_search, service
from smart_search.provider_errors import ProviderCallError
from smart_search.providers.deepseek import DeepSeekToolsProvider, search_query, tools_endpoint


class FakeDeepSeekClient:
    calls = []
    responses: dict[str, httpx.Response] = {}

    def __init__(self, timeout, follow_redirects=True):
        self.timeout = timeout

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def post(self, url, headers, json):
        self.__class__.calls.append({"url": url, "headers": headers, "json": json})
        return self.__class__.responses[url.rsplit("/", 1)[-1]]


@pytest.fixture(autouse=True)
def fake_client(monkeypatch):
    FakeDeepSeekClient.calls = []
    FakeDeepSeekClient.responses = {}
    monkeypatch.setattr("smart_search.providers.deepseek.httpx.AsyncClient", FakeDeepSeekClient)


def _response(tool: str, payload, status_code: int = 200) -> httpx.Response:
    request = httpx.Request("POST", f"https://api.deepseek.com/v1/tools/{tool}")
    return httpx.Response(status_code, json=payload, request=request)


def _result(**overrides):
    item = {
        "rerank_score": 2.4, "title": "DeepSeek V4", "url": "https://example.com/v4",
        "snippet": "short", "summary": "long query-focused summary", "content": "",
        "site_name": "Example News", "site_icon": None, "date": "2026-06-01T00:00:00+00:00", "authority": 3,
    }
    item.update(overrides)
    return item


@pytest.mark.parametrize("base", ["https://api.deepseek.com", "https://api.deepseek.com/", "https://api.deepseek.com/v1/"])
def test_endpoint_accepts_the_chat_api_base_with_or_without_v1(base):
    assert tools_endpoint(base, "search") == "https://api.deepseek.com/v1/tools/search"


def test_long_queries_fit_the_128_character_limit():
    words = "deepseek " * 40
    assert len(search_query(words)) <= 128
    assert not search_query(words).endswith("deeps")
    assert len(search_query("深" * 300)) == 128
    assert search_query("  a\n b  ") == "a b"


@pytest.mark.asyncio
async def test_search_sends_bearer_key_and_normalizes_results():
    FakeDeepSeekClient.responses["search"] = _response("search", {"results": [_result(), _result(site_name=None, date=None, summary="")]})

    results = await DeepSeekToolsProvider("https://api.deepseek.com", "ds-secret").search("deepseek v4", max_results=80)

    call = FakeDeepSeekClient.calls[0]
    assert call["url"] == "https://api.deepseek.com/v1/tools/search"
    assert call["headers"]["Authorization"] == "Bearer ds-secret"
    assert call["json"] == {"query": "deepseek v4", "count": 50}
    assert results[0] == {
        "title": "DeepSeek V4", "url": "https://example.com/v4", "description": "long query-focused summary",
        "provider": "deepseek", "source": "Example News", "published_date": "2026-06-01T00:00:00+00:00",
    }
    assert results[1]["description"] == "short"
    assert "source" not in results[1] and "published_date" not in results[1]


@pytest.mark.asyncio
async def test_search_failures_are_classified_without_leaking_the_key():
    FakeDeepSeekClient.responses["search"] = _response(
        "search", {"error": {"message": "invalid key ds-secret", "type": "authentication_error"}}, 401)

    with pytest.raises(ProviderCallError) as raised:
        await DeepSeekToolsProvider("https://api.deepseek.com", "ds-secret").search("q")

    assert raised.value.error_type == "auth_error"
    assert "ds-secret" not in raised.value.error

    FakeDeepSeekClient.responses["search"] = _response("search", {"data": []})
    with pytest.raises(ProviderCallError) as raised:
        await DeepSeekToolsProvider("https://api.deepseek.com", "ds-secret").search("q")
    assert raised.value.error_type == "parse_error"


@pytest.mark.asyncio
async def test_fetch_returns_markdown_and_treats_page_rejections_as_no_content():
    provider = DeepSeekToolsProvider("https://api.deepseek.com", "ds-secret")
    FakeDeepSeekClient.responses["fetch"] = _response("fetch", {"title": "Example", "content": "# Example\n\nBody"})

    assert await provider.fetch("https://example.com") == {"title": "Example", "content": "# Example\n\nBody"}
    assert FakeDeepSeekClient.calls[0]["json"] == {"url": "https://example.com"}

    for status in (403, 404):
        FakeDeepSeekClient.responses["fetch"] = _response("fetch", {"error": {"message": "no content"}}, status)
        assert await provider.fetch("https://example.com/private") is None

    FakeDeepSeekClient.responses["fetch"] = _response("fetch", {"error": {"message": "Insufficient Balance"}}, 402)
    with pytest.raises(ProviderCallError) as raised:
        await provider.fetch("https://example.com")
    assert raised.value.error_type == "provider_error"
    assert "Insufficient Balance" in raised.value.error


@pytest.mark.asyncio
async def test_deepseek_alone_covers_search_and_fetch(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "ds-secret")
    status = service.get_capability_status()
    assert status["web_search"]["configured"] == ["deepseek"]
    assert status["web_fetch"]["configured"] == ["deepseek"]
    assert service.validate_minimum_profile()["ok"]

    channels = {item["id"] for item in jev_search.available_channels(service, "read https://example.com/a", [])}
    fetch_id = "deepseek:fetch:" + hashlib.sha256(b"https://example.com/a").hexdigest()[:12]
    assert {"deepseek:search", fetch_id} <= channels

    FakeDeepSeekClient.responses["fetch"] = _response("fetch", {"title": "A", "content": "# Page A"})
    result = await service.fetch("https://example.com/a")
    assert result["ok"] and result["provider"] == "deepseek" and result["content"] == "# Page A"


@pytest.mark.asyncio
async def test_unfetchable_pages_do_not_cool_down_the_provider(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "ds-secret")
    FakeDeepSeekClient.responses["fetch"] = _response("fetch", {"error": {"message": "no markdown"}}, 404)

    for _ in range(4):
        result = await service.fetch("https://example.com/binary")
        assert result["ok"] is False
        assert result["provider_attempts"][-1]["status"] == "empty"

    assert service._provider_health_status("deepseek")["state"] != "cooldown"


@pytest.mark.asyncio
async def test_connection_test_probes_search_and_fetch(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "ds-secret")
    FakeDeepSeekClient.responses["search"] = _response("search", {"results": [_result()]})
    FakeDeepSeekClient.responses["fetch"] = _response("fetch", {"title": "Example", "content": "Example Domain"})

    result = await service.test_provider_connection("deepseek")

    assert result["ok"] is True
    assert sorted(call["url"].rsplit("/", 1)[-1] for call in FakeDeepSeekClient.calls) == ["fetch", "search"]

    FakeDeepSeekClient.responses["fetch"] = _response("fetch", {"error": {"message": "blocked"}}, 403)
    assert (await service.test_provider_connection("deepseek"))["status"] == "warning"

    FakeDeepSeekClient.responses["search"] = _response("search", {"error": {"message": "bad key"}}, 401)
    assert (await service.test_provider_connection("deepseek"))["status"] == "auth_error"


def test_docs_questions_use_web_search_when_no_docs_channel_is_configured(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "ds-secret")
    query = "React useEffect API 清理函数"
    assert service.build_rules_route(query, mode="rules").docs_intent

    selected = jev_search.fallback_channels(service, query, jev_search.available_channels(service, query, []), 1)
    assert [item["id"] for item in selected] == ["deepseek:search"]

    monkeypatch.setenv("CONTEXT7_API_KEY", "c7-secret")
    selected = jev_search.fallback_channels(service, query, jev_search.available_channels(service, query, []), 1)
    assert [item["provider"] for item in selected] == ["context7"]
