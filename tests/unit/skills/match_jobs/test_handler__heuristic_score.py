from datetime import datetime, timezone

from agent.jobs import JobPosting
from skills.match_jobs.handler import heuristic_score
from skills.match_jobs.schema import MatchInput


def test_heuristic_score__skill_and_location_overlap__high() -> None:
    job = JobPosting(
        source="lever",
        company="Acme",
        title="Backend Engineer",
        location="Remote",
        url="https://jobs.lever.co/acme/1",
        posted_at=datetime.now(timezone.utc),
        description="Looking for Python and FastAPI on PostgreSQL.",
    )
    inp = MatchInput(
        jobs=[job],
        resume="Python",
        skills=["Python", "FastAPI", "PostgreSQL"],
        locations=["Remote"],
        experience_years=3,
        exclude_terms=[],
        match_threshold=70,
    )
    score = heuristic_score(job, inp)
    assert score.match_score >= 70
