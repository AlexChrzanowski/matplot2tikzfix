"""
LLM-based script generator.

Supports Anthropic (default) and a stubbed OpenAI provider.
The LLMProvider protocol allows additional backends to be plugged in.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from .example_suite import GeneratedScript
from .prompts import (
    RETRY_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    build_retry_prompt,
    build_user_prompt,
)


# ---------------------------------------------------------------------------
# Provider protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class LLMProvider(Protocol):
    def generate(self, system: str, user: str) -> str:
        ...


# ---------------------------------------------------------------------------
# Anthropic provider
# ---------------------------------------------------------------------------

class AnthropicProvider:
    def __init__(self, model: str, api_key: str) -> None:
        try:
            import anthropic  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "anthropic package not installed. Run: pip install anthropic"
            ) from exc
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def generate(self, system: str, user: str) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return response.content[0].text


# ---------------------------------------------------------------------------
# OpenAI provider (stub)
# ---------------------------------------------------------------------------

class OpenAIProvider:
    def __init__(self, model: str, api_key: str) -> None:
        # TODO: plug in openai client
        try:
            import openai  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "openai package not installed. Run: pip install openai"
            ) from exc
        self._client = openai.OpenAI(api_key=api_key)
        self._model = model

    def generate(self, system: str, user: str) -> str:
        # TODO: OpenAI provider — implement full chat-completion call
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content or ""


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def make_provider(provider: str, model: str) -> LLMProvider:
    if provider == "anthropic":
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable is not set."
            )
        return AnthropicProvider(model=model, api_key=api_key)
    elif provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is not set."
            )
        return OpenAIProvider(model=model, api_key=api_key)
    else:
        raise ValueError(f"Unknown provider: {provider!r}. Use 'anthropic' or 'openai'.")


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

class LLMGenerator:
    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    def generate_script(self, test_index: int, seed: int) -> GeneratedScript | None:
        """
        Ask the LLM to generate a Matplotlib test script.

        Returns a GeneratedScript on success, or None if both attempts fail.
        """
        user_prompt = build_user_prompt(test_index, seed)
        raw = self._provider.generate(SYSTEM_PROMPT, user_prompt)

        result = _parse_response(raw)
        if result is not None:
            return result

        # Retry once with a stricter prompt
        retry_user = build_retry_prompt(test_index, seed, raw)
        raw2 = self._provider.generate(RETRY_SYSTEM_PROMPT, retry_user)
        result = _parse_response(raw2)
        return result  # None means generation_error


# ---------------------------------------------------------------------------
# JSON parsing helpers
# ---------------------------------------------------------------------------

def _parse_response(raw: str) -> GeneratedScript | None:
    """Try to parse raw LLM output as JSON with 'features' and 'code' keys."""
    text = raw.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.splitlines()
        # Remove first and last fence lines
        inner = []
        in_block = False
        for line in lines:
            if line.startswith("```") and not in_block:
                in_block = True
                continue
            if line.startswith("```") and in_block:
                break
            if in_block:
                inner.append(line)
        text = "\n".join(inner)

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Try to find the first { ... } block
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                data = json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                return None
        else:
            return None

    if not isinstance(data, dict):
        return None

    features = data.get("features")
    code = data.get("code")

    if not isinstance(features, list) or not isinstance(code, str):
        return None

    return GeneratedScript(features=[str(f) for f in features], code=code)
