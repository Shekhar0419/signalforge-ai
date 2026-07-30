from typing import Any

import pytest

from app.services.llm_provider import (
    LLMProviderError,
    OllamaProvider,
    OpenAICompatibleProvider,
    parse_json_content,
)


def test_openai_provider_generates_normalized_result() -> None:
    captured_request: dict[str, Any] = {}

    def fake_http_post(
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any],
        timeout_seconds: float,
    ) -> dict[str, Any]:
        captured_request["url"] = url
        captured_request["headers"] = headers
        captured_request["payload"] = payload
        captured_request["timeout_seconds"] = timeout_seconds

        return {
            "choices": [
                {
                    "message": {
                        "content": (
                            '{"executive_summary": "Dataset reviewed."}'
                        )
                    }
                }
            ]
        }

    provider = OpenAICompatibleProvider(
        api_key="test-api-key",
        model="test-model",
        base_url="https://example.com/v1",
        timeout_seconds=15,
        http_post=fake_http_post,
    )

    result = provider.generate(
        prompt="Analyze this profile.",
        system_prompt="Return JSON.",
    )

    assert result.provider == "openai"
    assert result.model == "test-model"
    assert "Dataset reviewed" in result.content

    assert captured_request["url"] == (
        "https://example.com/v1/chat/completions"
    )

    assert captured_request["headers"]["Authorization"] == (
        "Bearer test-api-key"
    )

    assert captured_request["payload"]["model"] == "test-model"
    assert captured_request["payload"]["temperature"] == 0.1

    assert captured_request["payload"]["messages"] == [
        {
            "role": "system",
            "content": "Return JSON.",
        },
        {
            "role": "user",
            "content": "Analyze this profile.",
        },
    ]

    assert captured_request["timeout_seconds"] == 15


def test_ollama_provider_generates_normalized_result() -> None:
    captured_request: dict[str, Any] = {}

    def fake_http_post(
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any],
        timeout_seconds: float,
    ) -> dict[str, Any]:
        captured_request["url"] = url
        captured_request["headers"] = headers
        captured_request["payload"] = payload
        captured_request["timeout_seconds"] = timeout_seconds

        return {
            "message": {
                "role": "assistant",
                "content": (
                    '{"executive_summary": "Local analysis complete."}'
                ),
            }
        }

    provider = OllamaProvider(
        model="qwen2.5:7b",
        base_url="http://localhost:11434",
        timeout_seconds=45,
        http_post=fake_http_post,
    )

    result = provider.generate(
        prompt="Analyze this profile.",
    )

    assert result.provider == "ollama"
    assert result.model == "qwen2.5:7b"
    assert "Local analysis complete" in result.content

    assert captured_request["url"] == (
        "http://localhost:11434/api/chat"
    )

    assert captured_request["payload"]["stream"] is False
    assert captured_request["payload"]["format"] == "json"
    assert captured_request["timeout_seconds"] == 45


def test_openai_provider_rejects_empty_api_key() -> None:
    with pytest.raises(
        ValueError,
        match="API key",
    ):
        OpenAICompatibleProvider(
            api_key="",
            model="test-model",
        )


def test_provider_rejects_empty_prompt() -> None:
    provider = OllamaProvider(
        model="qwen2.5:7b",
        http_post=lambda *_: {},
    )

    with pytest.raises(
        ValueError,
        match="prompt",
    ):
        provider.generate("   ")


def test_openai_provider_rejects_missing_choices() -> None:
    provider = OpenAICompatibleProvider(
        api_key="test-api-key",
        model="test-model",
        http_post=lambda *_: {},
    )

    with pytest.raises(
        LLMProviderError,
        match="no choices",
    ):
        provider.generate(
            "Analyze this profile."
        )


def test_ollama_provider_rejects_missing_message() -> None:
    provider = OllamaProvider(
        model="qwen2.5:7b",
        http_post=lambda *_: {},
    )

    with pytest.raises(
        LLMProviderError,
        match="no message",
    ):
        provider.generate(
            "Analyze this profile."
        )


def test_parse_json_content() -> None:
    parsed = parse_json_content(
        '{"executive_summary": "Valid result"}'
    )

    assert parsed == {
        "executive_summary": "Valid result"
    }


def test_parse_json_content_accepts_markdown_fence() -> None:
    parsed = parse_json_content(
        """```json
{
  "executive_summary": "Valid fenced result"
}
```"""
    )

    assert parsed["executive_summary"] == (
        "Valid fenced result"
    )


def test_parse_json_content_rejects_invalid_json() -> None:
    with pytest.raises(
        LLMProviderError,
        match="not valid JSON",
    ):
        parse_json_content(
            "This is not JSON."
        )


def test_parse_json_content_rejects_json_array() -> None:
    with pytest.raises(
        LLMProviderError,
        match="JSON object",
    ):
        parse_json_content(
            '["invalid", "response"]'
        )