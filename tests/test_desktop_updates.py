"""Independent CLI checks and the native App update handoff."""
import asyncio
import json
import time

import httpx
import pytest

from smart_search.i18n import use_language


@pytest.fixture(autouse=True)
def chinese_presentation():
    with use_language("zh"):
        yield

from smart_search import desktop_updates as updates
from smart_search.desktop_backend import Backend
from smart_search import desktop_backend


@pytest.mark.parametrize("remote,current,expected", [("v1.2.3", "1.2.2", True), ("1.2.3", "1.2.3", False),
    ("1.2.2", "1.2.3", False), ("1.3.0-rc.1", "1.2.3", False), ("1.3.0", "dev", False), ("1.2.3", "1.2.3+build", False)])
def test_versions(remote, current, expected):
    assert updates.newer(remote, current) is expected


@pytest.mark.parametrize('version,known', [('0.1.23', True), ('development', False)])
def test_cached_release_keeps_current_app_identity_without_enabling_cached_download(tmp_path, version, known):
    (tmp_path / 'state.json').write_text(json.dumps({'app': {
        'current_version': '0.1.22', 'latest_version': '0.1.23', 'checked_at': 1,
        'version_known': True, 'available': True, 'asset': {'untrusted': 'cached'}}}))
    manager = updates.Updates(lambda *_: None, directory=tmp_path)
    manager.current_version = version
    manager.refresh_installed({})
    app = manager.state['app']
    assert app['current_version'] == version and app['version_known'] is known
    assert not app['available'] and 'asset' not in app
    assert app['managed_by'] == 'native'


@pytest.mark.parametrize('fresh,owned,verified,available', [(True, True, False, True),
    (False, True, False, False), (True, False, False, False), (True, True, True, False)])
def test_latest_cli_can_retry_incomplete_runtime_only_after_fresh_owned_check(tmp_path, fresh, owned, verified, available):
    manager = updates.Updates(lambda *_: None, directory=tmp_path)
    manager.state['cli'] = {'latest_version': '0.1.23', 'checked_at': 1, 'cached': not fresh}
    manager.refresh_installed({'external_version': '0.1.23', 'can_update': owned,
                              'external_runtime_verified': verified, 'manager': 'npm',
                              'manager_command': ['node', 'npm.js'], 'manager_options': []})
    assert manager.state['cli']['available'] is available
    assert manager.state['cli']['runtime_needs_repair'] is (owned and not verified)


@pytest.mark.asyncio
async def test_cli_refresh_recovers_update_controls_from_previous_detection_failure(tmp_path, monkeypatch):
    events = []
    backend = Backend(events.append)
    backend.initialized, backend.directory = True, str(tmp_path / 'config')
    backend.updates = updates.Updates(backend.event, directory=tmp_path / 'updates')
    backend.updates.current_version = '0.1.23'
    backend.updates.state['cli'] = {'latest_version': '0.1.23', 'checked_at': 1, 'error': ''}
    backend.cli_info = {'manager': 'unknown', 'external_version': None, 'can_update': False}
    backend.cli_status()
    assert not backend.updates.state['cli']['available']
    healthy = {'manager': 'mise', 'external_version': '0.1.22', 'can_update': True,
               'external_runtime_verified': True, 'manager_command': ['mise'], 'manager_options': []}
    monkeypatch.setattr(desktop_backend.shutil, 'which', lambda *a, **k: str(tmp_path / 'smart-search.exe'))
    monkeypatch.setattr(desktop_backend, 'managed_cli_info', lambda *a: None)
    monkeypatch.setattr(desktop_backend, 'discover', lambda *a: dict(healthy))
    await backend.handle('cli.status', {})
    snapshot = events[-1]['data']
    assert events[-1]['event'] == 'updates'
    assert snapshot['installed_cli']['can_update'] and snapshot['installed_cli']['external_version'] == '0.1.22'
    assert snapshot['cli']['available'] and '@0.1.23' in snapshot['cli']['command']
    healthy['external_version'] = '0.1.23'
    await backend.handle('cli.status', {})
    assert not backend.updates.state['cli']['available']


@pytest.mark.asyncio
async def test_inflight_remote_check_does_not_restore_old_cli_detection(tmp_path, monkeypatch):
    gate = asyncio.Event()
    async def response(request):
        await gate.wait()
        return httpx.Response(200, json={'version': '0.1.23'})
    client = httpx.AsyncClient(transport=httpx.MockTransport(response))
    monkeypatch.setattr(updates.httpx, 'AsyncClient', lambda **_: client)
    manager = updates.Updates(lambda *_: None, directory=tmp_path)
    manager.current_version = '0.1.23'
    manager.check({'external_version': None, 'can_update': False})
    await asyncio.sleep(0)
    manager.refresh_installed({'external_version': '0.1.22', 'can_update': True, 'manager': 'npm',
                               'manager_command': ['node', 'npm-cli.js'], 'manager_options': []})
    gate.set()
    await manager.check_task
    assert manager.state['installed_cli']['external_version'] == '0.1.22'
    assert manager.state['cli']['current_version'] == '0.1.22' and manager.state['cli']['available']


@pytest.mark.asyncio
async def test_cli_checks_never_fetch_app_releases_and_errors_do_not_enable_update(tmp_path, monkeypatch):
    failed = False
    urls = []
    def respond(request):
        urls.append(str(request.url))
        return httpx.Response(429) if failed else httpx.Response(200, json={"version": "0.2.0"})
    real_client = httpx.AsyncClient
    monkeypatch.setattr(updates.httpx, "AsyncClient", lambda **kw: real_client(transport=httpx.MockTransport(respond), **kw))
    manager = updates.Updates(lambda *_: None, directory=tmp_path)
    manager.check({"external_version": "0.1.23"})
    first = manager.check_task
    manager.check({"external_version": "0.1.23"})
    assert manager.check_task is first
    await first
    assert urls == [updates.NPM_URL] and manager.state['cli']['available']
    success = manager.state['last_success']
    failed = True
    manager.check({"external_version": "0.1.23"})
    await manager.check_task
    assert manager.state['last_success'] == success
    assert manager.state['cli']['error'] and not manager.state['cli']['available']
    assert not manager.state['app']['available'] and 'asset' not in manager.state['app']


@pytest.mark.asyncio
async def test_native_update_prepare_locks_backend_without_stopping_active_work(tmp_path):
    backend = Backend(lambda _: None)
    backend.initialized, backend.directory = True, str(tmp_path)
    backend.skills.state['busy'] = True
    with pytest.raises(ValueError, match='Skills'):
        await backend.handle('app.update-prepare', {})
    assert not backend.app_update_pending
    backend.skills.state['busy'] = False
    backend.environment.state['busy'] = True
    with pytest.raises(ValueError, match='环境'):
        await backend.handle('app.update-prepare', {})
    assert not backend.app_update_pending
    backend.environment.state['busy'] = False
    backend.runs['active'] = {'status': 'running'}
    with pytest.raises(ValueError, match='任务'):
        await backend.handle('app.update-prepare', {})
    assert not backend.app_update_pending and backend.runs['active']['status'] == 'running'
    del backend.runs['active']
    backend.updates.state['cli_update']['status'] = 'running'
    with pytest.raises(ValueError, match='CLI'):
        await backend.handle('app.update-prepare', {})
    assert not backend.app_update_pending
    backend.updates.state['cli_update']['status'] = 'idle'
    assert (await backend.handle('app.update-prepare', {}))['ok']
    with pytest.raises(ValueError, match='App'):
        await backend.handle('config.apply', {})
    original_language = backend.language
    with pytest.raises(ValueError, match='App'):
        await backend.handle('language.set', {'lang': 'en' if original_language != 'en' else 'zh'})
    assert backend.language == original_language
    assert (await backend.handle('shutdown', {}))['ok']


@pytest.mark.asyncio
@pytest.mark.parametrize('method', ['updates.download', 'updates.cancel', 'updates.installer', 'app.update-check'])
async def test_removed_app_downloader_cannot_be_invoked(method,tmp_path):
    backend = Backend(lambda _: None)
    backend.initialized, backend.directory = True, str(tmp_path)
    with pytest.raises(ValueError, match='未知协议方法'):
        await backend.handle(method, {})


@pytest.mark.asyncio
async def test_auto_check_setting_and_daily_throttle(tmp_path, monkeypatch):
    manager = updates.Updates(lambda *_: None, directory=tmp_path)
    calls = []
    monkeypatch.setattr(manager, "check", lambda info: calls.append(info))
    manager.auto_check({})
    assert not calls  # protocol-only consumers never opt into automatic networking
    manager.enabled = True
    manager.auto_check({})
    assert len(calls) == 1
    manager.state["last_attempt"] = time.time()
    manager.auto_check({})
    assert len(calls) == 1
    manager.state["auto_check"] = False
    manager.save()
    assert updates.Updates(lambda *_: None, directory=tmp_path).state["auto_check"] is False
