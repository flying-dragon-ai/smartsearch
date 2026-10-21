"""CLI-owned Skill maintenance, native protocol, and file safety in isolated homes."""
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest

from smart_search import cli, desktop_skills as update, skill_installer as skills, skill_maintenance as maintenance
from smart_search.desktop_backend import Backend
from smart_search.desktop_environment import Environment


@pytest.fixture(autouse=True)
def receipts_in_temp(monkeypatch, tmp_path):
    monkeypatch.setattr(maintenance, "state_directory", lambda home=None: tmp_path / "receipts")


def isolated(tmp_path, monkeypatch):
    environment = Environment(lambda *_: None, directory=tmp_path / "tools", home=tmp_path / "home")
    manager = update.Skills(lambda *_: None, environment, directory=tmp_path / "cache")
    info = {"external_version": "0.0.1"}
    manager.snapshot({}, info, str(tmp_path / "config"))
    return manager, info


async def sync(manager, targets):
    manager.sync({"targets": targets, "confirm": True, "plan_id": manager.state["plan_id"]})
    await manager.task
    assert manager.state["result"]["ok"]


def test_catalog_is_readonly_local_and_uses_custom_claude_root(tmp_path, monkeypatch):
    manager, info = isolated(tmp_path, monkeypatch)
    state = manager.snapshot({"CLAUDE_CONFIG_DIR": str(tmp_path / "custom")}, info, str(tmp_path))
    rows = {row["target"]: row for row in state["targets"]}
    assert set(rows) == set(skills.SKILL_TARGET_BY_ID)
    assert rows["claude"]["path"] == str(tmp_path / "custom/skills/smart-search-cli")
    assert state["source"] == {"version": cli._get_version(), "managed_by": "cli"}
    assert set(manager.files) == {"SKILL.md"} and b"agent-guide" in manager.files["SKILL.md"]
    assert len(manager.files["SKILL.md"]) < len(dict(skills._load_skill_files())["SKILL.md"])
    manager.check()
    assert not list(tmp_path.iterdir()), "Reading the current CLI needs neither a remote package nor filesystem writes"


def test_manual_standalone_skill_uses_selected_executable_without_path(tmp_path, monkeypatch):
    import sys
    from smart_search import desktop_cli
    from smart_search.config import config

    executable = tmp_path / "手动 CLI & space" / ("smart-search.exe" if os.name == "nt" else "smart-search")
    monkeypatch.delenv("SMART_SEARCH_PACKAGE_ROOT", raising=False)
    monkeypatch.delenv("SMART_SEARCH_NODE_PATH", raising=False)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(executable))
    monkeypatch.setattr(desktop_cli, "tools_directory", lambda: tmp_path / "tools")
    with config.snapshot(directory=str(tmp_path / "config")):
        document = dict(skills._local_skill_files(None))["SKILL.md"]
    body, note = skills.split_local_note(document)
    assert b"smart-search agent-guide" in body
    assert str(executable).encode() in note
    assert str(tmp_path / "config").encode() in note
    assert b"Replace the `smart-search` command" in note and b"--version" in note
    assert not list(tmp_path.iterdir()), "Generating invocation guidance must not install a shim or Skill"


@pytest.mark.asyncio
async def test_sync_is_explicit_scoped_backed_up_and_registered(tmp_path, monkeypatch):
    manager, _ = isolated(tmp_path, monkeypatch)
    target = skills.target_path("codex", manager.environment.home, {})
    target.mkdir(parents=True)
    (target / "SKILL.md").write_bytes(b"personal instructions")
    (target / "extra.md").write_bytes(b"keep")
    plan = manager.state["plan_id"]
    with pytest.raises(ValueError):
        manager.sync({"targets": ["codex"], "plan_id": plan})
    with pytest.raises(ValueError):
        manager.sync({"targets": ["codex"], "confirm": True, "plan_id": plan})
    await sync(manager, ["codex"])
    receipt = manager.state["result"]["installed"][0]
    assert (Path(receipt["backup"]) / "SKILL.md").read_bytes() == b"personal instructions"
    assert b"agent-guide" in (target / "SKILL.md").read_bytes()
    assert (target / "extra.md").read_bytes() == b"keep"
    assert not skills.target_path("claude", manager.environment.home, {}).exists()
    assert set(maintenance.load(manager.directory)["managed"]) == {"codex"}
    before = (target / "SKILL.md").stat().st_mtime_ns
    await sync(manager, ["codex"])
    assert (target / "SKILL.md").stat().st_mtime_ns == before


@pytest.mark.asyncio
async def test_cli_upgrade_maintains_only_opted_in_unmodified_targets(tmp_path, monkeypatch):
    manager, _ = isolated(tmp_path, monkeypatch)
    await sync(manager, ["codex", "claude"])
    codex = skills.target_path("codex", manager.environment.home, {}) / "SKILL.md"
    claude = skills.target_path("claude", manager.environment.home, {}) / "SKILL.md"
    original = codex.read_bytes()
    claude.write_bytes(b"my edited instructions")
    monkeypatch.setattr(skills, "_local_skill_files", lambda _: [("SKILL.md", b"new bootstrap")])
    monkeypatch.setattr(cli, "_get_version", lambda: "4.5.6")
    state = maintenance.maintain(directory=manager.directory)
    assert codex.read_bytes() == b"new bootstrap" and claude.read_bytes() == b"my edited instructions"
    assert {row["target"]: row["status"] for row in state["maintenance"]} == {"codex": "updated", "claude": "personal_changes"}
    backup = next(row["backup"] for row in state["maintenance"] if row["target"] == "codex")
    assert (Path(backup) / "SKILL.md").read_bytes() == original
    monkeypatch.setattr(skills, "_local_skill_files", lambda _: pytest.fail("Repeated same-version check should be throttled"))
    maintenance.maintain(directory=manager.directory)
    assert not skills.target_path("roo", manager.environment.home, {}).exists()


@pytest.mark.asyncio
async def test_cli_upgrade_maintains_receipts_from_older_mise_version(tmp_path, monkeypatch):
    manager, _ = isolated(tmp_path, monkeypatch)
    await sync(manager, ["codex"])
    tool = tmp_path / "mise/installs/npm-konbakuyomu-smart-search"
    with maintenance.file_lock(manager.directory / "state.json"):
        state = maintenance.load(manager.directory)
        state["managed"]["codex"]["owner"] = str(tool / "1.0.0/node_modules/@konbakuyomu/smart-search")
        maintenance.save(state, manager.directory)
    monkeypatch.setenv("SMART_SEARCH_PACKAGE_ROOT", str(tool / "1.0.1/node_modules/@konbakuyomu/smart-search"))
    monkeypatch.setattr(skills, "_local_skill_files", lambda _: [("SKILL.md", b"new bootstrap")])
    monkeypatch.setattr(cli, "_get_version", lambda: "1.0.1")
    state = maintenance.maintain(directory=manager.directory, force=True)
    codex = skills.target_path("codex", manager.environment.home, {}) / "SKILL.md"
    assert codex.read_bytes() == b"new bootstrap"
    assert {row["target"]: row["status"] for row in state["maintenance"]}["codex"] == "updated"
    assert maintenance.load(manager.directory)["managed"]["codex"]["cli_version"] == "1.0.1"


@pytest.mark.asyncio
async def test_older_cli_does_not_overwrite_newer_skill_files(tmp_path, monkeypatch):
    manager, _ = isolated(tmp_path, monkeypatch)
    await sync(manager, ["codex"])
    monkeypatch.setattr(skills, "_local_skill_files", lambda _: [("SKILL.md", b"new bootstrap")])
    monkeypatch.setattr(cli, "_get_version", lambda: "1.0.1")
    maintenance.maintain(directory=manager.directory, force=True)
    monkeypatch.setattr(cli, "_get_version", lambda: "1.0.0")
    monkeypatch.setattr(skills, "_local_skill_files", lambda _: [("SKILL.md", b"old bootstrap")])
    maintenance.maintain(directory=manager.directory, force=True)
    codex = skills.target_path("codex", manager.environment.home, {}) / "SKILL.md"
    assert codex.read_bytes() == b"new bootstrap"


def test_mise_versions_share_one_skill_owner(tmp_path, monkeypatch):
    tool = tmp_path / "mise/installs/npm-konbakuyomu-smart-search"
    monkeypatch.setenv("SMART_SEARCH_PACKAGE_ROOT", str(tool / "1.0.0/node_modules/@konbakuyomu/smart-search"))
    assert maintenance.cli_owner() == str(tool.resolve())
    monkeypatch.setenv("SMART_SEARCH_PACKAGE_ROOT", str(tool / "1.0.1/node_modules/.mise/@konbakuyomu+smart-search@1.0.1/node_modules/@konbakuyomu/smart-search"))
    assert maintenance.cli_owner() == str(tool.resolve())
    package = tmp_path / "npm/lib/node_modules/@konbakuyomu/smart-search"
    monkeypatch.setenv("SMART_SEARCH_PACKAGE_ROOT", str(package))
    assert maintenance.cli_owner() == str(package.resolve())


@pytest.mark.asyncio
async def test_disabling_maintenance_survives_cli_upgrade(tmp_path, monkeypatch):
    manager, _ = isolated(tmp_path, monkeypatch)
    await sync(manager, ["codex"])
    manager.state["auto_check"] = False
    manager.save()
    monkeypatch.setattr(cli, "_get_version", lambda: "9.9.9")
    monkeypatch.setattr(skills, "_local_skill_files", lambda _: pytest.fail("Opted out targets must not be written"))
    assert maintenance.maintain(directory=manager.directory)["auto_check"] is False


@pytest.mark.asyncio
async def test_remove_keeps_backup_and_stops_future_maintenance(tmp_path, monkeypatch):
    manager, _ = isolated(tmp_path, monkeypatch)
    await sync(manager, ["codex", "claude"])
    original = (skills.target_path("codex", manager.environment.home, {}) / "SKILL.md").read_bytes()
    with pytest.raises(ValueError):
        manager.remove({"targets": ["codex"]})
    with pytest.raises(ValueError):
        manager.remove({"targets": [{}], "confirm": True})
    manager.remove({"targets": ["codex"], "confirm": True})
    row = manager.state["result"]["removed"][0]
    assert not Path(row["path"]).exists()
    assert (Path(row["backup"]) / "SKILL.md").read_bytes() == original
    maintenance.maintain(directory=manager.directory, force=True)
    assert not Path(row["path"]).exists()
    assert skills.target_path("claude", manager.environment.home, {}).exists()


@pytest.mark.parametrize("receipt", [None, {"path": "/", "files": {"../outside": "x"}}, {"path": "/smart-search-cli", "files": []}])
def test_malformed_receipt_does_not_break_cli(tmp_path, receipt):
    maintenance.save({"managed": {"codex": receipt}}, tmp_path)
    state = maintenance.maintain(directory=tmp_path)
    assert state["maintenance"] == [{"target": "codex", "status": "needs_attention"}]


def test_agent_guide_reads_current_cli_and_rejects_path_escape(tmp_path, capsys):
    assert cli.main(["agent-guide"]) == 0
    assert dict(skills._load_skill_files())["SKILL.md"].decode() in capsys.readouterr().out
    assert cli.main(["agent-guide", "../../config.json"]) == 2
    assert "Usage" in capsys.readouterr().err
    assert cli.main(["--desktop-capabilities"]) == 0
    capability = json.loads(capsys.readouterr().out)
    assert capability["desktop_protocol_version"] == 1 and capability["skills_protocol_version"] == 1


@pytest.mark.asyncio
async def test_native_protocol_reads_same_cli_catalog_and_removes(tmp_path, monkeypatch):
    manager, info = isolated(tmp_path, monkeypatch)
    events = []
    backend = Backend(events.append)
    backend.directory, backend.initialized = str(tmp_path / "config"), True
    backend.skills, backend.environment = manager, manager.environment
    manager.emit = backend.event
    monkeypatch.setattr(backend, "cli_status", lambda: info)
    catalog = await backend.handle("skills.catalog", {})
    await backend.handle("skills.sync", {"targets": ["roo"], "confirm": True, "plan_id": catalog["plan_id"]})
    await manager.task
    refreshed = await backend.handle("skills.catalog", {})
    assert next(row for row in refreshed["targets"] if row["target"] == "roo")["status"] == "up_to_date"
    await backend.handle("skills.remove", {"targets": ["roo"], "confirm": True})
    assert events[-1]["data"]["result"]["ok"]


def test_write_failure_restores_old_files_and_keeps_backup(tmp_path, monkeypatch):
    target = tmp_path / "target"
    target.mkdir()
    (target / "SKILL.md").write_bytes(b"original")
    (target / "b.md").write_bytes(b"original-b")
    replace = Path.replace
    def failing_replace(path, destination):
        if Path(destination).name == "b.md":
            raise PermissionError("fixture denial")
        return replace(path, destination)
    monkeypatch.setattr(Path, "replace", failing_replace)
    with pytest.raises(ValueError):
        skills.write_skill_files(target, {"SKILL.md": b"new", "b.md": b"new-b"}, tmp_path / "backups")
    assert (target / "SKILL.md").read_bytes() == b"original"
    assert (target / "b.md").read_bytes() == b"original-b"
    assert next((tmp_path / "backups").glob("*/SKILL.md")).read_bytes() == b"original"


def test_symlink_target_is_refused_before_writes(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    link = tmp_path / "link"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("OS did not permit a test symlink")
    with pytest.raises(ValueError):
        skills.write_skill_files(link / "skill", {"SKILL.md": b"bad"}, tmp_path / "backups")
    assert not list(outside.iterdir())


def test_link_guard_without_os_symlink_privileges(tmp_path, monkeypatch):
    parent = tmp_path / "redirected-parent"
    monkeypatch.setattr(Path, "is_symlink", lambda path: path == parent)
    with pytest.raises(ValueError):
        skills.write_skill_files(parent / "skill", {"SKILL.md": b"bad"}, tmp_path / "backups")
    assert not list(tmp_path.iterdir())


@pytest.mark.skipif(os.name != "nt", reason="Windows reparse point contract")
def test_real_junction_is_rejected_without_python312_pathlib(tmp_path, monkeypatch):
    shell = shutil.which("pwsh") or shutil.which("powershell")
    assert shell, "Windows junction test requires the system PowerShell"
    outside, junction = tmp_path / "outside", tmp_path / "junction"
    outside.mkdir()
    result = subprocess.run([shell, "-NoProfile", "-Command",
        "New-Item -ItemType Junction -Path $env:SMART_SEARCH_TEST_JUNCTION -Target $env:SMART_SEARCH_TEST_OUTSIDE | Out-Null"],
        env=dict(os.environ, SMART_SEARCH_TEST_JUNCTION=str(junction), SMART_SEARCH_TEST_OUTSIDE=str(outside)),
        capture_output=True, text=True, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW)
    assert result.returncode == 0, result.stderr
    monkeypatch.delattr(Path, "is_junction", raising=False)
    with pytest.raises(ValueError):
        skills.write_skill_files(junction / "skill", {"SKILL.md": b"must not escape"}, tmp_path / "backups")
    assert not list(outside.iterdir())


def test_invalid_claude_root_is_one_target_error_not_a_broken_catalog(tmp_path, monkeypatch):
    manager, info = isolated(tmp_path, monkeypatch)
    state = manager.snapshot({"CLAUDE_CONFIG_DIR": "relative"}, info, str(tmp_path))
    rows = {row["target"]: row for row in state["targets"]}
    assert rows["claude"]["status"] == "error" and rows["codex"]["status"] == "missing"


@pytest.mark.asyncio
async def test_backend_serializes_skill_and_runtime_mutations(tmp_path, monkeypatch):
    backend = Backend(lambda *_: None)
    backend.directory, backend.initialized = str(tmp_path), True
    backend.skills.state["busy"] = True
    for method in ("profile.select", "cli.update", "cli.enable", "environment.install", "skills.install", "app.update-prepare", "shutdown", "language.set"):
        with pytest.raises(ValueError):
            await backend.handle(method, {"lang": "en"})
    backend.skills.state["busy"] = False
    backend.environment.state["busy"] = True
    with pytest.raises(ValueError):
        await backend.handle("skills.sync", {})


@pytest.mark.asyncio
async def test_maintenance_keeps_original_cli_and_config_binding(tmp_path, monkeypatch):
    from smart_search.config import config
    owner = ["cli-one"]
    monkeypatch.setattr(maintenance, "cli_owner", lambda: owner[0])
    manager, _ = isolated(tmp_path, monkeypatch)
    selected_config = tmp_path / "chosen-config"
    with config.snapshot(directory=str(selected_config)):
        await sync(manager, ["codex"])
    target = skills.target_path("codex", manager.environment.home, {}) / "SKILL.md"
    original = target.read_bytes()
    owner[0] = "cli-two"
    maintenance.maintain(directory=manager.directory, force=True)
    assert target.read_bytes() == original
    owner[0] = "cli-one"
    monkeypatch.setattr(skills, "_local_skill_files", lambda _: [("SKILL.md", str(config.config_file.parent).encode())])
    maintenance.maintain(directory=manager.directory, force=True)
    assert target.read_bytes() == str(selected_config).encode()
