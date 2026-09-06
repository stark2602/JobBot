from tests.eval.run_eval import score_case


def test_eval_scorer__empty_state_routes_ingest() -> None:
    case = {
        "input": {"tool_results": []},
        "expected": {"kind": "call_skill", "skill": "ingest_jobs"},
    }
    assert score_case(case) is True
