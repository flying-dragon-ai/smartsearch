import json

import httpx
import pytest

from smart_search.provider_errors import ProviderCallError, classify_provider_exception


def _http_error(status_code: int) -> httpx.HTTPStatusError:
    request = httpx.Request("POST", "https://provider.example.test")
    response = httpx.Response(status_code, text="provider detail", request=request)
    return httpx.HTTPStatusError("provider failed", request=request, response=response)


@pytest.mark.parametrize(
    ("status_code", "error_type"),
    [
        (400, "parameter_error"),
        (401, "auth_error"),
        (403, "auth_error"),
        (408, "timeout"),
        (422, "parameter_error"),
        (429, "rate_limited"),
        (500, "network_error"),
        (503, "network_error"),
    ],
)
def test_http_statuses_use_the_stable_provider_error_taxonomy(status_code, error_type):
    actual_type, message = classify_provider_exception(_http_error(status_code))

    assert actual_type == error_type
    assert f"HTTP {status_code}" in message


@pytest.mark.parametrize(
    ("exc", "error_type"),
    [
        (httpx.TimeoutException("slow"), "timeout"),
        (httpx.ConnectError("offline"), "network_error"),
        (json.JSONDecodeError("bad JSON", "not-json", 0), "parse_error"),
        (ProviderCallError("provider_error", "tool rejected the request"), "provider_error"),
        (ProviderCallError("quality_error", "challenge page"), "quality_error"),
    ],
)
def test_non_http_failures_use_the_stable_provider_error_taxonomy(exc, error_type):
    actual_type, _ = classify_provider_exception(exc)

    assert actual_type == error_type


def test_provider_error_excerpt_redacts_credentials():
    request = httpx.Request("POST", "https://user:password@example.test")
    response = httpx.Response(
        401,
        text='Authorization: Bearer bearer-secret; {"api_key":"api-secret", "access_token":"access-secret"}',
        request=request,
    )
    error = httpx.HTTPStatusError("provider failed", request=request, response=response)

    _, message = classify_provider_exception(error)

    assert "bearer-secret" not in message
    assert "api-secret" not in message
    assert "access-secret" not in message
    assert "password" not in message
    assert "[REDACTED]" in message


def test_provider_error_excerpt_redacts_configured_secret_without_a_label():
    request = httpx.Request("POST", "https://provider.example.test")
    response = httpx.Response(
        500,
        text="upstream echoed configured-secret during failure",
        request=request,
    )
    error = httpx.HTTPStatusError("provider failed", request=request, response=response)

    _, message = classify_provider_exception(error, additional_secrets=("configured-secret",))

    assert "configured-secret" not in message
    assert "[REDACTED]" in message
