"""Single adapter for all model calls. Nothing else talks to a provider API."""

from __future__ import annotations

import json
import re
from typing import Any, Protocol

import httpx
from pydantic import BaseModel, Field

from agent.config import AppConfig
from agent.errors import LlmError

_JSON_OBJECT = re.compile(r"\{.*\}", re.DOTALL)


class MatchScore(BaseModel):
    """Strict matcher output required by JobBot."""

    match_score: int = Field(ge=0, le=100)
    reason: str = Field(min_length=1, max_length=500)


class LlmTransport(Protocol):
    def post_json(self, url: str, *, headers: dict[str, str], body: dict[str, Any], timeout_s: float) -> dict[str, Any]:
        ...


class HttpxTransport:
    def post_json(
        self, url: str, *, headers: dict[str, str], body: dict[str, Any], timeout_s: float
    ) -> dict[str, Any]:
        try:
            response = httpx.post(url, headers=headers, json=body, timeout=timeout_s)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            raise LlmError(f"LLM HTTP failure: {exc}") from exc
        if not isinstance(data, dict):
            raise LlmError("LLM response was not a JSON object")
        return data


class LlmClient:
    """Timeout-bounded structured-output client for Gemini or Groq."""

    def __init__(self, config: AppConfig, transport: LlmTransport | None = None) -> None:
        self._config = config
        self._transport = transport or HttpxTransport()

    def complete_json(self, *, system: str, user: str, timeout_s: float = 30.0) -> dict[str, Any]:
        """Call the configured provider and parse a JSON object from the reply.

        Raises:
            ConfigError path is pre-validated; LlmError on HTTP or parse failure.
        """
        if self._config.llm_provider == "gemini":
            raw = self._complete_gemini(system=system, user=user, timeout_s=timeout_s)
        else:
            raw = self._complete_groq(system=system, user=user, timeout_s=timeout_s)
        return parse_json_object(raw)

    def match_job(self, *, system: str, user: str, timeout_s: float = 30.0) -> MatchScore:
        data = self.complete_json(system=system, user=user, timeout_s=timeout_s)
        try:
            return MatchScore.model_validate(data)
        except Exception as exc:
            raise LlmError(f"LLM JSON failed MatchScore validation: {exc}") from exc

    def _complete_gemini(self, *, system: str, user: str, timeout_s: float) -> str:
        key = self._config.llm_api_key
        if not key:
            raise LlmError("JOBBOT_LLM_API_KEY is missing")
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self._config.llm_model}:generateContent"
        )
        body = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 256},
        }
        data = self._transport.post_json(
            url,
            headers={"x-goog-api-key": key, "content-type": "application/json"},
            body=body,
            timeout_s=timeout_s,
        )
        try:
            return str(data["candidates"][0]["content"]["parts"][0]["text"])
        except (KeyError, IndexError, TypeError) as exc:
            raise LlmError("Unexpected Gemini response shape") from exc

    def _complete_groq(self, *, system: str, user: str, timeout_s: float) -> str:
        key = self._config.llm_api_key
        if not key:
            raise LlmError("JOBBOT_LLM_API_KEY is missing")
        data = self._transport.post_json(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"authorization": f"Bearer {key}", "content-type": "application/json"},
            body={
                "model": self._config.llm_model,
                "temperature": 0.1,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
            timeout_s=timeout_s,
        )
        try:
            return str(data["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError) as exc:
            raise LlmError("Unexpected Groq response shape") from exc


def parse_json_object(text: str) -> dict[str, Any]:
    """Parse a JSON object, including fenced model replies.

    Raises:
        LlmError: no object found or JSON invalid.
    """
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    match = _JSON_OBJECT.search(stripped)
    if not match:
        raise LlmError("Model reply contained no JSON object")
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise LlmError(f"Model JSON was invalid: {exc}") from exc
    if not isinstance(data, dict):
        raise LlmError("Model JSON was not an object")
    return data
