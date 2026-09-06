"""Deterministic JobBot planner: ingest → match → csv → digest → final."""

from __future__ import annotations

from agent.state import AgentState, Decision, ToolResult


def _latest(state: AgentState, skill: str) -> ToolResult | None:
    for result in reversed(state.tool_results):
        if result.skill == skill:
            return result
    return None


def plan(state: AgentState) -> Decision:
    """Pure function of state. No I/O, no globals.

    Raises:
        None — invalid routing is a typed Decision, not an exception.
    """
    ingest = _latest(state, "ingest_jobs")
    if ingest is None:
        return Decision(kind="call_skill", skill="ingest_jobs", arguments={})
    if not ingest.ok:
        return Decision(kind="final", content=f"ingest_jobs failed: {ingest.error}")

    match = _latest(state, "match_jobs")
    if match is None:
        mem = state.working_memory
        return Decision(
            kind="call_skill",
            skill="match_jobs",
            arguments={
                "jobs": ingest.payload.get("jobs", []),
                "resume": mem.get("resume", ""),
                "skills": mem.get("skills", []),
                "locations": mem.get("locations", []),
                "experience_years": mem.get("experience_years", 0),
                "exclude_terms": mem.get("exclude_terms", []),
                "match_threshold": mem.get("match_threshold", 70),
            },
        )
    if not match.ok:
        return Decision(kind="final", content=f"match_jobs failed: {match.error}")

    export = _latest(state, "export_csv")
    if export is None:
        return Decision(
            kind="call_skill",
            skill="export_csv",
            arguments={"matched": match.payload.get("matched", [])},
        )
    if not export.ok:
        return Decision(kind="final", content=f"export_csv failed: {export.error}")

    digest = _latest(state, "send_digest")
    if digest is None:
        return Decision(
            kind="call_skill",
            skill="send_digest",
            arguments={
                "matched": match.payload.get("matched", []),
                "csv_path": export.payload.get("csv_path", ""),
            },
        )
    if not digest.ok:
        return Decision(kind="final", content=f"send_digest failed: {digest.error}")

    top = digest.payload.get("top_count", 0)
    good = digest.payload.get("good_count", 0)
    sent = digest.payload.get("sent", False)
    skipped = digest.payload.get("skipped_reason")
    return Decision(
        kind="final",
        content=(
            f"JobBot complete. csv={export.payload.get('csv_path')} "
            f"rows={export.payload.get('rows_written')} top={top} good={good} "
            f"email_sent={sent} skip={skipped}"
        ),
    )
