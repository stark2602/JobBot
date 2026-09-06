from datetime import datetime, timezone

from agent.jobs import JobPosting
from agent.planner import plan
from agent.state import AgentState, BudgetRemaining, ToolResult


def _state(*results: ToolResult) -> AgentState:
    return AgentState(
        tool_results=results,
        working_memory={
            "resume": "Python FastAPI",
            "skills": ["Python"],
            "locations": ["Remote"],
            "experience_years": 3,
            "exclude_terms": ["C2C"],
            "match_threshold": 70,
        },
        budget=BudgetRemaining(steps=8, wall_clock_s=60, cost_usd=0),
    )


def test_planner__no_results__ingest() -> None:
    decision = plan(_state())
    assert decision.kind == "call_skill"
    assert decision.skill == "ingest_jobs"


def test_planner__after_ingest__match() -> None:
    posting = JobPosting(
        source="greenhouse",
        company="Acme",
        title="Python Engineer",
        location="Remote",
        url="https://boards.greenhouse.io/acme/jobs/1",
        posted_at=datetime.now(timezone.utc),
        description="Python FastAPI",
    )
    ingest = ToolResult(
        skill="ingest_jobs",
        ok=True,
        payload={"jobs": [posting.model_dump(mode="json")], "source_errors": []},
    )
    decision = plan(_state(ingest))
    assert decision.skill == "match_jobs"
    assert decision.arguments["jobs"][0]["title"] == "Python Engineer"


def test_planner__failed_ingest__final() -> None:
    ingest = ToolResult(skill="ingest_jobs", ok=False, payload={}, error="boom")
    decision = plan(_state(ingest))
    assert decision.kind == "final"
    assert "boom" in (decision.content or "")
