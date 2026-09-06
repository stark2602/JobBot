from datetime import datetime, timezone

from agent.jobs import JobPosting, MatchedJob
from skills.send_digest.html import split_tiers


def _job(score: int) -> MatchedJob:
    posting = JobPosting(
        source="greenhouse",
        company="Acme",
        title="Engineer",
        location="Remote",
        url="https://boards.greenhouse.io/acme/jobs/1",
        posted_at=datetime.now(timezone.utc),
    )
    return MatchedJob(posting=posting, match_score=score, reason="overlap")


def test_split_tiers__90_and_80_and_72__email_omits_72() -> None:
    top, good = split_tiers([_job(92), _job(80), _job(72)])
    assert [j.match_score for j in top] == [92]
    assert [j.match_score for j in good] == [80]
