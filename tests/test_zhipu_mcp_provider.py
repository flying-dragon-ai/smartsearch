import json

import httpx
import pytest

from smart_search.providers.zhipu_mcp import ZhipuMCPProvider


class FakeZhipuMCPClient:
    calls = []
    response: httpx.Response | None = None
    responses: list[httpx.Response] = []
    exception: Exception | None = None

    def __init__(self, timeout, follow_redirects=True):
        self.timeout = timeout
        self.follow_redirects = follow_redirects

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def post(self, url, headers, json):
        self.__class__.calls.append({"url": url, "headers": headers, "json": json, "timeout": self.timeout})
        if self.__class__.exception:
            raise self.__class__.exception
        if self.__class__.responses:
            return self.__class__.responses.pop(0)
        return self.__class__.response


@pytest.fixture(autouse=True)
def reset_fake_client():
    FakeZhipuMCPClient.calls = []
    FakeZhipuMCPClient.response = None
    FakeZhipuMCPClient.responses = []
    FakeZhipuMCPClient.exception = None


def _request(url: str) -> httpx.Request:
    return httpx.Request("POST", url)


def _initialize_response(url: str, session_id: str = "zmcp-session") -> httpx.Response:
    return httpx.Response(
        200,
        json={"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "2024-11-05"}},
        headers={"Mcp-Session-Id": session_id},
        request=_request(url),
    )


@pytest.mark.asyncio
async def test_zhipu_mcp_web_search_calls_tool_and_parses_results(monkeypatch):
    url = "https://open.bigmodel.cn/api/mcp/web_search_prime/mcp"
    FakeZhipuMCPClient.responses = [
        _initialize_response(url),
        httpx.Response(
            200,
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": "### 1. Result\n- **URL**: https://example.com\nSnippet",
                        }
                    ]
                },
            },
            request=_request(url),
        ),
    ]
    monkeypatch.setattr("smart_search.providers.zhipu_mcp.httpx.AsyncClient", FakeZhipuMCPClient)

    provider = ZhipuMCPProvider(url, "zmcp-secret")
    data = json.loads(await provider.web_search("query", count=2))

    assert data["ok"] is True
    assert data["provider"] == "zhipu-mcp"
    assert data["tool"] == "web_search_prime"
    assert data["results"][0]["url"] == "https://example.com"
    initialize_call = FakeZhipuMCPClient.calls[0]
    assert initialize_call["headers"]["Authorization"] == "Bearer zmcp-secret"
    assert initialize_call["json"]["method"] == "initialize"
    assert initialize_call["json"]["params"]["protocolVersion"] == "2024-11-05"
    call = FakeZhipuMCPClient.calls[1]
    assert call["headers"]["Authorization"] == "Bearer zmcp-secret"
    assert call["headers"]["Mcp-Session-Id"] == "zmcp-session"
    assert call["json"]["method"] == "tools/call"
    assert call["json"]["params"]["name"] == "web_search_prime"
    assert call["json"]["params"]["arguments"] == {"search_query": "query"}


@pytest.mark.asyncio
async def test_zhipu_mcp_reader_returns_content(monkeypatch):
    url = "https://open.bigmodel.cn/api/mcp/web_reader/mcp"
    FakeZhipuMCPClient.responses = [
        _initialize_response(url),
        httpx.Response(
            200,
            json={"jsonrpc": "2.0", "id": 2, "result": {"content": [{"type": "text", "text": "# Page"}]}},
            request=_request(url),
        ),
    ]
    monkeypatch.setattr("smart_search.providers.zhipu_mcp.httpx.AsyncClient", FakeZhipuMCPClient)

    provider = ZhipuMCPProvider(url, "zmcp-secret", provider_id="zhipu-mcp-reader")
    data = json.loads(await provider.web_reader("https://example.com"))

    assert data["ok"] is True
    assert data["provider"] == "zhipu-mcp-reader"
    assert data["tool"] == "webReader"
    assert data["content"] == "# Page"
    assert FakeZhipuMCPClient.calls[1]["headers"]["Mcp-Session-Id"] == "zmcp-session"
    assert FakeZhipuMCPClient.calls[1]["json"]["params"]["arguments"] == {"url": "https://example.com"}


@pytest.mark.asyncio
async def test_zhipu_mcp_reader_json_error_text_is_provider_error(monkeypatch):
    url = "https://open.bigmodel.cn/api/mcp/web_reader/mcp"
    FakeZhipuMCPClient.responses = [
        _initialize_response(url),
        httpx.Response(
            200,
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "result": {"content": [{"type": "text", "text": '"{\\"error\\":\\"fetch failed\\"}"'}]},
            },
            request=_request(url),
        ),
    ]
    monkeypatch.setattr("smart_search.providers.zhipu_mcp.httpx.AsyncClient", FakeZhipuMCPClient)

    provider = ZhipuMCPProvider(url, "zmcp-secret", provider_id="zhipu-mcp-reader")
    data = json.loads(await provider.web_reader("https://example.com"))

    assert data["ok"] is False
    assert data["error_type"] == "provider_error"
    assert data["error"] == "fetch failed"


@pytest.mark.asyncio
async def test_zhipu_mcp_content_mcp_401_is_auth_error(monkeypatch):
    url = "https://open.bigmodel.cn/api/mcp/web_search_prime/mcp"
    FakeZhipuMCPClient.responses = [
        _initialize_response(url),
        httpx.Response(
            200,
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "result": {"content": [{"type": "text", "text": "MCP error -401: Api key not found"}]},
            },
            request=_request(url),
        ),
    ]
    monkeypatch.setattr("smart_search.providers.zhipu_mcp.httpx.AsyncClient", FakeZhipuMCPClient)

    provider = ZhipuMCPProvider(url, "zmcp-secret")
    data = json.loads(await provider.web_search("query"))

    assert data["ok"] is False
    assert data["error_type"] == "auth_error"
    assert "Api key not found" in data["error"]


@pytest.mark.asyncio
async def test_zhipu_mcp_tool_error_redacts_credentials(monkeypatch):
    url = "https://open.bigmodel.cn/api/mcp/web_search_prime/mcp"
    leaked_secret = "zmcp-secret"
    FakeZhipuMCPClient.responses = [
        _initialize_response(url),
        httpx.Response(
            200,
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "result": {
                    "isError": True,
                    "content": [
                        {
                            "type": "text",
                            "text": f"MCP error -401: upstream repeated {leaked_secret}",
                        }
                    ],
                },
            },
            request=_request(url),
        ),
    ]
    monkeypatch.setattr("smart_search.providers.zhipu_mcp.httpx.AsyncClient", FakeZhipuMCPClient)

    provider = ZhipuMCPProvider(url, "zmcp-secret")
    data = json.loads(await provider.web_search("query"))

    rendered = json.dumps(data)
    assert data["ok"] is False
    assert data["error_type"] == "auth_error"
    assert leaked_secret not in rendered
    assert "[REDACTED]" in data["error"]
    assert data["content"] == data["error"]
    assert data["raw_content"] == data["error"]


@pytest.mark.asyncio
async def test_zhipu_mcp_zread_tools_send_expected_arguments(monkeypatch):
    url = "https://open.bigmodel.cn/api/mcp/zread/mcp"
    FakeZhipuMCPClient.responses = [
        _initialize_response(url),
        httpx.Response(
            200,
            json={"jsonrpc": "2.0", "id": 2, "result": {"content": [{"type": "text", "text": "ok"}]}},
            request=_request(url),
        ),
        httpx.Response(
            200,
            json={"jsonrpc": "2.0", "id": 3, "result": {"content": [{"type": "text", "text": "ok"}]}},
            request=_request(url),
        ),
        httpx.Response(
            200,
            json={"jsonrpc": "2.0", "id": 4, "result": {"content": [{"type": "text", "text": "ok"}]}},
            request=_request(url),
        ),
    ]
    monkeypatch.setattr("smart_search.providers.zhipu_mcp.httpx.AsyncClient", FakeZhipuMCPClient)

    provider = ZhipuMCPProvider(url, "zmcp-secret", provider_id="zhipu-mcp-zread")
    await provider.search_doc("owner/repo", "install", max_results=3)
    await provider.get_repo_structure("owner/repo", ref="main")
    await provider.read_file("owner/repo", "README.md", ref="main")

    assert [call["json"]["method"] for call in FakeZhipuMCPClient.calls] == [
        "initialize",
        "tools/call",
        "tools/call",
        "tools/call",
    ]
    assert [call["json"]["params"]["name"] for call in FakeZhipuMCPClient.calls[1:]] == [
        "search_doc",
        "get_repo_structure",
        "read_file",
    ]
    assert all(call["headers"]["Mcp-Session-Id"] == "zmcp-session" for call in FakeZhipuMCPClient.calls[1:])
    assert FakeZhipuMCPClient.calls[0]["json"]["method"] == "initialize"
    assert FakeZhipuMCPClient.calls[1]["json"]["params"]["arguments"] == {
        "repo_name": "owner/repo",
        "query": "install",
    }
    assert FakeZhipuMCPClient.calls[3]["json"]["params"]["arguments"] == {
        "repo_name": "owner/repo",
        "file_path": "README.md",
    }


@pytest.mark.asyncio
async def test_zhipu_mcp_http_401_is_auth_error(monkeypatch):
    url = "https://open.bigmodel.cn/api/mcp/web_search_prime/mcp"
    FakeZhipuMCPClient.responses = [
        _initialize_response(url),
        httpx.Response(
            401,
            text="invalid token",
            request=_request(url),
        ),
    ]
    monkeypatch.setattr("smart_search.providers.zhipu_mcp.httpx.AsyncClient", FakeZhipuMCPClient)

    provider = ZhipuMCPProvider(url, "zmcp-secret")
    data = json.loads(await provider.web_search("query"))

    assert data["ok"] is False
    assert data["error_type"] == "auth_error"
    assert "HTTP 401" in data["error"]
    assert "zmcp-secret" not in data["error"]


@pytest.mark.asyncio
async def test_zhipu_mcp_initialize_401_is_auth_error(monkeypatch):
    url = "https://open.bigmodel.cn/api/mcp/web_search_prime/mcp"
    FakeZhipuMCPClient.responses = [
        httpx.Response(
            401,
            text="invalid token",
            request=_request(url),
        )
    ]
    monkeypatch.setattr("smart_search.providers.zhipu_mcp.httpx.AsyncClient", FakeZhipuMCPClient)

    provider = ZhipuMCPProvider(url, "zmcp-secret")
    data = json.loads(await provider.web_search("query"))

    assert data["ok"] is False
    assert data["error_type"] == "auth_error"
    assert "HTTP 401" in data["error"]
    assert "zmcp-secret" not in data["error"]
    assert [call["json"]["method"] for call in FakeZhipuMCPClient.calls] == ["initialize"]


@pytest.mark.asyncio
async def test_zhipu_mcp_initialize_without_session_header_is_provider_error(monkeypatch):
    url = "https://open.bigmodel.cn/api/mcp/web_search_prime/mcp"
    FakeZhipuMCPClient.responses = [
        httpx.Response(
            200,
            json={"jsonrpc": "2.0", "id": 1, "result": {}},
            request=_request(url),
        )
    ]
    monkeypatch.setattr("smart_search.providers.zhipu_mcp.httpx.AsyncClient", FakeZhipuMCPClient)

    provider = ZhipuMCPProvider(url, "zmcp-secret")
    data = json.loads(await provider.web_search("query"))

    assert data["ok"] is False
    assert data["error_type"] == "provider_error"
    assert "Mcp-Session-Id" in data["error"]
    assert [call["json"]["method"] for call in FakeZhipuMCPClient.calls] == ["initialize"]


@pytest.mark.asyncio
async def test_zhipu_mcp_sse_response_is_parsed(monkeypatch):
    url = "https://open.bigmodel.cn/api/mcp/web_search_prime/mcp"
    FakeZhipuMCPClient.responses = [
        _initialize_response(url),
        httpx.Response(
            200,
            text='event: message\ndata: {"jsonrpc":"2.0","id":2,"result":{"content":[{"type":"text","text":"### Result\\nhttps://example.com"}]}}\n\n',
            headers={"content-type": "text/event-stream"},
            request=_request(url),
        ),
    ]
    monkeypatch.setattr("smart_search.providers.zhipu_mcp.httpx.AsyncClient", FakeZhipuMCPClient)

    provider = ZhipuMCPProvider(url, "zmcp-secret")
    data = json.loads(await provider.web_search("query"))

    assert data["ok"] is True
    assert data["results"][0]["url"] == "https://example.com"
