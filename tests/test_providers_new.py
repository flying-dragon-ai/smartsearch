import json

import httpx
import pytest

from smart_search.providers.context7 import Context7Provider
from smart_search.providers.exa import ExaSearchProvider
from smart_search.providers.zhipu import ZhipuWebSearchProvider


@pytest.mark.asyncio
async def test_zhipu_provider_normalizes_search_results(monkeypatch):
    class FakeAsyncClient:
        def __init__(self, timeout, follow_redirects=True):
            self.timeout = timeout
            self.follow_redirects = follow_redirects

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, endpoint, headers, json):
            return httpx.Response(
                200,
                json={
                    "request_id": "r1",
                    "search_result": [
                        {
                            "title": "Title",
                            "content": "Snippet",
                            "link": "https://example.com",
                            "media": "Example",
                            "publish_date": "2026-05-12",
                        }
                    ],
                },
                request=httpx.Request("POST", endpoint),
            )

    monkeypatch.setattr("smart_search.providers.zhipu.httpx.AsyncClient", FakeAsyncClient)
    provider = ZhipuWebSearchProvider("https://open.bigmodel.cn/api", "key")

    data = json.loads(await provider.search("hello"))

    assert data["ok"] is True
    assert data["results"][0]["url"] == "https://example.com"
    assert data["results"][0]["provider"] == "zhipu"


@pytest.mark.asyncio
async def test_zhipu_provider_uses_configured_engine_and_call_override(monkeypatch):
    payloads = []

    class FakeAsyncClient:
        def __init__(self, timeout, follow_redirects=True):
            self.timeout = timeout
            self.follow_redirects = follow_redirects

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, endpoint, headers, json):
            payloads.append(json.copy())
            return httpx.Response(
                200,
                json={"request_id": "r1", "search_result": []},
                request=httpx.Request("POST", endpoint),
            )

    monkeypatch.setattr("smart_search.providers.zhipu.httpx.AsyncClient", FakeAsyncClient)
    provider = ZhipuWebSearchProvider("https://open.bigmodel.cn/api", "key", search_engine="search_pro")

    data = json.loads(await provider.search("hello"))
    override_data = json.loads(await provider.search("hello", search_engine="search_pro_quark"))

    assert data["search_engine"] == "search_pro"
    assert override_data["search_engine"] == "search_pro_quark"
    assert payloads[0]["search_engine"] == "search_pro"
    assert payloads[1]["search_engine"] == "search_pro_quark"


@pytest.mark.asyncio
async def test_zhipu_provider_reports_rate_limit_without_retry(monkeypatch):
    calls = []

    class FakeAsyncClient:
        def __init__(self, timeout, follow_redirects=True):
            self.timeout = timeout
            self.follow_redirects = follow_redirects

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, endpoint, headers, json):
            calls.append(endpoint)
            return httpx.Response(
                429,
                json={"error": "rate limited"},
                request=httpx.Request("POST", endpoint),
            )

    monkeypatch.setattr("smart_search.providers.zhipu.httpx.AsyncClient", FakeAsyncClient)
    provider = ZhipuWebSearchProvider("https://open.bigmodel.cn/api", "key")

    data = json.loads(await provider.search("test"))

    assert data["ok"] is False
    assert data["error_type"] == "rate_limited"
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_context7_provider_normalizes_library_results(monkeypatch):
    class FakeAsyncClient:
        def __init__(self, timeout, follow_redirects=True):
            self.timeout = timeout
            self.follow_redirects = follow_redirects

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get(self, endpoint, headers):
            return httpx.Response(
                200,
                json=[{"id": "/reactjs/react.dev", "title": "React", "description": "UI"}],
                headers={"content-type": "application/json"},
                request=httpx.Request("GET", endpoint),
            )

    monkeypatch.setattr("smart_search.providers.context7.httpx.AsyncClient", FakeAsyncClient)
    provider = Context7Provider("https://context7.com", "key")

    data = json.loads(await provider.library("react", "hooks"))

    assert data["ok"] is True
    assert data["results"][0]["id"] == "/reactjs/react.dev"
    assert data["results"][0]["provider"] == "context7"


@pytest.mark.asyncio
async def test_context7_provider_uses_shared_http_error_taxonomy(monkeypatch):
    class FakeAsyncClient:
        def __init__(self, timeout, follow_redirects=True):
            self.timeout = timeout
            self.follow_redirects = follow_redirects

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get(self, endpoint, headers):
            return httpx.Response(
                422,
                json={"error": "invalid library id"},
                request=httpx.Request("GET", endpoint),
            )

    monkeypatch.setattr("smart_search.providers.context7.httpx.AsyncClient", FakeAsyncClient)
    provider = Context7Provider("https://context7.com", "key")

    data = json.loads(await provider.docs("/invalid", "hooks"))

    assert data["ok"] is False
    assert data["error_type"] == "parameter_error"
    assert "HTTP 422" in data["error"]


@pytest.mark.asyncio
async def test_context7_library_uses_official_search_endpoint(monkeypatch):
    def handler(request):
        assert request.method == "GET"
        assert request.url.path == "/api/v2/libs/search"
        assert dict(request.url.params) == {"libraryName": "React", "query": "useEffect cleanup"}
        return httpx.Response(200, json={"results": [{
            "id": "/reactjs/react.dev", "title": "React", "description": "React documentation",
            "trustScore": 10, "benchmarkScore": 85.23, "totalSnippets": 4342, "stars": 11311,
        }], "searchFilterApplied": False})

    client = httpx.AsyncClient
    monkeypatch.setattr("smart_search.providers.context7.httpx.AsyncClient", lambda **kwargs: client(transport=httpx.MockTransport(handler), **kwargs))
    data = json.loads(await Context7Provider("https://context7.com", "key").library("React", "useEffect cleanup"))

    assert data["ok"]
    assert data["results"] == [{
        "id": "/reactjs/react.dev", "title": "React", "description": "React documentation",
        "trust_score": 10, "benchmark_score": 85.23, "total_snippets": 4342, "stars": 11311, "provider": "context7",
    }]


@pytest.mark.asyncio
async def test_context7_library_without_query_searches_by_name(monkeypatch):
    def handler(request):
        assert dict(request.url.params) == {"libraryName": "react", "query": "react"}
        return httpx.Response(200, json={"results": []})

    client = httpx.AsyncClient
    monkeypatch.setattr("smart_search.providers.context7.httpx.AsyncClient", lambda **kwargs: client(transport=httpx.MockTransport(handler), **kwargs))
    assert json.loads(await Context7Provider("https://context7.com", "key").library("react"))["ok"]


@pytest.mark.asyncio
@pytest.mark.parametrize("status,body,error_type", [
    (404, {"error": "not_found"}, "provider_error"),
    (404, "Not found", "provider_error"),
    (500, {"error": "no_relevant_snippets"}, "network_error"),
])
async def test_context7_docs_preserves_other_errors(monkeypatch, status, body, error_type):
    monkeypatch.setenv("SMART_SEARCH_RETRY_MAX_ATTEMPTS", "0")

    def handler(request):
        return httpx.Response(status, **({"json": body} if isinstance(body, dict) else {"text": body}))

    client = httpx.AsyncClient
    monkeypatch.setattr("smart_search.providers.context7.httpx.AsyncClient", lambda **kwargs: client(transport=httpx.MockTransport(handler), **kwargs))
    data = json.loads(await Context7Provider("https://context7.com", "key").docs("/reactjs/react.dev", "hooks"))

    assert not data["ok"]
    assert data["error_type"] == error_type
    assert f"HTTP {status}" in data["error"]
    assert (body["error"] if isinstance(body, dict) else body) in data["error"]


@pytest.mark.asyncio
async def test_exa_provider_reports_bad_request_as_parameter_error(monkeypatch):
    class FakeAsyncClient:
        def __init__(self, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, endpoint, headers, json):
            return httpx.Response(
                400,
                json={"error": "invalid includeDomains"},
                request=httpx.Request("POST", endpoint),
            )

    monkeypatch.setattr("smart_search.providers.exa.httpx.AsyncClient", FakeAsyncClient)
    provider = ExaSearchProvider("https://api.exa.ai", "key")

    data = json.loads(await provider.search("test", include_domains=["github.com freertos.org"]))

    assert data["ok"] is False
    assert data["error_type"] == "parameter_error"
    assert "HTTP 400" in data["error"]
    assert "invalid includeDomains" in data["error"]


def _zhipu_client_returning(payload):
    class FakeAsyncClient:
        def __init__(self, timeout, follow_redirects=True):
            self.timeout = timeout
            self.follow_redirects = follow_redirects

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, endpoint, headers, json):
            return httpx.Response(200, json=payload, request=httpx.Request("POST", endpoint))

    return FakeAsyncClient


@pytest.mark.parametrize(
    ("payload", "expected_type"),
    [
        ({"error": {"code": "1002", "message": "Authorization Token 非法"}}, "auth_error"),
        ({"error": {"code": "1113", "message": "账户余额不足，请充值"}}, "rate_limited"),
        ({"error": {"code": "1210", "message": "参数不合法"}}, "provider_error"),
        ({"code": 1002, "message": "invalid api key"}, "auth_error"),
    ],
)
@pytest.mark.asyncio
async def test_zhipu_provider_classifies_errors_returned_with_http_200(monkeypatch, payload, expected_type):
    monkeypatch.setattr("smart_search.providers.zhipu.httpx.AsyncClient", _zhipu_client_returning(payload))
    provider = ZhipuWebSearchProvider("https://open.bigmodel.cn/api", "secret-key")

    data = json.loads(await provider.search("hello"))

    assert data["ok"] is False
    assert data["error_type"] == expected_type
    assert "secret-key" not in data["error"]


@pytest.mark.asyncio
async def test_zhipu_provider_keeps_an_empty_result_set_successful(monkeypatch):
    monkeypatch.setattr(
        "smart_search.providers.zhipu.httpx.AsyncClient",
        _zhipu_client_returning({"request_id": "r1", "code": 200, "search_result": []}),
    )
    provider = ZhipuWebSearchProvider("https://open.bigmodel.cn/api", "key")

    data = json.loads(await provider.search("hello"))

    assert data["ok"] is True
    assert data["results"] == []
