"""Shared AppConfig factory for unit tests (no real secrets)."""

from __future__ import annotations

from pathlib import Path

from agent.config import AppConfig, Budget


def make_config(tmp_path: Path, **overrides: object) -> AppConfig:
    base = dict(
        env="local",
        matcher_backend="heuristic",
        llm_provider="gemini",
        llm_model="gemini-2.0-flash",
        llm_api_key=None,
        send_email=False,
        auto_confirm_email=True,
        smtp_host="smtp.office365.com",
        smtp_port=587,
        smtp_user=None,
        smtp_password=None,
        digest_to=None,
        sqlite_path=tmp_path / "jobs.sqlite",
        csv_path=tmp_path / "jobs.csv",
        profile_path=tmp_path / "profile.yaml",
        resume_override=None,
        budget=Budget(max_steps=12, max_wall_clock_s=60, max_cost_usd=0),
        granted_permissions=["network", "filesystem:read", "filesystem:write", "send_email"],
        allowed_skills=["export_csv", "ingest_jobs", "match_jobs", "send_digest"],
    )
    base.update(overrides)
    return AppConfig.model_validate(base)
