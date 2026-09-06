"""Dedupe, exclude, then score with LLM or explicit heuristic backend."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from agent.errors import SkillPermissionDenied, SkillTimeoutError
from agent.guardrails import Guardrails
from agent.jobs import JobPosting, MatchedJob, contains_excluded
from agent.llm_client import LlmClient, MatchScore
from skills.manifest import CostEstimate, SkillContext, SkillManifest
from skills.match_jobs.schema import MatchInput, MatchOutput
from tools.sqlite_store import JobStore


def _prompt_text() -> str:
    return (Path(__file__).parent / "prompts" / "match_v1.md").read_text(encoding="utf-8")


def heuristic_score(job: JobPosting, inp: MatchInput) -> MatchScore:
    """Deterministic overlap scorer. Used only when matcher_backend=heuristic."""
    blob = job.blob().lower()
    skill_hits = sum(1 for skill in inp.skills if skill.lower() in blob)
    loc_hits = sum(1 for loc in inp.locations if loc.lower() in job.location.lower() or loc.lower() in blob)
    skill_ratio = skill_hits / max(1, len(inp.skills))
    loc_ratio = loc_hits / max(1, len(inp.locations))
    score = int(round(100 * (0.7 * skill_ratio + 0.3 * loc_ratio)))
    reason = (
        f"Heuristic overlap: {skill_hits}/{len(inp.skills)} listed skills and "
        f"{loc_hits}/{len(inp.locations)} locations appeared in the posting."
    )
    return MatchScore(match_score=min(100, score), reason=reason)


async def handle(inp: MatchInput, ctx: SkillContext) -> MatchOutput:
    if datetime.now(timezone.utc) >= ctx.deadline:
        raise SkillTimeoutError("match_jobs deadline exceeded")
    if "filesystem:write" not in ctx.granted_permissions:
        raise SkillPermissionDenied("match_jobs requires filesystem:write for SQLite")
    store = ctx.extras.get("store")
    if not isinstance(store, JobStore):
        store = JobStore(ctx.config.sqlite_path)
    guardrails = Guardrails(allowed_skills=ctx.config.allowed_skills)
    system = _prompt_text()
    llm = ctx.extras.get("llm")
    matched: list[MatchedJob] = []
    skipped: list[str] = []
    dropped = 0
    excluded = 0
    for job in inp.jobs:
        if datetime.now(timezone.utc) >= ctx.deadline:
            raise SkillTimeoutError("match_jobs deadline exceeded")
        if store.exists(job.job_hash):
            skipped.append(job.job_hash)
            continue
        if contains_excluded(job.blob(), inp.exclude_terms):
            excluded += 1
            continue
        if ctx.config.matcher_backend == "heuristic":
            score = heuristic_score(job, inp)
        else:
            if "network" not in ctx.granted_permissions:
                raise SkillPermissionDenied("llm matcher requires network")
            client = llm if isinstance(llm, LlmClient) else LlmClient(ctx.config)
            wrapped = guardrails.wrap_untrusted(job.blob(), source=job.url)
            user = (
                f"Candidate skills: {', '.join(inp.skills)}\n"
                f"Locations: {', '.join(inp.locations)}\n"
                f"Experience years: {inp.experience_years}\n"
                f"Resume:\n{inp.resume[:8000]}\n\n"
                f"{wrapped}"
            )
            remaining = max(1.0, (ctx.deadline - datetime.now(timezone.utc)).total_seconds())
            score = client.match_job(system=system, user=user, timeout_s=min(30.0, remaining))
        if score.match_score < inp.match_threshold:
            dropped += 1
            continue
        matched.append(MatchedJob(posting=job, match_score=score.match_score, reason=score.reason))
    return MatchOutput(
        matched=matched,
        skipped_hashes=skipped,
        dropped_below_threshold=dropped,
        excluded=excluded,
    )


SKILL = SkillManifest(
    name="match_jobs",
    description=(
        "Score ingested jobs against the candidate YAML skills/location/experience and resume. "
        "Skip hashes already in SQLite. Drop excluded terms and scores below threshold. "
        "Use after ingest_jobs has returned postings."
    ),
    input_schema=MatchInput,
    output_schema=MatchOutput,
    permissions=["filesystem:write", "network"],
    cost_estimate=CostEstimate(usd=0.0, latency_s=20.0),
    idempotent=True,
    handler=handle,
)
