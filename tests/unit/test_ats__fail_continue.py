from datetime import datetime, timedelta, timezone
from typing import Any

from agent.errors import SkillUpstreamError
from agent.profile import JobProfile, Sources, Candidate, SearchRules, WorkdayBoard
from tools.ats import ingest_all


class ScriptedHttp:
    def __init__(self, mapping: dict[str, Any]) -> None:
        self.mapping = mapping

    def get_json(self, url: str, *, timeout_s: float) -> Any:
        _ = timeout_s
        if url not in self.mapping:
            raise SkillUpstreamError(f"unexpected GET {url}")
        value = self.mapping[url]
        if isinstance(value, Exception):
            raise value
        return value

    def post_json(self, url: str, *, body: dict[str, Any], timeout_s: float) -> Any:
        _ = body, timeout_s
        if url not in self.mapping:
            raise SkillUpstreamError(f"unexpected POST {url}")
        value = self.mapping[url]
        if isinstance(value, Exception):
            raise value
        return value


def test_ingest_all__one_source_fails__others_continue() -> None:
    now = datetime.now(timezone.utc)
    iso = now.isoformat()
    http = ScriptedHttp(
        {
            "https://boards-api.greenhouse.io/v1/boards/goodco/jobs?content=true": {
                "jobs": [
                    {
                        "title": "Python Engineer",
                        "company_name": "GoodCo",
                        "absolute_url": "https://boards.greenhouse.io/goodco/jobs/1",
                        "first_published": iso,
                        "location": {"name": "Remote"},
                        "content": "<p>Python FastAPI</p>",
                    }
                ]
            },
            "https://api.lever.co/v0/postings/badco?mode=json": SkillUpstreamError("lever down"),
        }
    )
    profile = JobProfile(
        candidate=Candidate(
            skills=["Python"],
            locations=["Remote"],
            experience_years=3,
            resume_path="JobBot/resume.txt",
        ),
        search=SearchRules(max_age_hours=12),
        sources=Sources(greenhouse=["goodco"], lever=["badco"], workday=[]),
    )
    jobs, errors = ingest_all(profile, http=http)
    assert len(jobs) == 1
    assert jobs[0].title == "Python Engineer"
    assert any("lever:badco" in e for e in errors)


def test_ingest_all__stale_job__filtered() -> None:
    old = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
    http = ScriptedHttp(
        {
            "https://boards-api.greenhouse.io/v1/boards/goodco/jobs?content=true": {
                "jobs": [
                    {
                        "title": "Ancient Role",
                        "company_name": "GoodCo",
                        "absolute_url": "https://boards.greenhouse.io/goodco/jobs/9",
                        "first_published": old,
                        "location": {"name": "Remote"},
                        "content": "Python",
                    }
                ]
            }
        }
    )
    profile = JobProfile(
        candidate=Candidate(
            skills=["Python"],
            locations=["Remote"],
            experience_years=3,
            resume_path="JobBot/resume.txt",
        ),
        sources=Sources(greenhouse=["goodco"]),
    )
    jobs, errors = ingest_all(profile, http=http)
    assert jobs == []
    assert errors == []
