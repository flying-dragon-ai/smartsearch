"""Manager ownership and exact-target updates without touching real installs."""
import json
import os
from pathlib import Path
import sys
import subprocess

import pytest

from smart_search.i18n import use_language


@pytest.fixture(autouse=True)
def chinese_presentation():
    with use_language("zh"):
        yield

from smart_search import desktop_cli
from smart_search.desktop_backend import Backend, manager_environment
from smart_search.desktop_updates import Updates


def test_mise_ownership_options_and_conflicting_path(tmp_path, monkeypatch):
    shim = tmp_path / "mise/shims/smart-search.exe"
    install = tmp_path / "mise/installs/smart-search/0.1.19"
    entry = install / "node_modules/.bin/smart-search"
    root = install / "node_modules/@konbakuyomu/smart-search"
    root.mkdir(parents=True)
    (root / "package.json").write_text(json.dumps({"name": desktop_cli.PACKAGE, "version": "0.1.19"}))
    source = tmp_path / "config.toml"
    source.write_text('[tools]\n"npm:@konbakuyomu/smart-search" = {version="0.1.19", allow_low_downloads="true"}\n')
    monkeypatch.setenv("MISE_GLOBAL_CONFIG_FILE", str(source))
    monkeypatch.delenv("MISE_CONFIG_FILE", raising=False)
    monkeypatch.delenv("MISE_ENV", raising=False)
    monkeypatch.setattr(desktop_cli.shutil, "which", lambda _, **kwargs: "mise.exe")
    monkeypatch.setattr(desktop_cli, "path_entries", lambda *_: [])
    env = {"MISE_GLOBAL_CONFIG_FILE": str(source)}
    def read(argv, env):
        if argv[1] == "which":
            return str(entry)
        return json.dumps([{"active": True, "installed": True, "install_path": str(install), "requested_version": "0.1.19",
                           "source": {"path": str(source), "type": "mise.toml"}}])
    monkeypatch.setattr(desktop_cli, "run_read", read)
    if desktop_cli.tomllib is None:
        assert not desktop_cli.discover(str(shim), env)["can_update"]
        return
    info = desktop_cli.discover(str(shim), env)
    assert info["manager"] == "mise" and info["can_update"]
    argv = desktop_cli.update_command(info, "0.2.0")
    assert argv == ["mise.exe", "use", "--global", "--pin", "--tool-option", 'allow_low_downloads="true"',
                    "npm:@konbakuyomu/smart-search@0.2.0"]
    monkeypatch.setattr(desktop_cli, "path_entries", lambda *_: [tmp_path / "other/smart-search.exe"])
    assert not desktop_cli.discover(str(shim), env)["can_update"]
    monkeypatch.setattr(desktop_cli, "path_entries", lambda *_: [])
    source.write_text('[tools]\n"npm:@konbakuyomu/smart-search" = {version="0.1.19", postinstall="custom command"}\n')
    assert not desktop_cli.discover(str(shim), env)["can_update"]


def test_npm_only_updates_proven_global_root(tmp_path, monkeypatch):
    entry = tmp_path / "prefix/smart-search.cmd"
    root = entry.parent / "node_modules/@konbakuyomu/smart-search"
    root.mkdir(parents=True)
    (root / "package.json").write_text(json.dumps({"name": desktop_cli.PACKAGE, "version": "0.1.19"}))
    monkeypatch.setattr(desktop_cli.shutil, "which", lambda _, **kwargs: None)
    monkeypatch.setattr(desktop_cli, "npm_command", lambda *_: ["node", "npm-cli.js"])
    monkeypatch.setattr(desktop_cli, "run_read", lambda *_: str(entry.parent / "node_modules"))
    monkeypatch.setattr(desktop_cli, "path_entries", lambda *_: [])
    info = desktop_cli.discover(str(entry), {})
    assert info["manager"] == "npm" and info["can_update"]
    assert desktop_cli.update_command(info, "0.2.0") == ["node", "npm-cli.js", "install", "--global", "@konbakuyomu/smart-search@0.2.0"]
    monkeypatch.setattr(desktop_cli, "run_read", lambda *_: str(tmp_path / "different/node_modules"))
    assert not desktop_cli.discover(str(entry), {})["can_update"]
    with pytest.raises(ValueError):
        desktop_cli.update_command(info, "latest; bad-command")


@pytest.mark.parametrize("error,code", [(subprocess.TimeoutExpired('probe', 5), 'timeout'),
                                      (FileNotFoundError('secret detail'), 'launch_failed'),
                                      (ValueError('secret detail'), 'invalid_result')])
def test_manager_probe_failure_is_actionable_and_does_not_leak_output(tmp_path, monkeypatch, error, code):
    shim = tmp_path / 'mise/shims/smart-search.exe'
    observed = []
    monkeypatch.setattr(desktop_cli.shutil, 'which', lambda _, **kwargs: observed.append(kwargs['path']) or 'mise.exe')
    def fail(*_):
        raise error
    monkeypatch.setattr(desktop_cli, 'run_read', fail)
    info = desktop_cli.discover(str(shim), {'PATH': 'explicit-manager-path'})
    assert observed == ['explicit-manager-path'] and not info['can_update']
    assert info['probe_error'] == code and 'CLI' in info['update_note']
    assert 'secret detail' not in json.dumps(info)


def test_mise_shim_without_manager_reports_detection_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(desktop_cli.shutil, 'which', lambda _, **kwargs: None)
    info = desktop_cli.discover(str(tmp_path / 'mise/shims/smart-search.exe'), {'PATH': 'shim-only'})
    assert info['probe_error'] == 'manager_missing' and not info['can_update']


@pytest.mark.asyncio
@pytest.mark.parametrize("actual,exit_code,expected", [("0.2.0", 0, "finished"), ("0.1.19", 0, "failed"), ("0.2.0", 1, "failed")])
async def test_update_executes_exact_manager_and_checks_effective_version(tmp_path, monkeypatch, actual, exit_code, expected):
    b = Backend(lambda *_: None)
    b.directory = str(tmp_path / "config")
    b.updates = Updates(lambda *_: None, directory=tmp_path / "cache")
    manager_script = tmp_path / "manager.py"
    argv_file = tmp_path / "arguments.json"
    manager_script.write_text('import json,sys,os\nfrom pathlib import Path\n'
                              f'Path({str(argv_file)!r}).write_text(json.dumps(sys.argv[1:]))\n'
                              'assert "TYPESAFE_API_KEY" not in os.environ\n'
                              'assert "PYTHONPATH" not in os.environ\n'
                              f'print("package manager completed")\nsys.exit({exit_code})\n')
    info = {"external_path": "same", "resolved_path": "same", "external_version": "0.1.19", "manager": "npm",
            "manager_command": [sys.executable, str(manager_script)], "manager_options": [], "can_update": True, "external_runtime_verified": True}
    calls = []
    def status(**kwargs):
        calls.append(1)
        return {**info, "external_version": actual if len(calls) > 2 else "0.1.19"}
    monkeypatch.setattr(b, "cli_status", status)
    monkeypatch.setattr(b, "activity", lambda: {"runs": []})
    monkeypatch.setenv("TYPESAFE_API_KEY", "synthetic-private-key")
    monkeypatch.setenv("PYTHONPATH", "synthetic-wrong-python")
    b.updates.state["cli"] = {"current_version": "0.1.19", "latest_version": "0.2.0", "available": True}
    b.update_cli({"confirm": True, "version": "0.2.0"})
    first = b.updates.cli_task
    b.update_cli({"confirm": True, "version": "0.2.0"})
    assert b.updates.cli_task is first
    await first
    assert b.updates.state["cli_update"]["status"] == expected
    assert json.loads(argv_file.read_text()) == ["install", "--global", "@konbakuyomu/smart-search@0.2.0"]
    assert "synthetic-private-key" not in (tmp_path / "cache/cli-update.log").read_text()


@pytest.mark.asyncio
@pytest.mark.parametrize('outcome', ['ok', 'pip-fail', 'wrong-owner', 'manager-fail', 'python-missing'])
async def test_explicit_update_prepares_missing_runtime_and_retries_partial_install(tmp_path, monkeypatch, outcome):
    from smart_search import desktop_backend
    b = Backend(lambda *_: None)
    b.directory = str(tmp_path / 'config')
    b.updates = Updates(lambda *_: None, directory=tmp_path / 'cache')
    root = tmp_path / 'package'
    wrapper = root / 'npm/bin/smart-search.js'
    wrapper.parent.mkdir(parents=True)
    wrapper.write_text('')
    (root / 'package.json').write_text(json.dumps({'name': desktop_cli.PACKAGE, 'version': '0.1.23'}))
    installed, ready = tmp_path / 'installed', tmp_path / 'ready'
    manager = tmp_path / 'manager.py'
    manager.write_text(f'from pathlib import Path\nPath({str(installed)!r}).touch()\n'
                       f'print("installed npm package " * 100)\nraise SystemExit({1 if outcome == "manager-fail" else 0})\n')
    setup = tmp_path / 'setup.py'
    fail = tmp_path / 'fail-pip'
    if outcome == 'pip-fail': fail.touch()
    setup.write_text('from pathlib import Path\nimport os,sys,json\n'
                     'assert not {"EXA_API_KEY", "GH_TOKEN", "PYTHONPATH"} & os.environ.keys()\n'
                     'print("runtime stage: " + sys.argv[1])\n'
                     f'with Path({str(tmp_path / "steps")!r}).open("a") as out: out.write(sys.argv[1]+"\\n")\n'
                     'if sys.argv[1] == "pip":\n'
                     f' if Path({str(fail)!r}).exists(): raise SystemExit(2)\n'
                     f' Path({str(ready)!r}).touch()\n')
    info = {'external_path': str(tmp_path / 'shim'), 'resolved_path': str(wrapper), 'package_root': str(root),
            'external_version': '0.1.22', 'manager': 'npm', 'manager_command': [sys.executable, str(manager)],
            'manager_options': [], 'can_update': True, 'external_runtime_verified': True}
    def status(**kwargs):
        current = {**info, 'external_version': '0.1.23' if installed.exists() else '0.1.22',
                   'external_runtime_verified': ready.exists() if installed.exists() else True}
        if installed.exists() and outcome == 'wrong-owner': current.update(manager='unknown', can_update=False)
        b.updates.refresh_installed(current)
        return current
    monkeypatch.setattr(b, 'cli_status', status)
    monkeypatch.setattr(b, 'activity', lambda: {'runs': []})
    monkeypatch.setattr(b.environment, 'probe_python', lambda env: {'ready': outcome != 'python-missing', 'path': sys.executable})
    monkeypatch.setattr(desktop_backend, 'cli_runtime_commands', lambda package, python: (
        [sys.executable, str(setup), 'venv'], [sys.executable, str(setup), 'pip']))
    monkeypatch.setenv('EXA_API_KEY', 'synthetic-private-key')
    monkeypatch.setenv('GH_TOKEN', 'synthetic-private-token')
    b.updates.state['cli'] = {'current_version': '0.1.22', 'latest_version': '0.1.23', 'checked_at': 1, 'available': True}
    b.update_cli({'confirm': True, 'version': '0.1.23'})
    await b.updates.cli_task
    assert b.updates.state['cli_update']['status'] == ('finished' if outcome == 'ok' else 'failed')
    assert ready.exists() is (outcome == 'ok')
    assert (tmp_path / 'steps').exists() is (outcome in {'ok', 'pip-fail'})
    if outcome == 'pip-fail':
        assert b.updates.state['cli']['available'], 'same-version incomplete runtime must be retryable'
        assert 'Python' in b.updates.state['cli_update']['error']
        fail.unlink()
        b.update_cli({'confirm': True, 'version': '0.1.23'})
        await b.updates.cli_task
        assert b.updates.state['cli_update']['status'] == 'finished' and ready.exists()
    assert 'installed npm package' in b.updates.state['cli_update']['log']
    if outcome in {'ok', 'pip-fail'}:
        assert 'runtime stage: pip' in b.updates.state['cli_update']['log'], 'keep later stages beyond the first 300 characters'


@pytest.mark.skipif(os.name != 'nt', reason='Windows inherited synchronous pipe handles')
def test_runtime_probe_while_protocol_input_is_blocked(tmp_path):
    # A backend reader is already waiting for the next RPC during async updates.
    # Inheriting that pipe can stall Python startup on Windows before CLI code runs.
    script = r"""
import json,os,sys,threading,time
from pathlib import Path
from smart_search import desktop_backend as module
root=Path(sys.argv[1])/'package'
python=root/'.smart-search-python/Scripts/python.exe'
python.parent.mkdir(parents=True);python.touch()
module.shutil.which=lambda *a,**k: str(root/'entry')
module.managed_cli_info=lambda *a: None
module.discover=lambda *a: {'package_root':str(root),'external_version':'0.1.23'}
real_run=module.subprocess.run
def probe(argv,**options):
    output='smart-search 0.1.23' if argv[-1]=='--version' else '{"activity_protocol_version":1}'
    return real_run([sys.executable,'-c','print('+repr(output)+')'],**options)
module.subprocess.run=probe
threading.Thread(target=sys.stdin.buffer.readline,daemon=True).start()
time.sleep(.2)
state=module.Backend(lambda *_:None).cli_status()
print(json.dumps({'ready':state['external_runtime_verified'],'error':state.get('runtime_probe_error')}),flush=True)
os._exit(0 if state['external_runtime_verified'] else 1)
"""
    process = subprocess.Popen([sys.executable, '-c', script, str(tmp_path)], stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
    try:
        process.wait(timeout=15)  # Keep stdin open: communicate() would hide the bug by closing it.
        assert process.returncode == 0, process.stdout.read() + process.stderr.read()
        assert json.loads(process.stdout.read())['ready']
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        process.stdin.close()
        process.stdout.close()
        process.stderr.close()


def test_cli_update_requires_explicit_target_and_preserves_running_tasks(tmp_path, monkeypatch):
    b = Backend(lambda *_: None)
    b.updates = Updates(lambda *_: None, directory=tmp_path)
    info = {"external_version": "0.1.19", "manager": "unknown", "can_update": False}
    monkeypatch.setattr(b, "cli_status", lambda: info)
    monkeypatch.setattr(b, "activity", lambda: {"runs": []})
    with pytest.raises(ValueError, match="明确"):
        b.update_cli({})
    b.updates.state["cli"] = {"current_version": "0.1.19", "latest_version": "0.2.0", "available": True}
    with pytest.raises(ValueError, match="来源"):
        b.update_cli({"confirm": True, "version": "0.2.0"})
    b.runs["own"] = {"status": "running"}
    with pytest.raises(ValueError, match="任务"):
        b.update_cli({"confirm": True, "version": "0.2.0"})
    assert b.runs["own"]["status"] == "running"
