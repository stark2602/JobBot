import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent.errors import SkillUpstreamError
from agent.executor import Executor
from agent.profile import Candidate, JobProfile, SearchRules, Sources
from conftest import make_config
from tools.sqlite_store import JobStore


class ScriptedHttp:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def get_json(self, url: str, *, timeout_s: float) -> Any:
        _ = url, timeout_s
        return self.payload

    def post_json(self, url: str, *, body: dict[str, Any], timeout_s: float) -> Any:
        raise SkillUpstreamError("no workday in this test")


def test_executor__full_heuristic_run_writes_csv(tmp_path: Path) -> None:
    now = datetime.now(timezone.utc).isoformat()
    http = ScriptedHttp(
        {
            "jobs": [
                {
                    "title": "Python Engineer",
                    "company_name": "GoodCo",
                    "absolute_url": "https://boards.greenhouse.io/goodco/jobs/1",
                    "first_published": now,
                    "location": {"name": "Remote"},
                    "content": "Python FastAPI PostgreSQL TypeScript",
                }
            ]
        }
    )
    profile = JobProfile(
        candidate=Candidate(
            skills=["Python", "FastAPI", "PostgreSQL", "TypeScript"],
            locations=["Remote"],
            experience_years=3,
            resume_path="JobBot/resume.txt",
        ),
        search=SearchRules(max_age_hours=12),
        sources=Sources(greenhouse=["goodco"]),
    )
    cfg = make_config(tmp_path)
    store = JobStore(cfg.sqlite_path)
    executor = Executor(
        cfg,
        extras={"profile": profile, "store": store, "http": http},
    )
    state = executor.initial_state(
        {
            "resume": "Python FastAPI",
            "skills": profile.candidate.skills,
            "locations": profile.candidate.locations,
            "experience_years": 3,
            "exclude_terms": profile.search.exclude_terms,
            "match_threshold": 70,
        }
    )
    final = asyncio.run(executor.run(state))
    assert cfg.csv_path.is_file()
    assert "JobBot complete" in final.messages[-1].content
    assert any(r.skill == "send_digest" and r.ok for r in final.tool_results)
