"""DeepSeek web search and page fetch.

Both tools live under the DeepSeek API host (`/v1/tools/search` and
`/v1/tools/fetch`) and use the same Bearer key as the DeepSeek chat API.
"""
from ..i18n import source_message

from typing import Any

import httpx

from ..provider_errors import ProviderCallError, provider_call_error


MAX_QUERY_CHARS = 128
MAX_COUNT = 50
# Fetch answers 403 when its safety policy refuses a URL and 404 when the page
# has no usable Markdown. Both describe that one page, not the key or the
# service, so they read as "no content" and leave provider health alone.
PAGE_UNAVAILABLE_STATUSES = frozenset({403, 404})


def tools_endpoint(api_url: str, tool: str) -> str:
    base = api_url.rstrip("/")
    # The chat API documents both https://api.deepseek.com and .../v1 as its base.
    if base.endswith("/v1"):
        base = base[: -len("/v1")]
    return f"{base}/v1/tools/{tool}"


def search_query(query: str) -> str:
    """Fit a query into the 128-character limit, preferring a word boundary."""
    text = " ".join(query.split())
    if len(text) <= MAX_QUERY_CHARS:
        return text
    cut = text[:MAX_QUERY_CHARS]
    space = cut.rfind(" ")
    return cut[:space] if space >= MAX_QUERY_CHARS // 2 else cut


def _normalize_search_result(item: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {
        "title": item.get("title") or "",
        "url": item.get("url") or "",
        # summary is the longer, query-focused excerpt DeepSeek writes for models.
        "description": item.get("summary") or item.get("snippet") or "",
        "provider": "deepseek",
    }
    site_name = item.get("site_name") or ""
    if site_name:
        out["source"] = site_name
    published = item.get("date") or ""
    if published:
        out["published_date"] = published
    return out


class DeepSeekToolsProvider:
    def __init__(self, api_url: str, api_key: str, timeout: float = 60.0):
        self.api_url = api_url
        self.api_key = api_key or ""
        self.timeout = timeout

    def get_provider_name(self) -> str:
        return "deepseek"

    async def _post(self, tool: str, body: dict[str, Any]) -> httpx.Response:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        timeout = httpx.Timeout(connect=6.0, read=self.timeout, write=10.0, pool=None)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            return await client.post(tools_endpoint(self.api_url, tool), headers=headers, json=body)

    async def search(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        """Return normalized results; an empty list means DeepSeek found nothing."""
        body = {"query": search_query(query), "count": max(1, min(int(max_results), MAX_COUNT))}
        try:
            response = await self._post("search", body)
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise ProviderCallError("parse_error", source_message('DeepSeek search response is not a JSON object'))
            results = payload.get("results")
            if not isinstance(results, list):
                raise ProviderCallError("parse_error", source_message('DeepSeek search response is missing results'))
        except Exception as exc:
            raise provider_call_error(exc, additional_secrets=(self.api_key,)) from exc
        return [_normalize_search_result(item) for item in results[:max_results] if isinstance(item, dict)]

    async def fetch(self, url: str) -> dict[str, str] | None:
        """Return {title, content}, or None when DeepSeek has no usable text for this page."""
        try:
            response = await self._post("fetch", {"url": url})
            if response.status_code in PAGE_UNAVAILABLE_STATUSES:
                return None
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise ProviderCallError("parse_error", source_message('DeepSeek fetch response is not a JSON object'))
            content = payload.get("content")
            if not isinstance(content, str):
                raise ProviderCallError("parse_error", source_message('DeepSeek fetch content is not text'))
        except Exception as exc:
            raise provider_call_error(exc, additional_secrets=(self.api_key,)) from exc
        if not content.strip():
            return None
        return {"title": str(payload.get("title") or ""), "content": content}
