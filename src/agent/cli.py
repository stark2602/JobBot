"""JobBot entry: load config/profile, run the executor, print the final summary."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from agent.config import AppConfig, load_config
from agent.executor import Executor
from agent.profile import load_profile, load_resume
from tools.sqlite_store import JobStore


async def run_jobbot(config: AppConfig, *, repo_root: Path) -> str:
    profile = load_profile(config.profile_path)
    resume = load_resume(profile, repo_root=repo_root, override=config.resume_override)
    store = JobStore(config.sqlite_path)
    executor = Executor(config, extras={"profile": profile, "store": store})
    state = executor.initial_state(
        {
            "resume": resume,
            "skills": profile.candidate.skills,
            "locations": profile.candidate.locations,
            "experience_years": profile.candidate.experience_years,
            "exclude_terms": profile.search.exclude_terms,
            "match_threshold": profile.search.match_threshold,
        }
    )
    final = await executor.run(state)
    if not final.messages:
        return json.dumps({"trace_id": final.trace_id, "summary": "no messages"})
    return final.messages[-1].content


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Job Search & Match bot once.")
    parser.add_argument("--root", default=".", help="Repository root (profile/resume paths).")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    config = load_config(repo_root=root)
    summary = asyncio.run(run_jobbot(config, repo_root=root))
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
