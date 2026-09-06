from agent.memory import WorkingMemoryGuard


def test_working_memory__drops_raw_descriptions_when_huge() -> None:
    guard = WorkingMemoryGuard()
    data = {"raw_descriptions": "x" * 500_000, "skills": ["Python"]}
    out = guard.apply(data)
    assert "raw_descriptions" not in out
    assert out["skills"] == ["Python"]
