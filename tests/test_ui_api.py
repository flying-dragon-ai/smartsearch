"""The adapter layer, tested without opening a socket."""

import json

import pytest

from smart_search import service, ui_api
from smart_search.provider_health import ProviderHealthStore
from smart_search.skill_installer import SKILL_TARGETS


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(service.config, "_config_file", tmp_path / "config.json")
    monkeypatch.setattr(service.config, "_cached_model", None)
    store = ProviderHealthStore(tmp_path / "provider_health.json", cooldown_seconds=900, failure_threshold=2)
    monkeypatch.setattr(service, "provider_health", store)
    return store


def test_state_is_json_serialisable_and_complete(isolated):
    payload = ui_api.state()
    json.dumps(payload)
    assert payload["ok"] is True
    assert len(payload["metadata"]["fields"]) == len(service.config._CONFIG_KEYS - service.config.RETIRED_ROUTER_KEYS)
    assert len(payload["skill_targets"]) == len(SKILL_TARGETS)


def test_state_masks_every_secret(isolated):
    service.config.set_config_value("EXA_API_KEY", "exa-plaintext-secret")
    service.config.set_config_value("SCIVERSE_API_TOKEN", "sciverse-plaintext-token")
    body = json.dumps(ui_api.state(), ensure_ascii=False)
    assert "exa-plaintext-secret" not in body
    assert "sciverse-plaintext-token" not in body


def test_status_excludes_the_metadata_block(isolated):
    assert "metadata" not in ui_api.status()
    assert "metadata" in ui_api.state()


def test_capability_chains_come_from_the_router_table(isolated):
    chains = ui_api.status()["capability_chains"]
    # Must mirror the one declaration, not a fourth copy of it.
    assert chains == {k: list(v) for k, v in service.RESEARCH_PROFILE_ORDER.items()}


def test_state_agrees_with_the_service_capability_status(isolated):
    service.config.set_config_value("EXA_API_KEY", "k")
    assert ui_api.status()["capability_status"] == service.get_capability_status()


@pytest.mark.asyncio
async def test_test_provider_requires_a_provider(isolated):
    result = await ui_api.test_provider({})
    assert result["error_type"] == "parameter_error"
    assert "exa" in result["known_providers"]


@pytest.mark.asyncio
async def test_test_provider_rejects_a_bad_overrides_type(isolated):
    result = await ui_api.test_provider({"provider": "exa", "overrides": "nope"})
    assert result["error_type"] == "parameter_error"


@pytest.mark.asyncio
async def test_test_provider_rejects_a_bad_timeout(isolated):
    result = await ui_api.test_provider({"provider": "exa", "timeout_seconds": "soon"})
    assert result["error_type"] == "parameter_error"


@pytest.mark.asyncio
async def test_test_provider_delegates(isolated, monkeypatch):
    async def ok_probe():
        return {"status": "ok", "message": "fine"}

    monkeypatch.setitem(service._LIVE_PROBES, "exa", ok_probe)
    service.config.set_config_value("EXA_API_KEY", "k")
    result = await ui_api.test_provider({"provider": "exa"})
    assert result["ok"] is True


@pytest.mark.asyncio
@pytest.mark.parametrize("overrides", [None, {}, {"EXA_API_KEY": "unsaved-synthetic-key"}])
async def test_empty_override_keeps_explicit_snapshot_semantics(isolated, monkeypatch, overrides):
    service.config.set_config_value("EXA_API_KEY", "saved-synthetic-key")
    seen = []

    async def probe():
        seen.append(service.config.exa_api_key)
        return {"status": "ok", "message": "fine"}

    monkeypatch.setitem(service._LIVE_PROBES, "exa", probe)
    payload = {"provider": "exa"}
    if overrides is not None:
        payload["overrides"] = overrides
    result = await ui_api.test_provider(payload)
    assert result["ok"]
    assert result["recorded_as"] == ("exa" if overrides is None else "")
    assert seen == [(overrides or {}).get("EXA_API_KEY", "saved-synthetic-key")]
    assert service.config.exa_api_key == "saved-synthetic-key"


def test_reset_health_validates_its_argument(isolated):
    assert ui_api.reset_health({"providers": "zhipu"})["error_type"] == "parameter_error"
    assert ui_api.reset_health({"providers": ["zhipu"]})["ok"] is True
    assert ui_api.reset_health({})["ok"] is True


def test_reset_health_clears_a_real_cooldown(isolated):
    isolated.record_failure("zhipu", service._provider_fingerprint("zhipu"), "auth_error", "401")
    assert isolated.status("zhipu")["state"] == "cooldown"
    result = ui_api.reset_health({"providers": ["zhipu"]})
    assert result["cleared"] == ["zhipu"]
    assert isolated.status("zhipu")["state"] == "closed"


def test_skills_status_is_read_only(isolated):
    result = ui_api.skills_status()
    assert result["ok"] is True
    assert result["selected"]


def test_skills_status_rejects_an_unknown_target(isolated):
    assert ui_api.skills_status("not-an-editor")["error_type"] == "parameter_error"


# ---- write path ---------------------------------------------------------
def test_apply_config_saves_and_returns_fresh_status(isolated):
    result = ui_api.apply_config({"set": {"EXA_API_KEY": "exa-key", "CONTEXT7_API_KEY": "c7-key"}})
    assert result["ok"] is True
    assert sorted(result["saved"]) == ["CONTEXT7_API_KEY", "EXA_API_KEY"]
    assert "*" in result["saved"]["EXA_API_KEY"], "the echo must be masked too"
    assert result["status"]["capability_status"] == service.get_capability_status()


def test_apply_config_is_all_or_nothing(isolated):
    ui_api.apply_config({"set": {"EXA_API_KEY": "keep-me"}})
    before = service.config.config_file.read_bytes()

    result = ui_api.apply_config({"set": {
        "CONTEXT7_API_KEY": "would-be-saved",
        "SMART_SEARCH_VALIDATION_LEVEL": "not-a-level",
    }})

    assert result["ok"] is False
    assert "SMART_SEARCH_VALIDATION_LEVEL" in result["error"]
    assert service.config.config_file.read_bytes() == before


def test_apply_config_refuses_keys_the_environment_owns(isolated, monkeypatch):
    # The write would succeed and change nothing the user can see, because
    # os.getenv wins on every read. Refusing is the honest answer.
    monkeypatch.setenv("EXA_API_KEY", "from-the-environment")
    result = ui_api.apply_config({"set": {"EXA_API_KEY": "from-the-page"}})
    assert result["ok"] is False
    assert result["shadowed"] == ["EXA_API_KEY"]
    assert not service.config.config_file.exists()


def test_apply_config_refuses_an_env_owned_unset(isolated, monkeypatch):
    monkeypatch.setenv("EXA_API_KEY", "from-the-environment")
    result = ui_api.apply_config({"unset": ["EXA_API_KEY"]})
    assert result["ok"] is False
    assert result["shadowed"] == ["EXA_API_KEY"]


def test_apply_config_unsets(isolated):
    ui_api.apply_config({"set": {"EXA_API_KEY": "exa-key", "CONTEXT7_API_KEY": "c7-key"}})
    result = ui_api.apply_config({"unset": ["EXA_API_KEY"]})
    assert result["ok"] is True
    assert result["unset"] == ["EXA_API_KEY"]
    assert "EXA_API_KEY" not in service.config.get_saved_config(masked=True)


def test_apply_config_validates_its_argument_types(isolated):
    assert ui_api.apply_config({"set": "nope"})["error_type"] == "parameter_error"
    assert ui_api.apply_config({"unset": "nope"})["error_type"] == "parameter_error"


def test_preview_is_offline_and_answers_the_minimum_profile(isolated, monkeypatch):
    monkeypatch.setenv("SMART_SEARCH_MINIMUM_PROFILE", "standard")

    def explode(*args, **kwargs):
        raise AssertionError("preview must not touch the network")

    monkeypatch.setattr("httpx.AsyncClient", explode)

    empty = ui_api.preview({"values": {}})
    assert empty["ok"] is True
    assert empty["minimum_profile_ok"] is False
    assert empty["missing"] == ["retrieval"]

    # One retrieval channel passes, exactly as the overview's minimum profile does.
    single = ui_api.preview({"values": {"EXA_API_KEY": "y"}})
    assert single["minimum_profile_ok"] is True
    assert single["missing"] == []
    assert single["minimum_profile_ok"] == service._minimum_profile_result("standard", single["capability_status"])["ok"]


def test_preview_saves_nothing(isolated):
    ui_api.preview({"values": {"EXA_API_KEY": "never-persisted"}})
    assert not service.config.config_file.exists()


def test_preview_honours_a_disabled_minimum_profile(isolated, monkeypatch):
    monkeypatch.setenv("SMART_SEARCH_MINIMUM_PROFILE", "off")
    result = ui_api.preview({"values": {}})
    assert result["required"] == []
    assert result["minimum_profile_ok"] is True


def test_preview_validates_its_argument(isolated):
    assert ui_api.preview({"values": "nope"})["error_type"] == "parameter_error"


# ---- try it -------------------------------------------------------------
@pytest.mark.asyncio
async def test_run_query_defaults_to_the_free_command(isolated, monkeypatch):
    seen = {}

    async def fake_route(query, **kwargs):
        seen["query"] = query
        return {"ok": True, "required_capabilities": ["docs_search"]}

    monkeypatch.setattr(service, "route", fake_route)
    result = await ui_api.run_query({"query": "React useEffect cleanup"})
    assert result["ok"] is True
    assert seen["query"] == "React useEffect cleanup"


@pytest.mark.asyncio
async def test_run_query_rejects_an_unknown_command(isolated):
    result = await ui_api.run_query({"command": "deep", "query": "x"})
    assert result["error_type"] == "parameter_error"
    assert result["known_commands"] == ["route", "search"]


@pytest.mark.asyncio
async def test_run_query_requires_a_query(isolated):
    assert (await ui_api.run_query({"command": "route"}))["error_type"] == "parameter_error"
    assert (await ui_api.run_query({"query": "   "}))["error_type"] == "parameter_error"


@pytest.mark.asyncio
async def test_run_query_caps_the_query_length(isolated):
    result = await ui_api.run_query({"query": "x" * 2001})
    assert result["error_type"] == "parameter_error"


@pytest.mark.asyncio
async def test_run_query_passes_the_search_timeout(isolated, monkeypatch):
    seen = {}

    async def fake_search(query, **kwargs):
        seen.update(kwargs)
        return {"ok": True}

    monkeypatch.setattr(service, "search", fake_search)
    await ui_api.run_query({"command": "search", "query": "news", "timeout_seconds": 42})
    assert seen["timeout_seconds"] == 42.0
    assert (await ui_api.run_query({
        "command": "search", "query": "news", "timeout_seconds": "soon"
    }))["error_type"] == "parameter_error"
