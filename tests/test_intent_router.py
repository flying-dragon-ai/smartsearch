import json

import httpx
import pytest

from smart_search import service
from smart_search.jev import JevClient


@pytest.mark.asyncio
@pytest.mark.parametrize("mode,effective", [("hybrid", "jev"), ("jev", "jev"), ("rules", "local"), ("off", "local"), ("local", "local")])
async def test_legacy_modes_preserve_configuration_without_legacy_requests(monkeypatch, mode, effective):
    values = {
        "SMART_SEARCH_INTENT_ROUTER": mode,
        "INTENT_EMBEDDING_API_URL": "https://retired.example/embeddings",
        "INTENT_EMBEDDING_API_KEY": "retained-embedding-secret",
        "INTENT_EMBEDDING_MODEL": "old-embedding",
        "INTENT_EMBEDDING_THRESHOLD": "invalid-unused-value",
        "INTENT_CLASSIFIER_API_URL": "https://retired.example/chat/completions",
        "INTENT_CLASSIFIER_API_KEY": "retained-classifier-secret",
        "INTENT_CLASSIFIER_MODEL": "old-classifier",
        "EXA_API_KEY": "exa-test",
    }
    service.config.config_file.write_text(json.dumps(values), encoding="utf-8")
    before = service.config.config_file.read_bytes()

    async def forbidden(*args, **kwargs):
        raise AssertionError("legacy settings must not cause an HTTP request")

    async def retrieve(*args, **kwargs):
        return {"ok": True, "results": [{"url": "https://example.org/source", "content": "Retrieved text"}]}

    monkeypatch.setattr(httpx.AsyncClient, "send", forbidden)
    monkeypatch.setattr(service, "exa_search", retrieve)
    route = await service.route("React useEffect docs")
    result = await service.search("React useEffect docs")
    assert route["ok"] and result["ok"]
    assert service.config.intent_router_mode == effective
    assert service.config.effective_values()["SMART_SEARCH_INTENT_ROUTER"] == effective
    assert service.config.config_file.read_bytes() == before
    assert service.config.get_config_info()["config_parameter_errors"] == []
    assert result["routing_decision"]["router_engines_used"] == ["rules"]
    service.config.set_config_value("EXA_API_KEY", "replacement-exa-secret")
    saved = service.config.get_saved_config(masked=False)
    assert saved["INTENT_EMBEDDING_API_KEY"] == values["INTENT_EMBEDDING_API_KEY"]
    assert saved["INTENT_CLASSIFIER_API_KEY"] == values["INTENT_CLASSIFIER_API_KEY"]
    assert saved["SMART_SEARCH_INTENT_ROUTER"] == mode


@pytest.mark.asyncio
async def test_route_outputs_multiple_capabilities_for_url_verification(monkeypatch):
    monkeypatch.setenv("SMART_SEARCH_INTENT_ROUTER", "rules")
    result = await service.route("请核验这个链接里的说法 https://example.com/source", validation="strict")
    assert result["ok"]
    assert set(result["required_capabilities"]) == {"web_search", "web_fetch"}
    assert result["fetch_intent"]
    assert not result["web_current_intent"]
    assert result["intent_signals"]["strict_validation"]
    assert not result["executed_search"]


@pytest.mark.parametrize("query, docs, vertical", [
    ("What is the capital of France", False, False),
    ("rapid prototyping methods", False, False),
    ("nuclear reactor safety", False, False),
    ("annual report 2025 revenue", False, False),
    ("lawn care tips", False, False),
    ("React useEffect cleanup", True, False),
    ("python3 asyncio", True, False),
    ("Vue3 composition API", True, False),
    ("调用api接口超时", True, False),
    ("list of web frameworks", True, False),
    ("Next.js app router", True, False),
    ("github repos about rust", False, True),
])
def test_docs_and_vertical_keywords_match_whole_words(query, docs, vertical):
    route = service.build_rules_route(query, mode="rules")
    assert (route.docs_intent, route.intent_signals["vertical_intent"]) == (docs, vertical)


@pytest.mark.asyncio
async def test_route_keeps_zh_current_field_narrow_for_english_current_queries():
    result = await service.route("today AI news", mode="local")
    assert not result["zh_current_intent"]
    assert result["web_current_intent"]
    assert result["required_capabilities"] == ["web_search"]


@pytest.mark.asyncio
async def test_remote_preview_requires_explicit_opt_in_and_respects_local_override(monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "jev-test")
    monkeypatch.setenv("EXA_API_KEY", "exa-test")
    calls = []

    async def judge(self, state, questions, timeout):
        calls.append(state)
        return {"answers": {key: {"type": "noul", "noul": 0.95} for key in questions}}

    monkeypatch.setattr(JevClient, "_request", judge)
    assert (await service.route("Find sources"))["executed_search"] is False
    assert (await service.route("Find sources", mode="off", allow_remote=True))["executed_search"] is False
    assert calls == []
    result = await service.route("Find sources", mode="hybrid", allow_remote=True)
    assert result["ok"]
    assert len(calls) == 1
    assert len(result["selected_channels"]) == 1
    assert result["provider_selection"] == "jev"


def test_deep_planner_is_offline_with_remote_credentials(monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "jev-test")
    monkeypatch.setenv("INTENT_CLASSIFIER_API_KEY", "retired-secret")

    async def forbidden(*args, **kwargs):
        raise AssertionError("offline planner must not call a provider")

    monkeypatch.setattr(httpx.AsyncClient, "send", forbidden)
    result = service.build_deep_research_plan("React useEffect API docs")
    assert result["ok"]
    assert result["intent_signals"]["docs_api_intent"]
    assert result["preflight"]["executed_by_deep_command"] is False
