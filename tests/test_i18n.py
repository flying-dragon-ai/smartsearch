"""Language boundaries: local copy changes, user/provider content and behavior do not."""
import ast
import json
from pathlib import Path
import re

import pytest

from smart_search import cli, i18n, service
from smart_search.config import config
from smart_search.desktop_backend import Backend
from smart_search.desktop_environment import Environment
from smart_search.provider_errors import sanitize_provider_error_message

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def isolated_language(monkeypatch, tmp_path):
    monkeypatch.setenv("SMART_SEARCH_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv("LC_ALL", "en_US.UTF-8")


@pytest.mark.parametrize("value,expected", [("auto", "auto"), ("zh-CN", "zh"), ("zh_TW", "zh"), ("en-US", "en")])
def test_locale_normalization(value, expected):
    assert i18n.normalize(value) == expected


@pytest.mark.parametrize("value", ["", " ", "fr", "invalid", None])
def test_invalid_explicit_language_is_rejected(value):
    with pytest.raises(ValueError):
        i18n.normalize(value)


@pytest.mark.parametrize("locale,expected", [("zh_CN.UTF-8", "zh"), ("zh_TW", "zh"), ("en_GB", "en"), ("de_DE", "en"), ("C", "en")])
def test_automatic_language_uses_cli_locale(monkeypatch, locale, expected):
    monkeypatch.setenv("LC_ALL", locale)
    assert i18n.resolve("auto") == expected


def test_preference_precedence_and_one_call_does_not_write(monkeypatch, tmp_path, capsys):
    config._save_config_file({"SMART_SEARCH_LANGUAGE": "zh", "EXA_API_KEY": "test-secret"})
    before = config.config_file.read_bytes()
    assert cli._command_language([])[1] == "zh"
    monkeypatch.setenv("SMART_SEARCH_LANGUAGE", "en")
    assert cli._command_language([])[1] == "en"
    assert cli._command_language(["config", "path", "--lang=zh-CN"])[0:2] == (["config", "path"], "zh")
    with pytest.raises(SystemExit) as result:
        cli.main(["--lang", "zh", "--help"])
    assert result.value.code == 0
    assert "用法" in capsys.readouterr().out
    assert config.config_file.read_bytes() == before
    assert cli._command_language(["--lang=en", "--", "--lang=zh"])[0:2] == (["--", "--lang=zh"], "en")


def test_save_language_preserves_keys_and_reloads(capsys):
    config._save_config_file({"EXA_API_KEY": "test-secret"})
    assert cli.main(["config", "set", "SMART_SEARCH_LANGUAGE", "zh"]) == 0
    capsys.readouterr()
    assert cli._command_language([])[1] == "zh"
    assert json.loads(config.config_file.read_text()) == {"EXA_API_KEY": "test-secret", "SMART_SEARCH_LANGUAGE": "zh"}
    with pytest.raises(ValueError):
        config.set_config_value("SMART_SEARCH_LANGUAGE", "")


@pytest.mark.parametrize("saved", ["{", "[]", '{"SMART_SEARCH_LANGUAGE":"fr"}'])
def test_broken_preferences_warn_and_fall_back(tmp_path, saved):
    (tmp_path / "config.json").write_text(saved)
    arguments, language, warning = cli._command_language(["--help"])
    assert arguments == ["--help"] and language == "en" and warning
    assert (tmp_path / "config.json").read_text() == saved


@pytest.mark.parametrize("language,label", [("zh", "用法"), ("en", "usage")])
@pytest.mark.parametrize("arguments", [["--help"], ["config", "list", "--help"], ["skills", "status", "--help"]])
def test_help_is_localized_at_all_parser_levels(language, label, arguments, capsys):
    for args in (["--lang", language, *arguments], [*arguments, "--lang", language]):
        with pytest.raises(SystemExit) as result:
            cli.main(args)
        assert result.value.code == 0
        assert label in capsys.readouterr().out


@pytest.mark.parametrize("language,label", [("zh", "错误"), ("en", "error")])
def test_parameter_error_preserves_user_argument(language, label, capsys):
    with pytest.raises(SystemExit) as result:
        cli.main(["route", "query", "--bad-user-option", "--lang", language])
    assert result.value.code == 2
    captured = capsys.readouterr()
    assert not captured.out
    assert label in captured.err and "--bad-user-option" in captured.err
    assert cli.main(["--lang="]) == 2


def test_only_explicitly_owned_messages_are_translated():
    raw = "Task cancelled."
    original = {"error": raw, "message": raw, "content": raw, "query": raw,
                "sources": [{"title": raw, "description": raw}], "status": "failed", "provider": "xai-responses"}
    assert i18n.render_messages(original, "zh") == original
    with i18n.use_language("zh"):
        owned = i18n.source_message("Task cancelled.")
        assert str(owned) == raw  # Internal comparisons and classification keep their original input.
        assert i18n.render_messages({"error": owned})["error"] == "任务已取消。"
        assert sanitize_provider_error_message(raw) == raw
        assert sanitize_provider_error_message(owned) == "任务已取消。"
        assert i18n.render_messages(i18n.source_message("HTTP {0}: {1}", 400, raw)) == "HTTP 400: " + raw
    assert i18n.render_messages(i18n.render_messages(original, "zh"), "en") == original


@pytest.mark.asyncio
async def test_local_provider_errors_translate_but_machine_contract_does_not():
    outputs = []
    for language in ("zh", "en"):
        with i18n.use_language(language):
            outputs.append(i18n.render_messages(await service.exa_search("用户 query")))
    assert outputs[0]["error"] != outputs[1]["error"]
    assert outputs[0]["error_type"] == outputs[1]["error_type"] == "config_error"
    assert "EXA_API_KEY" in outputs[0]["error"] and "EXA_API_KEY" in outputs[1]["error"]


@pytest.mark.asyncio
async def test_backend_switch_retains_work_and_rerenders_async_status(monkeypatch, tmp_path):
    emitted = []
    backend = Backend(emitted.append)
    backend.initialized = True
    backend.directory = str(tmp_path)
    run = {"status": "running", "query": "Task cancelled."}
    backend.runs["synthetic"] = run
    with i18n.use_language("zh"):
        message = i18n.tr("正在检测本机运行环境…")
    monkeypatch.setattr(backend, "state", lambda: {"language": backend.language, "runs": backend.runs, "message": message})
    before = dict(config.get_saved_config())
    result = await backend.handle("language.set", {"lang": "en"})
    assert result["language"] == "en" and backend.runs["synthetic"] is run
    assert result["runs"]["synthetic"] == run
    backend.event("environment", {"message": message})
    assert emitted[-1]["data"]["message"] == i18n.translate(message.source, "en")
    assert config.get_saved_config() == before
    backend.environment.state["busy"] = True
    with pytest.raises(ValueError):
        await backend.handle("language.set", {"lang": "zh"})
    assert backend.language == "en"


def test_integration_files_do_not_depend_on_app_language(tmp_path):
    environment = Environment(lambda *_: None, directory=tmp_path / "tools", home=tmp_path / "home")
    values = []
    for language in ("zh", "en"):
        with i18n.use_language(language):
            values.append(environment.skill_files({"ready": True, "path": str(tmp_path / "node")}, {"package_root": str(tmp_path / "npm")}, str(tmp_path / "配置")))
    assert values[0] == values[1]


def test_catalog_coverage_placeholders_and_packaged_resource_parity():
    catalog = i18n.catalog()
    for key, pair in catalog.items():
        assert len(pair) == 2 and all(isinstance(text, str) for text in pair), key
        slots = [set(re.findall(r"\{(\d+)(?:![rsa])?(?::[^{}]+)?\}", text)) for text in pair]
        assert slots[0] == slots[1], key
    for path in (ROOT / "src/smart_search").rglob("*.py"):
        if "assets" in path.parts:
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"tr", "source_message"} and node.args:
                source = node.args[0]
                if isinstance(source, ast.Constant) and isinstance(source.value, str) and source.value.strip():
                    assert source.value in catalog, (path.name, source.lineno, source.value)
    assert (ROOT / "src/smart_search/assets/i18n/messages.json").read_bytes() == (ROOT / "desktop/macos/Sources/SmartSearchDesktop/Localization.json").read_bytes()
