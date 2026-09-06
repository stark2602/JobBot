"""Write this run's matches to CSV and persist hashes in SQLite."""

from __future__ import annotations

from datetime import datetime, timezone

from agent.errors import SkillPermissionDenied, SkillTimeoutError
from skills.export_csv.schema import ExportInput, ExportOutput
from skills.manifest import CostEstimate, SkillContext, SkillManifest
from tools.csv_export import append_jobs
from tools.sqlite_store import JobStore, StoredJob


async def handle(inp: ExportInput, ctx: SkillContext) -> ExportOutput:
    if datetime.now(timezone.utc) >= ctx.deadline:
        raise SkillTimeoutError("export_csv deadline exceeded")
    if "filesystem:write" not in ctx.granted_permissions:
        raise SkillPermissionDenied("export_csv requires filesystem:write")
    store = ctx.extras.get("store")
    if not isinstance(store, JobStore):
        store = JobStore(ctx.config.sqlite_path)
    seen_at = store.seen_at_now()
    rows: list[StoredJob] = []
    for item in inp.matched:
        posting = item.posting
        rows.append(
            StoredJob(
                job_hash=posting.job_hash,
                company=posting.company,
                title=posting.title,
                location=posting.location,
                url=posting.url,
                match_score=item.match_score,
                reason=item.reason,
                source=posting.source,
                posted_at=posting.posted_at.isoformat(),
                seen_at=seen_at,
            )
        )
    persisted = 0
    for row in rows:
        if not store.exists(row.job_hash):
            store.insert(row)
            persisted += 1
    path = append_jobs(ctx.config.csv_path, rows)
    return ExportOutput(csv_path=str(path), rows_written=len(rows), persisted=persisted)


SKILL = SkillManifest(
    name="export_csv",
    description=(
        "Append matched jobs to the tracking CSV and insert new hashes into SQLite. "
        "Use after match_jobs. Not for sending email."
    ),
    input_schema=ExportInput,
    output_schema=ExportOutput,
    permissions=["filesystem:write"],
    cost_estimate=CostEstimate(usd=0.0, latency_s=0.2),
    idempotent=True,
    handler=handle,
)
