"""plan → act → observe loop. Skills are invoked only here."""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import Any

from pydantic import ValidationError

from agent.config import AppConfig
from agent.errors import (
    BudgetExceeded,
    GuardrailBlocked,
    SkillPermissionDenied,
    SkillTimeoutError,
    SkillUpstreamError,
)
from agent.guardrails import Guardrails
from agent.memory import WorkingMemoryGuard
from agent.planner import plan
from agent.state import AgentState, BudgetRemaining, Decision, Message, ToolCall, ToolResult
from observability import JsonLogger, TraceEvent
from skills.manifest import SkillContext, SkillManifest
from skills.registry import get_skill


class Executor:
    """Owns the loop, budget, guardrails, and the single skill chokepoint."""

    def __init__(
        self,
        config: AppConfig,
        *,
        extras: dict[str, Any],
        logger: JsonLogger | None = None,
        guardrails: Guardrails | None = None,
    ) -> None:
        self._config = config
        self._extras = extras
        self._logger = logger or JsonLogger()
        self._guardrails = guardrails or Guardrails(allowed_skills=config.allowed_skills)
        self._memory = WorkingMemoryGuard()

    def initial_state(self, working_memory: dict[str, Any]) -> AgentState:
        return AgentState(
            working_memory=self._memory.apply(working_memory),
            budget=BudgetRemaining(
                steps=self._config.budget.max_steps,
                wall_clock_s=self._config.budget.max_wall_clock_s,
                cost_usd=self._config.budget.max_cost_usd,
            ),
        )

    async def run(self, state: AgentState) -> AgentState:
        deadline = state.started_at + timedelta(seconds=self._config.budget.max_wall_clock_s)
        step = 0
        current = state
        while True:
            step += 1
            self._assert_budget(current, deadline=deadline)
            decision = plan(current)
            self._guardrails.assert_decision(decision)
            if decision.kind != "call_skill":
                self._logger.emit(
                    TraceEvent(
                        trace_id=current.trace_id,
                        step=step,
                        event_type="final",
                        outcome="success",
                        extra={"content": decision.content},
                    )
                )
                return current.append_message(Message(role="assistant", content=decision.content or ""))
            current = await self.invoke_skill(decision, current, step=step, deadline=deadline)

    def _assert_budget(self, state: AgentState, *, deadline: datetime) -> None:
        if state.budget.steps <= 0:
            raise BudgetExceeded("max_steps exhausted")
        if datetime.now(timezone.utc) >= deadline:
            raise BudgetExceeded("max_wall_clock exhausted")
        if state.budget.cost_usd < 0:
            raise BudgetExceeded("max_cost_usd exhausted")

    async def invoke_skill(
        self,
        decision: Decision,
        state: AgentState,
        *,
        step: int,
        deadline: datetime,
    ) -> AgentState:
        name = decision.skill or ""
        skill = get_skill(name)
        self._enforce_permissions(skill)
        call = ToolCall(skill=name, arguments=decision.arguments)
        state = state.append_call(call)
        started = time.perf_counter()
        try:
            payload = await self._call_handler(skill, decision.arguments, state, deadline)
            latency = int((time.perf_counter() - started) * 1000)
            result = ToolResult(skill=name, ok=True, payload=payload, latency_ms=latency)
            outcome = "success"
            error: str | None = None
        except (SkillTimeoutError, SkillPermissionDenied, SkillUpstreamError, GuardrailBlocked, ValidationError) as exc:
            latency = int((time.perf_counter() - started) * 1000)
            result = ToolResult(
                skill=name, ok=False, payload={}, error=str(exc), latency_ms=latency
            )
            outcome = "error"
            error = str(exc)
        self._logger.emit(
            TraceEvent(
                trace_id=state.trace_id,
                step=step,
                event_type="skill",
                skill=name,
                latency_ms=result.latency_ms,
                outcome=outcome,
                extra={"error": error} if error else None,
            )
        )
        return state.append_result(result).consume_step()

    def _enforce_permissions(self, skill: SkillManifest) -> None:
        granted = set(self._config.granted_permissions)
        missing = [perm for perm in skill.permissions if perm not in granted]
        if missing:
            raise SkillPermissionDenied(f"{skill.name} missing permissions: {missing}")
        if skill.name not in self._config.allowed_skills:
            raise SkillPermissionDenied(f"{skill.name} not in bot allowlist")

    async def _call_handler(
        self,
        skill: SkillManifest,
        arguments: dict[str, Any],
        state: AgentState,
        deadline: datetime,
    ) -> dict[str, Any]:
        try:
            validated = skill.input_schema.model_validate(arguments)
        except ValidationError as exc:
            raise GuardrailBlocked(f"invalid {skill.name} input: {exc}") from exc
        ctx = SkillContext(
            deadline=deadline,
            trace_id=state.trace_id,
            granted_permissions=self._config.granted_permissions,
            config=self._config,
            extras=self._extras,
        )
        output = await skill.handler(validated, ctx)
        if not isinstance(output, skill.output_schema):
            output = skill.output_schema.model_validate(output)
        dumped = output.model_dump(mode="json")
        if not isinstance(dumped, dict):
            raise GuardrailBlocked(f"{skill.name} output was not an object")
        return dumped
