# Memory

- Short-term: `AgentState.working_memory` (resume, skills, thresholds). Evicted by `WorkingMemoryGuard` at 200KB (`raw_descriptions` dropped first).
- Long-term: SQLite `jobs` table keyed by MD5 hash (`tools/sqlite_store.py`). Writes happen only in `export_csv` after a match.
