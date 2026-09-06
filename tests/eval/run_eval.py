"""Planner routing eval. No live model calls."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agent.planner import plan
from agent.state import AgentState, BudgetRemaining, ToolResult

HERE = Path(__file__).resolve().parent
DATASET = HERE / "datasets" / "job_bot.jsonl"
BASELINE = HERE / "baseline.json"


def _state_from(case: dict[str, Any]) -> AgentState:
    results = tuple(
        ToolResult.model_validate(item) for item in case.get("tool_results", [])
    )
    return AgentState(
        tool_results=results,
        working_memory=case.get(
            "working_memory",
            {
                "resume": "Python",
                "skills": ["Python"],
                "locations": ["Remote"],
                "experience_years": 3,
                "exclude_terms": ["C2C"],
                "match_threshold": 70,
            },
        ),
        budget=BudgetRemaining(steps=8, wall_clock_s=60, cost_usd=0),
    )


def score_case(case: dict[str, Any]) -> bool:
    decision = plan(_state_from(case["input"]))
    expected = case["expected"]
    if "kind" in expected and decision.kind != expected["kind"]:
        return False
    if "skill" in expected and decision.skill != expected["skill"]:
        return False
    if expected.get("skill_not") and decision.skill == expected["skill_not"]:
        return False
    return True


def main() -> int:
    rows = [
        json.loads(line) for line in DATASET.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    passed = sum(1 for row in rows if score_case(row))
    rate = passed / max(1, len(rows))
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    prior = float(baseline["job_bot"]["pass_rate"])
    report = {"passed": passed, "total": len(rows), "pass_rate": rate, "baseline": prior}
    print(json.dumps(report))
    if rate + 1e-9 < prior:
        raise SystemExit(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
