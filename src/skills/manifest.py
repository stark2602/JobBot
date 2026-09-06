"""Skill contract types consumed by the executor registry."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from agent.config import AppConfig

Permission = str


class CostEstimate(BaseModel):
    usd: float = 0.0
    latency_s: float = 1.0


class SkillContext(BaseModel):
    """Per-invocation context. Handlers must abort before `deadline`."""

    model_config = {"arbitrary_types_allowed": True}

    deadline: datetime
    trace_id: str
    granted_permissions: list[str]
    config: AppConfig
    extras: dict[str, Any] = Field(default_factory=dict)


class SkillManifest(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    name: str
    description: str
    input_schema: type[BaseModel]
    output_schema: type[BaseModel]
    permissions: list[Permission]
    cost_estimate: CostEstimate
    idempotent: bool
    handler: Callable[[BaseModel, SkillContext], Awaitable[BaseModel]]
