"""Structured JSON logs with secret redaction."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel

from agent.guardrails import redact_secrets


class TraceEvent(BaseModel):
    """One executor/skill step."""

    trace_id: str
    step: int
    event_type: str
    skill: str | None = None
    latency_ms: int | None = None
    cost_usd: float = 0.0
    outcome: str
    extra: dict[str, Any] | None = None


class JsonLogger:
    def emit(self, event: TraceEvent) -> None:
        payload = redact_secrets(event.model_dump())
        payload["ts"] = datetime.now(timezone.utc).isoformat()
        sys.stdout.write(json.dumps(payload, default=str) + "\n")
        sys.stdout.flush()
