import asyncio
from datetime import datetime, timezone
from pathlib import Path

from agent.jobs import JobPosting
from conftest import make_config
from skills.match_jobs.handler import handle
from skills.match_jobs.schema import MatchInput
from skills.manifest import SkillContext
from tools.sqlite_store import JobStore, StoredJob


def test_match_jobs__existing_hash__skipped(tmp_path: Path) -> None:
    job = JobPosting(
        source="greenhouse",
        company="Acme",
        title="Python Engineer",
        location="Remote",
        url="https://boards.greenhouse.io/acme/jobs/1",
        posted_at=datetime.now(timezone.utc),
        description="Python FastAPI PostgreSQL Remote",
    )
    store = JobStore(tmp_path / "jobs.sqlite")
    store.insert(
        StoredJob(
            job_hash=job.job_hash,
            company=job.company,
            title=job.title,
            location=job.location,
            url=job.url,
            match_score=90,
            reason="prior",
            source=job.source,
            posted_at=job.posted_at.isoformat(),
            seen_at="2026-09-05T00:00:00Z",
        )
    )
    cfg = make_config(tmp_path)
    ctx = SkillContext(
        deadline=datetime.now(timezone.utc).replace(year=2099),
        trace_id="t",
        granted_permissions=cfg.granted_permissions,
        config=cfg,
        extras={"store": store},
    )
    inp = MatchInput(
        jobs=[job],
        resume="Python",
        skills=["Python"],
        locations=["Remote"],
        experience_years=3,
        exclude_terms=["C2C"],
        match_threshold=70,
    )
    out = asyncio.run(handle(inp, ctx))
    assert out.skipped_hashes == [job.job_hash]
    assert out.matched == []
