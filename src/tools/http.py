"""Timeout-bounded HTTP GET/POST used by ATS adapters."""

from __future__ import annotations

from typing import Any, Protocol

import httpx

from agent.errors import SkillUpstreamError


class HttpTransport(Protocol):
    def get_json(self, url: str, *, timeout_s: float) -> Any: ...

    def post_json(self, url: str, *, body: dict[str, Any], timeout_s: float) -> Any: ...


class HttpxHttp:
    def get_json(self, url: str, *, timeout_s: float) -> Any:
        try:
            response = httpx.get(
                url,
                timeout=timeout_s,
                headers={"user-agent": "jobbot/0.1 (ATS public API client)"},
                follow_redirects=True,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise SkillUpstreamError(f"GET {url} failed: {exc}") from exc

    def post_json(self, url: str, *, body: dict[str, Any], timeout_s: float) -> Any:
        try:
            response = httpx.post(
                url,
                json=body,
                timeout=timeout_s,
                headers={
                    "user-agent": "jobbot/0.1 (ATS public API client)",
                    "content-type": "application/json",
                    "accept": "application/json",
                },
                follow_redirects=True,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise SkillUpstreamError(f"POST {url} failed: {exc}") from exc
