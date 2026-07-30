from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class LLMProviderError(RuntimeError):
    """Raised when an LLM provider request cannot be completed."""


@dataclass(frozen=True)
class LLMProviderResult:
    """
    Normalized response returned by every supported LLM provider.
    """

    content: str
    provider: str
    model: str


HTTPPostFunction = Callable[
    [str, dict[str, str], dict[str, Any], float],
    dict[str, Any],
]


def _default_http_post(
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout_seconds: float,
) -> dict[str, Any]:
    """
    Send a JSON POST request using only the Python standard library.
    """
    encoded_payload = json.dumps(payload).encode("utf-8")

    request = Request(
        url=url,
        data=encoded_payload,
        headers=headers,
        method="POST",
    )

    try:
        with urlopen(
            request,
            timeout=timeout_seconds,
        ) as response:
            response_body = response.read().decode("utf-8")

    except HTTPError as exc:
        error_body = exc.read().decode(
            "utf-8",
            errors="replace",
        )

        raise LLMProviderError(
            f"LLM provider returned HTTP {exc.code}: "
            f"{error_body[:500]}"
        ) from exc

    except URLError as exc:
        raise LLMProviderError(
            f"Unable to connect to the LLM provider: {exc.reason}"
        ) from exc

    except socket.timeout as exc:
        raise LLMProviderError(
            "The LLM provider request timed out."
        ) from exc

    except TimeoutError as exc:
        raise LLMProviderError(
            "The LLM provider request timed out."
        ) from exc

    try:
        parsed_response = json.loads(response_body)
    except json.JSONDecodeError as exc:
        raise LLMProviderError(
            "The LLM provider returned invalid JSON."
        ) from exc

    if not isinstance(parsed_response, dict):
        raise LLMProviderError(
            "The LLM provider returned an unexpected response."
        )

    return parsed_response


class OpenAICompatibleProvider:
    """
    Client for OpenAI and OpenAI-compatible chat-completion APIs.
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://api.openai.com/v1",
        timeout_seconds: float = 30.0,
        http_post: HTTPPostFunction | None = None,
    ) -> None:
        cleaned_api_key = api_key.strip()
        cleaned_model = model.strip()
        cleaned_base_url = base_url.rstrip("/")

        if not cleaned_api_key:
            raise ValueError(
                "An API key is required for the OpenAI provider."
            )

        if not cleaned_model:
            raise ValueError(
                "A model name is required for the OpenAI provider."
            )

        if timeout_seconds <= 0:
            raise ValueError(
                "timeout_seconds must be greater than zero."
            )

        self.api_key = cleaned_api_key
        self.model = cleaned_model
        self.base_url = cleaned_base_url
        self.timeout_seconds = timeout_seconds
        self.http_post = http_post or _default_http_post

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> LLMProviderResult:
        """
        Generate a response through an OpenAI-compatible endpoint.
        """
        cleaned_prompt = prompt.strip()

        if not cleaned_prompt:
            raise ValueError(
                "The prompt cannot be empty."
            )

        messages: list[dict[str, str]] = []

        if system_prompt and system_prompt.strip():
            messages.append(
                {
                    "role": "system",
                    "content": system_prompt.strip(),
                }
            )

        messages.append(
            {
                "role": "user",
                "content": cleaned_prompt,
            }
        )

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.1,
            "response_format": {
                "type": "json_object",
            },
        }

        response = self.http_post(
            f"{self.base_url}/chat/completions",
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            payload,
            self.timeout_seconds,
        )

        content = self._extract_content(response)

        return LLMProviderResult(
            content=content,
            provider="openai",
            model=self.model,
        )

    @staticmethod
    def _extract_content(
        response: dict[str, Any],
    ) -> str:
        choices = response.get("choices")

        if not isinstance(choices, list) or not choices:
            raise LLMProviderError(
                "The OpenAI-compatible response has no choices."
            )

        first_choice = choices[0]

        if not isinstance(first_choice, dict):
            raise LLMProviderError(
                "The OpenAI-compatible response contains "
                "an invalid choice."
            )

        message = first_choice.get("message")

        if not isinstance(message, dict):
            raise LLMProviderError(
                "The OpenAI-compatible response has no message."
            )

        content = message.get("content")

        if not isinstance(content, str) or not content.strip():
            raise LLMProviderError(
                "The OpenAI-compatible response has empty content."
            )

        return content.strip()


class OllamaProvider:
    """
    Client for a locally running Ollama server.
    """

    def __init__(
        self,
        model: str,
        base_url: str = "http://localhost:11434",
        timeout_seconds: float = 60.0,
        http_post: HTTPPostFunction | None = None,
    ) -> None:
        cleaned_model = model.strip()
        cleaned_base_url = base_url.rstrip("/")

        if not cleaned_model:
            raise ValueError(
                "A model name is required for Ollama."
            )

        if timeout_seconds <= 0:
            raise ValueError(
                "timeout_seconds must be greater than zero."
            )

        self.model = cleaned_model
        self.base_url = cleaned_base_url
        self.timeout_seconds = timeout_seconds
        self.http_post = http_post or _default_http_post

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> LLMProviderResult:
        """
        Generate a response through Ollama's chat endpoint.
        """
        cleaned_prompt = prompt.strip()

        if not cleaned_prompt:
            raise ValueError(
                "The prompt cannot be empty."
            )

        messages: list[dict[str, str]] = []

        if system_prompt and system_prompt.strip():
            messages.append(
                {
                    "role": "system",
                    "content": system_prompt.strip(),
                }
            )

        messages.append(
            {
                "role": "user",
                "content": cleaned_prompt,
            }
        )

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.1,
            },
        }

        response = self.http_post(
            f"{self.base_url}/api/chat",
            {
                "Content-Type": "application/json",
            },
            payload,
            self.timeout_seconds,
        )

        content = self._extract_content(response)

        return LLMProviderResult(
            content=content,
            provider="ollama",
            model=self.model,
        )

    @staticmethod
    def _extract_content(
        response: dict[str, Any],
    ) -> str:
        message = response.get("message")

        if not isinstance(message, dict):
            raise LLMProviderError(
                "The Ollama response has no message."
            )

        content = message.get("content")

        if not isinstance(content, str) or not content.strip():
            raise LLMProviderError(
                "The Ollama response has empty content."
            )

        return content.strip()


def parse_json_content(
    content: str,
) -> dict[str, Any]:
    """
    Parse a provider response expected to contain one JSON object.

    Markdown JSON fences are accepted because some models return them
    even when instructed to produce plain JSON.
    """
    cleaned_content = content.strip()

    if cleaned_content.startswith("```"):
        lines = cleaned_content.splitlines()

        if lines and lines[0].strip().lower() in {
            "```",
            "```json",
        }:
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        cleaned_content = "\n".join(lines).strip()

    try:
        parsed_content = json.loads(cleaned_content)
    except json.JSONDecodeError as exc:
        raise LLMProviderError(
            "The model response is not valid JSON."
        ) from exc

    if not isinstance(parsed_content, dict):
        raise LLMProviderError(
            "The model response must be a JSON object."
        )

    return parsed_content