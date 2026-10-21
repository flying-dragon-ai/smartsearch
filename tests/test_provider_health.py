import json

import pytest

from smart_search.provider_health import ProviderHealthStore, provider_fingerprint


class FakeClock:
    def __init__(self, now: float = 1_000.0):
        self.now = now

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def _store(tmp_path, clock, **kwargs) -> ProviderHealthStore:
    return ProviderHealthStore(
        tmp_path / "provider_health.json",
        cooldown_seconds=kwargs.pop("cooldown_seconds", 900.0),
        failure_threshold=kwargs.pop("failure_threshold", 2),
        clock=clock,
        **kwargs,
    )


def test_soft_failures_open_cooldown_only_at_threshold(tmp_path):
    clock = FakeClock()
    store = _store(tmp_path, clock)

    first = store.record_failure("zhipu", "fp", "timeout", "request timed out")
    assert first["state"] == "closed"
    assert store.should_skip("zhipu", "fp") == (False, first)

    second = store.record_failure("zhipu", "fp", "timeout", "request timed out")
    assert second["state"] == "cooldown"
    assert second["cooldown_remaining_seconds"] == 900.0
    skip, state = store.should_skip("zhipu", "fp")
    assert skip is True
    assert state["error_type"] == "timeout"


def test_hard_failure_opens_cooldown_on_first_occurrence(tmp_path):
    clock = FakeClock()
    store = _store(tmp_path, clock)

    state = store.record_failure("zhipu", "fp", "auth_error", "HTTP 401: invalid api key")

    assert state["state"] == "cooldown"
    assert state["hard_failure"] is True
    # Hard failures wait four cooldown windows: a bad key does not heal itself.
    assert state["cooldown_remaining_seconds"] == 3600.0


def test_soft_failure_is_probeable_but_hard_failure_is_not(tmp_path):
    clock = FakeClock()
    store = _store(tmp_path, clock)

    store.record_failure("tavily", "fp", "network_error", "HTTP 503")
    store.record_failure("tavily", "fp", "network_error", "HTTP 503")
    store.record_failure("zhipu", "fp", "auth_error", "HTTP 401")

    soft_skip, soft_state = store.should_skip("tavily", "fp", allow_probe=True)
    hard_skip, _ = store.should_skip("zhipu", "fp", allow_probe=True)

    assert soft_skip is False
    assert soft_state["probe"] is True
    assert hard_skip is True


def test_cooldown_expires_and_success_clears_the_record(tmp_path):
    clock = FakeClock()
    store = _store(tmp_path, clock)
    store.record_failure("exa", "fp", "auth_error", "HTTP 401")

    clock.advance(3600.0)
    assert store.status("exa", "fp")["state"] == "closed"

    clock.advance(-3600.0)
    assert store.status("exa", "fp")["state"] == "cooldown"
    store.record_success("exa", "fp")
    assert store.status("exa", "fp")["state"] == "closed"
    assert store.snapshot() == []


def test_changed_credentials_clear_the_cooldown(tmp_path):
    clock = FakeClock()
    store = _store(tmp_path, clock)
    store.record_failure("zhipu", provider_fingerprint("old-key", "https://open.bigmodel.cn/api"), "auth_error", "HTTP 401")

    rekeyed = provider_fingerprint("new-key", "https://open.bigmodel.cn/api")

    assert store.status("zhipu", rekeyed)["state"] == "closed"
    assert store.should_skip("zhipu", rekeyed) == (False, store.status("zhipu", rekeyed))


def test_zero_cooldown_disables_the_store(tmp_path):
    clock = FakeClock()
    store = _store(tmp_path, clock, cooldown_seconds=0.0)

    state = store.record_failure("zhipu", "fp", "auth_error", "HTTP 401")

    assert store.enabled is False
    assert state["state"] == "closed"
    assert store.should_skip("zhipu", "fp") == (False, state)
    assert not (tmp_path / "provider_health.json").exists()


def test_reset_clears_selected_or_all_providers(tmp_path):
    clock = FakeClock()
    store = _store(tmp_path, clock)
    store.record_failure("zhipu", "fp", "auth_error", "HTTP 401")
    store.record_failure("exa", "fp", "auth_error", "HTTP 401")

    assert store.reset(["zhipu"]) == ["zhipu"]
    assert store.status("zhipu", "fp")["state"] == "closed"
    assert store.status("exa", "fp")["state"] == "cooldown"
    assert store.reset(["missing"]) == []
    assert store.reset() == ["exa"]
    assert store.snapshot() == []


def test_corrupt_or_foreign_store_is_ignored_rather_than_raising(tmp_path):
    clock = FakeClock()
    path = tmp_path / "provider_health.json"
    store = _store(tmp_path, clock)

    path.write_text("{not json", encoding="utf-8")
    assert store.snapshot() == []

    path.write_text(json.dumps({"version": 99, "providers": {"zhipu": {}}}), encoding="utf-8")
    assert store.status("zhipu", "fp")["state"] == "closed"

    # A readable store still works after being overwritten by a valid record.
    store.record_failure("zhipu", "fp", "auth_error", "HTTP 401")
    assert json.loads(path.read_text(encoding="utf-8"))["version"] == 1


def test_unwritable_store_never_raises(tmp_path, monkeypatch):
    clock = FakeClock()
    store = _store(tmp_path, clock)

    def deny(*args, **kwargs):
        raise PermissionError("read-only config dir")

    monkeypatch.setattr("smart_search.provider_health.open", deny, raising=False)

    assert store.record_failure("zhipu", "fp", "auth_error", "HTTP 401")["state"] == "cooldown"
    assert store.snapshot() == []


def test_snapshot_orders_by_remaining_cooldown(tmp_path):
    clock = FakeClock()
    store = _store(tmp_path, clock)
    store.record_failure("tavily", "fp", "network_error", "HTTP 503")
    store.record_failure("tavily", "fp", "network_error", "HTTP 503")
    store.record_failure("zhipu", "fp", "auth_error", "HTTP 401")

    assert [item["provider"] for item in store.snapshot()] == ["zhipu", "tavily"]


@pytest.mark.parametrize("error_type", ["timeout", "rate_limited", "provider_error", "network_error", "parse_error"])
def test_only_auth_and_config_errors_count_as_hard(tmp_path, error_type):
    clock = FakeClock()
    store = _store(tmp_path, clock)

    assert store.record_failure("zhipu", "fp", error_type, "boom")["state"] == "closed"
