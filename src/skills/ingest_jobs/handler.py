"""Fetch Greenhouse/Lever/Workday jobs; isolate per-source failures."""

from __future__ import annotations

from datetime import datetime, timezone

from agent.errors import SkillPermissionDenied, SkillTimeoutError
from agent.profile import JobProfile
from skills.ingest_jobs.schema import IngestInput, IngestOutput
from skills.manifest import CostEstimate, SkillContext, SkillManifest
from tools.ats import ingest_all
from tools.http import HttpTransport


async def handle(inp: IngestInput, ctx: SkillContext) -> IngestOutput:
    _ = inp
    if datetime.now(timezone.utc) >= ctx.deadline:
        raise SkillTimeoutError("ingest_jobs deadline exceeded")
    if "network" not in ctx.granted_permissions:
        raise SkillPermissionDenied("ingest_jobs requires network")
    profile = ctx.extras.get("profile")
    if not isinstance(profile, JobProfile):
        raise SkillPermissionDenied("ingest_jobs missing JobProfile in context extras")
    http = ctx.extras.get("http")
    transport: HttpTransport | None = http if http is not None else None
    remaining = max(1.0, (ctx.deadline - datetime.now(timezone.utc)).total_seconds())
    jobs, errors = ingest_all(profile, http=transport, timeout_s=min(20.0, remaining))
    return IngestOutput(jobs=jobs, source_errors=errors, fetched_at=datetime.now(timezone.utc))


SKILL = SkillManifest(
    name="ingest_jobs",
    description=(
        "Fetch recent job postings from Greenhouse, Lever, and Workday public APIs "
        "listed in the candidate YAML profile. Use when the run has not yet loaded jobs."
    ),
    input_schema=IngestInput,
    output_schema=IngestOutput,
    permissions=["network"],
    cost_estimate=CostEstimate(usd=0.0, latency_s=8.0),
    idempotent=True,
    handler=handle,
)
