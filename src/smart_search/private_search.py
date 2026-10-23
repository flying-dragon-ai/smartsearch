"""Explicit-only Xiaohongshu and WeChat Official Account search.

Search only. No publish, like, follow, or comment calls.
Credentials come from config or environment, never from CLI arguments.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .config import config

PLATFORMS = {
    "xhs": {
        "provider": "xhs",
        "source": "xiaohongshu",
        "enabled_key": "XHS_ENABLED",
        "url_key": "XHS_API_URL",
        "key_key": "XHS_API_KEY",
        "mode_key": "XHS_MODE",
    },
    "wechat": {
        "provider": "wechat",
        "source": "wechat",
        "enabled_key": "WECHAT_ENABLED",
        "url_key": "WECHAT_API_URL",
        "key_key": "WECHAT_API_KEY",
        "mode_key": "WECHAT_MODE",
    },
}

ERROR_CODES = {"auth_required", "rate_limited", "empty", "upstream"}
_FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


def _fail(provider: str, query: str, code: str, message: str) -> dict[str, Any]:
    if code not in ERROR_CODES:
        code = "upstream"
    return {
        "ok": False,
        "provider": provider,
        "query": query,
        "results": [],
        "sources": [],
        "sources_count": 0,
        "error": {"code": code, "message": message},
        "error_type": "config_error" if code == "auth_required" else "network_error" if code in {"rate_limited", "upstream"} else "quality_error",
    }


def _ok(provider: str, query: str, results: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "ok": True,
        "provider": provider,
        "query": query,
        "results": results,
        "sources": results,
        "sources_count": len(results),
        "error": None,
    }


def _settings(platform: str) -> dict[str, str]:
    spec = PLATFORMS[platform]
    mode = (config._get_config_value(spec["mode_key"], "live") or "live").strip().lower()
    return {
        "enabled": "true" if config.provider_enabled(spec["provider"]) else "false",
        "url": (config._get_config_value(spec["url_key"]) or "").strip(),
        "key": (config._get_config_value(spec["key_key"]) or "").strip(),
        "mode": mode if mode in {"live", "fixture", "browser"} else "live",
    }


def _normalize_item(raw: dict[str, Any], source: str) -> dict[str, str] | None:
    title = str(raw.get("title") or "").strip()
    url = str(raw.get("url") or "").strip()
    if not title and not url:
        return None
    return {
        "title": title,
        "url": url,
        "snippet": str(raw.get("snippet") or "").strip(),
        "source": source,
        "published_date": str(raw.get("published_date") or "").strip(),
        "author": str(raw.get("author") or "").strip(),
        "id": str(raw.get("id") or "").strip(),
    }


def _load_fixture(platform: str) -> list[dict[str, str]]:
    path = _FIXTURE_DIR / f"{platform}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    source = PLATFORMS[platform]["source"]
    items = []
    for raw in data.get("results") or []:
        item = _normalize_item(raw, source)
        if item:
            items.append(item)
    return items


def _http_json(method: str, url: str, api_key: str, payload: dict[str, Any] | None, timeout: float) -> tuple[int, Any]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    # 私域适配器默认是本机/局域网服务；显式绕过系统与环境代理，避免 127.0.0.1 被代理拦截。
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        if exc.code in {401, 403}:
            raise PrivateSearchError("auth_required", f"HTTP {exc.code}") from exc
        if exc.code == 429:
            raise PrivateSearchError("rate_limited", f"HTTP {exc.code}") from exc
        raise PrivateSearchError("upstream", f"HTTP {exc.code} {detail}") from exc
    except PrivateSearchError:
        raise
    except json.JSONDecodeError as exc:
        raise PrivateSearchError("upstream", "invalid JSON") from exc
    except Exception as exc:
        raise PrivateSearchError("upstream", str(exc)[:300]) from exc


class PrivateSearchError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def search(platform: str, query: str, count: int = 8, fixture: bool = False) -> dict[str, Any]:
    spec = PLATFORMS[platform]
    provider = spec["provider"]
    query = query.strip()
    if not query:
        return _fail(provider, query, "upstream", "query is empty")
    if not config.provider_enabled(provider):
        return _fail(provider, query, "upstream", f"{spec['enabled_key']}=false")
    settings = _settings(platform)
    mode = "fixture" if fixture else settings["mode"]
    if mode == "fixture":
        return _ok(provider, query, _load_fixture(platform)[:count])
    if mode == "browser":
        return _fail(provider, query, "upstream", "browser mode is experimental and not implemented")
    if not settings["url"] or not settings["key"]:
        return _fail(provider, query, "auth_required", f"{spec['url_key']} or {spec['key_key']} is not configured")
    endpoint = settings["url"].rstrip("/") + "/search"
    if not endpoint.startswith(("http://", "https://")):
        return _fail(provider, query, "upstream", "baseUrl must be http or https")
    try:
        _status, data = _http_json(
            "POST",
            endpoint,
            settings["key"],
            {"query": query, "count": count, "platform": platform},
			45,
        )
    except PrivateSearchError as exc:
        return _fail(provider, query, exc.code, exc.message)
    results = []
    for raw in data.get("results") or []:
        if isinstance(raw, dict):
            item = _normalize_item(raw, spec["source"])
            if item:
                results.append(item)
    if not results:
        return _fail(provider, query, "empty", "upstream returned no results")
    return _ok(provider, query, results[:count])


def channel_status(platform: str) -> dict[str, Any]:
    spec = PLATFORMS[platform]
    provider = spec["provider"]
    settings = _settings(platform)
    base = {
        "provider": provider,
        "configured": False,
        "state": "unconfigured",
        "probe": "none",
        "experimental": False,
        "error_type": "auth_required",
        "error": f"{spec['url_key']} or {spec['key_key']} is not configured",
        "consecutive_failures": 0,
        "hard_failure": False,
    }
    if settings["enabled"] != "true":
        return {**base, "state": "disabled", "error_type": "", "error": f"{spec['enabled_key']}=false"}
    if settings["mode"] == "fixture":
        return {**base, "configured": True, "state": "closed", "probe": "fixture", "error_type": "", "error": ""}
    if settings["mode"] == "browser":
        return {**base, "state": "experimental", "experimental": True, "probe": "browser", "error_type": "upstream", "error": "browser mode is experimental and not implemented"}
    if not settings["url"] or not settings["key"]:
        return base
    health = settings["url"].rstrip("/") + "/health"
    try:
        _http_json("GET", health, settings["key"], None, 10)
    except PrivateSearchError as exc:
        return {**base, "configured": True, "state": "error", "probe": "health", "error_type": exc.code, "error": exc.message}
    return {**base, "configured": True, "state": "closed", "probe": "health", "error_type": "", "error": ""}


def attach_private_status(info: dict[str, Any]) -> dict[str, Any]:
    channels = {name: channel_status(name) for name in PLATFORMS}
    info["private_search"] = channels
    health = info.setdefault("provider_health", {"providers": []})
    providers = health.setdefault("providers", [])
    seen = {item.get("provider") for item in providers}
    for status in channels.values():
        if status["provider"] not in seen:
            providers.append(status)
    capability = info.setdefault("capability_status", {})
    capability["private_search"] = {
        "configured": [name for name, status in channels.items() if status.get("configured")],
        "explicit_only": ["xhs", "wechat"],
        "ok": True,
    }
    return info
