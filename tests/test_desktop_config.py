"""The desktop and the CLI share these contracts, including concurrent writes."""
import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import httpx
import pytest

from smart_search.i18n import use_language


@pytest.fixture(autouse=True)
def chinese_presentation():
    with use_language("zh"):
        yield

from smart_search import activity, service, ui_api
from smart_search.config import config
from smart_search.desktop_backend import Backend


def test_rejects_stale_revision_and_preserves_broken_file(tmp_path):
    initial = config.revision()
    config.set_config_value("EXA_API_KEY", "first")
    result = ui_api.apply_config({"set": {"EXA_API_KEY": "second"}, "revision": initial})
    assert result["error_type"] == "config_conflict"
    assert config.exa_api_key == "first"
    config.config_file.write_text('{"broken":', encoding="utf-8")
    with pytest.raises(ValueError, match="原文件未修改"):
        config.set_config_value("EXA_API_KEY", "second")
    assert config.config_file.read_text() == '{"broken":'


@pytest.mark.asyncio
@pytest.mark.parametrize("include_secrets", [False, True])
async def test_native_router_save_and_reopen_preserves_legacy_credentials(tmp_path, include_secrets):
    saved = {"SMART_SEARCH_INTENT_ROUTER": "hybrid", "TYPESAFE_API_KEY": "synthetic-jev",
             "INTENT_EMBEDDING_API_KEY": "synthetic-retired", "EXA_API_KEY": "synthetic-exa"}
    config._save_config_file(saved)
    before = config.config_file.read_bytes()
    parameters = {"protocol_version": 1, "config_dir": str(tmp_path), "enable_update_checks": False,
                  "include_config_secrets": include_secrets, "independent_cli": True}
    backend = Backend(lambda _: None)
    try:
        state = await backend.handle("initialize", parameters)
        fields = {item["key"]: item for item in state["metadata"]["fields"]}
        assert fields["SMART_SEARCH_INTENT_ROUTER"]["choices"] == ["jev", "local"]
        assert not config.RETIRED_ROUTER_KEYS.intersection(fields)
        assert state["values"]["SMART_SEARCH_INTENT_ROUTER"] == "jev"
        assert config.config_file.read_bytes() == before
        applied = await backend.handle("config.apply", {"revision": state["revision"], "set": {
            "SMART_SEARCH_INTENT_ROUTER": "local", "SMART_SEARCH_JEV_MAX_ROUNDS": "4"}})
        assert applied["ok"]
    finally:
        await backend.close()
    reopened = Backend(lambda _: None)
    try:
        state = await reopened.handle("initialize", parameters)
        assert state["values"]["SMART_SEARCH_INTENT_ROUTER"] == "local"
        assert state["values"]["SMART_SEARCH_JEV_MAX_ROUNDS"] == "4"
        assert state["secret_presence"]["TYPESAFE_API_KEY"]
        assert json.loads(config.config_file.read_text(encoding="utf-8")) == {
            **saved, "SMART_SEARCH_INTENT_ROUTER": "local", "SMART_SEARCH_JEV_MAX_ROUNDS": "4"}
    finally:
        await reopened.close()


def test_state_values_and_revision_are_one_snapshot_even_when_file_changes(monkeypatch):
    config.set_config_value("OPENAI_COMPATIBLE_MODEL", "old-model")
    before = config.revision()
    original = config.get_config_info
    def concurrent_write():
        config.set_config_value("OPENAI_COMPATIBLE_MODEL", "other-process-model")
        return original()
    monkeypatch.setattr(config, "get_config_info", concurrent_write)
    state = ui_api.state()
    assert state["values"]["OPENAI_COMPATIBLE_MODEL"] == "old-model"
    assert state["saved_values"]["OPENAI_COMPATIBLE_MODEL"] == "old-model"
    assert state["revision"] == before
    result = config.update_config_values({"OPENAI_COMPATIBLE_MODEL": "draft"}, expected_revision=state["revision"])
    assert result["conflict"] and not result["ok"]


def test_apply_inside_snapshot_returns_the_new_saved_value():
    config.set_config_value("OPENAI_COMPATIBLE_MODEL", "old-model")
    with config.snapshot():
        result = ui_api.apply_config({"set": {"OPENAI_COMPATIBLE_MODEL": "new-model"}, "revision": config.snapshot_revision()})
        assert result["saved"]["OPENAI_COMPATIBLE_MODEL"] == "new-model"
        assert result["status"]["values"]["OPENAI_COMPATIBLE_MODEL"] == "new-model"


def test_preview_matches_environment_and_disabled_provider(monkeypatch):
    monkeypatch.setenv("SMART_SEARCH_MINIMUM_PROFILE", "standard")
    monkeypatch.setenv("XAI_API_KEY", "synthetic-primary")
    monkeypatch.setenv("EXA_API_KEY", "synthetic-docs")
    config.set_config_value("TAVILY_API_KEY", "synthetic-fetch")
    state = ui_api.state()
    assert state["values"]["XAI_API_KEY"] and "synthetic-primary" not in json.dumps(state)
    assert ui_api.preview({"values": {}})["minimum_profile_ok"]
    preview = ui_api.preview({"values": {"TAVILY_ENABLED": "false"}})
    assert preview["missing"] == [] and preview["capability_status"]["web_fetch"]["configured"] == []
    disabled = ui_api.preview({"values": {"SMART_SEARCH_RESEARCH_DISABLED_PROVIDERS": "xai-responses,exa,tavily"}})
    assert disabled["missing"] == ["retrieval"] and not disabled["minimum_profile_ok"]
    config.set_config_value("TAVILY_ENABLED", "false")
    assert preview["capability_status"] == service.get_capability_status()
    with use_language("en"), pytest.raises(ValueError, match="Invalid XAI_TOOLS"):
        config.set_config_value("XAI_TOOLS", "web_search,bogus")


@pytest.mark.asyncio
async def test_snapshots_isolate_concurrent_drafts_and_redact_echo(monkeypatch):
    config.set_config_value("EXA_API_KEY", "saved-secret-value")
    seen = []
    async def probe():
        await asyncio.sleep(0)
        seen.append(config.exa_api_key)
        return {"status": "ok", "message": "fine"}
    monkeypatch.setitem(service._LIVE_PROBES, "exa", probe)
    results = await asyncio.gather(*[
        service.test_provider_connection("exa", overrides={"EXA_API_KEY": value})
        for value in ("candidate-first", "candidate-second")
    ])
    assert set(seen) == {"candidate-first", "candidate-second"}
    assert all(not result["recorded_as"] for result in results)
    assert config.exa_api_key == "saved-secret-value"
    original_client = httpx.AsyncClient
    secret = "candidate-echo-sensitive"
    transport = httpx.MockTransport(lambda request: httpx.Response(401, text="Rejected credential " + secret))
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: original_client(transport=transport, **kwargs))
    # Restore the actual probe for the error-path check.
    monkeypatch.setitem(service._LIVE_PROBES, "exa", service._test_exa_connection)
    result = await service.test_provider_connection("exa", overrides={"EXA_API_KEY": secret})
    assert secret not in json.dumps(result)
    assert "[REDACTED]" in result["message"]


@pytest.mark.asyncio
async def test_direct_provider_parse_errors_are_redacted(monkeypatch):
    secret = "synthetic-direct-parse-secret"
    config.set_config_value("EXA_API_KEY", secret)
    async def invalid_json(*args, **kwargs):
        return "unlabelled rejection " + secret
    monkeypatch.setattr(service.ExaSearchProvider, "find_similar", invalid_json)
    with activity.observe("exa-similar"):
        result = await service.exa_find_similar("https://example.com")
    assert result["error_type"] == "parse_error" and secret not in json.dumps(result)
    result = await service._decode_provider_json("unlabelled rejection " + secret)
    assert secret not in json.dumps(result)


def test_independent_processes_merge_config_and_health(tmp_path):
    code = """
import sys,time
from pathlib import Path
from smart_search.config import config
from smart_search.provider_health import provider_health
root=Path(sys.argv[1]); key=sys.argv[2]; provider=sys.argv[3]
(root / (provider+'.ready')).touch()
while not (root / 'go').exists(): time.sleep(.01)
original=config._load_config_file
def slow_read(**kwargs):
    data=original(**kwargs); time.sleep(.15); return data
config._load_config_file=slow_read
config.set_config_value(key,provider)
provider_health.record_failure(provider, 'fingerprint', 'auth_error', 'denied')
"""
    env = dict(os.environ, SMART_SEARCH_CONFIG_DIR=str(tmp_path))
    children = [subprocess.Popen([sys.executable, "-c", code, str(tmp_path), key, provider], env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                for key, provider in [("EXA_API_KEY", "exa"), ("TAVILY_API_KEY", "tavily")]]
    deadline = time.monotonic() + 10
    while not all((tmp_path / (p + ".ready")).exists() for p in ("exa", "tavily")):
        assert time.monotonic() < deadline
        time.sleep(.01)
    (tmp_path / "go").touch()
    outputs = [child.communicate(timeout=10) for child in children]
    assert all(child.returncode == 0 for child in children), outputs
    values = json.loads((tmp_path / "config.json").read_text())
    assert values == {"EXA_API_KEY": "exa", "TAVILY_API_KEY": "tavily"}
    health = json.loads((tmp_path / "provider_health.json").read_text())
    assert set(health["providers"]) == {"exa", "tavily"}


@pytest.mark.skipif(os.name != "nt", reason="Windows byte-range locks prevent writes before locking")
def test_empty_lock_waits_before_initializing(tmp_path):
    import msvcrt

    path = tmp_path / "state.json"
    marker = tmp_path / "contended"
    code = """
import msvcrt, sys
from pathlib import Path
from smart_search.state_files import file_lock
path = Path(sys.argv[1])
original = msvcrt.locking
def observed_lock(*args):
    try:
        return original(*args)
    except OSError:
        path.with_name('contended').touch()
        raise
msvcrt.locking = observed_lock
with file_lock(path):
    path.write_text('acquired')
"""
    with path.with_suffix(".json.lock").open("w+b", buffering=0) as stream:
        # Windows can lock beyond EOF; both contenders must lock before writing byte 0.
        msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        child = subprocess.Popen([sys.executable, "-c", code, str(path)],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 10
            while not marker.exists() and child.poll() is None and time.monotonic() < deadline:
                time.sleep(.01)
            ran_while_locked = path.exists()
        finally:
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
        output = child.communicate(timeout=10)
    assert marker.exists() and child.returncode == 0, output
    assert not ran_while_locked
    assert path.read_text() == "acquired"
