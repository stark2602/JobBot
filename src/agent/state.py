"""Immutable agent state and append-only event log."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

DecisionKind = Literal["call_skill", "final", "clarify"]
Role = Literal["system", "user", "assistant", "tool"]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Message(BaseModel):
    """One conversation turn. Tool payloads are data, not instructions."""

    role: Role
    content: str
    created_at: datetime = Field(default_factory=utcnow)


class ToolCall(BaseModel):
    skill: str
    arguments: dict[str, Any]
    created_at: datetime = Field(default_factory=utcnow)


class ToolResult(BaseModel):
    skill: str
    ok: bool
    payload: dict[str, Any]
    error: str | None = None
    latency_ms: int = 0
    created_at: datetime = Field(default_factory=utcnow)


class BudgetRemaining(BaseModel):
    steps: int
    wall_clock_s: float
    cost_usd: float


class AgentState(BaseModel):
    """Single source of truth. Updates return a new instance."""

    model_config = {"frozen": True}

    trace_id: str = Field(default_factory=lambda: uuid4().hex)
    messages: tuple[Message, ...] = ()
    tool_calls: tuple[ToolCall, ...] = ()
    tool_results: tuple[ToolResult, ...] = ()
    working_memory: dict[str, Any] = Field(default_factory=dict)
    budget: BudgetRemaining
    started_at: datetime = Field(default_factory=utcnow)

    def append_message(self, message: Message) -> AgentState:
        return self.model_copy(update={"messages": self.messages + (message,)})

    def append_call(self, call: ToolCall) -> AgentState:
        return self.model_copy(update={"tool_calls": self.tool_calls + (call,)})

    def append_result(self, result: ToolResult) -> AgentState:
        return self.model_copy(update={"tool_results": self.tool_results + (result,)})

    def with_memory(self, patch: dict[str, Any]) -> AgentState:
        merged = {**self.working_memory, **patch}
        return self.model_copy(update={"working_memory": merged})

    def consume_step(self, *, cost_usd: float = 0.0) -> AgentState:
        remaining = BudgetRemaining(
            steps=self.budget.steps - 1,
            wall_clock_s=self.budget.wall_clock_s,
            cost_usd=round(self.budget.cost_usd - cost_usd, 6),
        )
        return self.model_copy(update={"budget": remaining})


class Decision(BaseModel):
    """Planner output. Never a free-text string."""

    kind: DecisionKind
    skill: str | None = None
    arguments: dict[str, Any] = Field(default_factory=dict)
    content: str | None = None
