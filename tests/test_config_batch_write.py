"""Atomic, all-or-nothing config writes (P0 groundwork for the web UI)."""

import json

import pytest

from smart_search.config import Config
from smart_search.i18n import use_language


@pytest.fixture
def cfg(tmp_path, monkeypatch):
    config = Config()
    monkeypatch.setattr(config, "_config_file", tmp_path / "config.json")
    monkeypatch.setattr(config, "_config_dir_source", "override")
    monkeypatch.setattr(config, "_cached_model", None)
    return config


def test_batch_update_writes_once(cfg, monkeypatch):
    calls = []
    original = cfg._save_config_file
    monkeypatch.setattr(cfg, "_save_config_file", lambda data: (calls.append(dict(data)), original(data))[1])

    result = cfg.update_config_values({
        "EXA_API_KEY": "exa-key",
        "CONTEXT7_API_KEY": "c7-key",
        "TAVILY_API_KEY": "tv-key",
        "XAI_API_KEY": "xai-key",
    })

    assert result["ok"] is True
    assert result["saved"] == ["CONTEXT7_API_KEY", "EXA_API_KEY", "TAVILY_API_KEY", "XAI_API_KEY"]
    assert len(calls) == 1, "a batch must not read-modify-write once per key"
    saved = json.loads(cfg.config_file.read_text(encoding="utf-8"))
    assert saved["EXA_API_KEY"] == "exa-key"
    assert saved["XAI_API_KEY"] == "xai-key"


def test_batch_update_rejects_whole_batch_on_one_bad_value(cfg):
    cfg.update_config_values({"EXA_API_KEY": "keep-me"})
    before = cfg.config_file.read_bytes()

    result = cfg.update_config_values({
        "CONTEXT7_API_KEY": "would-be-saved",
        "OPENAI_COMPATIBLE_API_MODE": "not-a-mode",
    })

    assert result["ok"] is False
    assert [item["key"] for item in result["errors"]] == ["OPENAI_COMPATIBLE_API_MODE"]
    assert cfg.config_file.read_bytes() == before, "a rejected batch must not write anything"


def test_batch_update_rejects_unknown_key(cfg):
    result = cfg.update_config_values({"NOT_A_REAL_KEY": "x"})
    assert result["ok"] is False
    assert result["errors"][0]["error"] == "Unsupported config key: NOT_A_REAL_KEY"
    assert not cfg.config_file.exists()


def test_unset_removes_key_in_batch(cfg):
    cfg.update_config_values({"EXA_API_KEY": "exa-key", "CONTEXT7_API_KEY": "c7-key"})
    result = cfg.update_config_values(unset_keys=["EXA_API_KEY"])
    assert result["ok"] is True
    assert result["unset"] == ["EXA_API_KEY"]
    saved = json.loads(cfg.config_file.read_text(encoding="utf-8"))
    assert "EXA_API_KEY" not in saved
    assert saved["CONTEXT7_API_KEY"] == "c7-key"


def test_failed_write_leaves_existing_config_intact(cfg, monkeypatch):
    cfg.update_config_values({"EXA_API_KEY": "original"})
    before = cfg.config_file.read_bytes()

    def boom(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(json, "dump", boom)
    with use_language("zh"), pytest.raises(ValueError, match="无法保存配置文件"):
        cfg.update_config_values({"EXA_API_KEY": "replacement"})

    assert cfg.config_file.read_bytes() == before, "a torn write must not clobber the old config"
    leftovers = list(cfg.config_file.parent.glob("config.json.*.tmp"))
    assert leftovers == [], f"temp files left behind: {leftovers}"


def test_config_file_is_not_world_readable(cfg):
    import sys

    cfg.update_config_values({"EXA_API_KEY": "secret"})
    if sys.platform.startswith("win"):
        pytest.skip("POSIX mode bits only")
    assert cfg.config_file.stat().st_mode & 0o077 == 0


def test_set_config_value_still_raises_the_same_errors(cfg):
    with pytest.raises(ValueError, match="Unsupported config key: NOPE"):
        cfg.set_config_value("NOPE", "x")
    with pytest.raises(ValueError, match="Invalid OPENAI_COMPATIBLE_API_MODE"):
        cfg.set_config_value("OPENAI_COMPATIBLE_API_MODE", "bogus")


@pytest.mark.parametrize(
    "key,value",
    [
        ("SMART_SEARCH_VALIDATION_LEVEL", "bogus"),
        ("SMART_SEARCH_FALLBACK_MODE", "sometimes"),
        ("SMART_SEARCH_MINIMUM_PROFILE", "loose"),
        ("SMART_SEARCH_INTENT_ROUTER", "psychic"),
        ("INTENT_EMBEDDING_THRESHOLD", "1.5"),
        ("INTENT_EMBEDDING_MARGIN", "-0.1"),
        ("EXA_TIMEOUT_SECONDS", "soon"),
        ("SMART_SEARCH_RETRY_MAX_ATTEMPTS", "many"),
    ],
)
def test_invalid_values_are_rejected_at_write_time(cfg, key, value):
    with pytest.raises(ValueError, match=f"Invalid {key}"):
        cfg.set_config_value(key, value)
    assert not cfg.config_file.exists()


@pytest.mark.parametrize(
    "key,value",
    [
        ("SMART_SEARCH_VALIDATION_LEVEL", "strict"),
        ("INTENT_EMBEDDING_THRESHOLD", "0.8"),
        ("EXA_TIMEOUT_SECONDS", "45"),
        ("SMART_SEARCH_RETRY_MAX_ATTEMPTS", "5"),
    ],
)
def test_valid_values_still_save(cfg, key, value):
    cfg.set_config_value(key, value)
    assert json.loads(cfg.config_file.read_text(encoding="utf-8"))[key] == value


def test_empty_value_clears_without_tripping_validation(cfg):
    # Every getter reads an empty value as "unset", so saving one must stay legal.
    cfg.set_config_value("EXA_TIMEOUT_SECONDS", "")
    assert json.loads(cfg.config_file.read_text(encoding="utf-8"))["EXA_TIMEOUT_SECONDS"] == ""
