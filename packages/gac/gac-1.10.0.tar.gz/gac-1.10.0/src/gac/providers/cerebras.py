"""Cerebras AI provider implementation."""

import os

import httpx

from gac.errors import AIError


def call_cerebras_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call Cerebras API directly."""
    api_key = os.getenv("CEREBRAS_API_KEY")
    if not api_key:
        raise AIError.authentication_error("CEREBRAS_API_KEY not found in environment variables")

    url = "https://api.cerebras.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    data = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}

    try:
        response = httpx.post(url, headers=headers, json=data, timeout=120)
        response.raise_for_status()
        response_data = response.json()
        content = response_data["choices"][0]["message"]["content"]
        if content is None:
            raise AIError.model_error("Cerebras API returned null content")
        if content == "":
            raise AIError.model_error("Cerebras API returned empty content")
        return content
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            raise AIError.rate_limit_error(f"Cerebras API rate limit exceeded: {e.response.text}") from e
        raise AIError.model_error(f"Cerebras API error: {e.response.status_code} - {e.response.text}") from e
    except httpx.TimeoutException as e:
        raise AIError.timeout_error(f"Cerebras API request timed out: {str(e)}") from e
    except Exception as e:
        raise AIError.model_error(f"Error calling Cerebras API: {str(e)}") from e
