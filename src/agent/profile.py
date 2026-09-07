"""Candidate search profile loaded from YAML. Missing file fails loudly."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator


class WorkdayBoard(BaseModel):
    """Public Workday CXS job search endpoint pieces."""

    host: str
    tenant: str
    site: str
    company: str


class Sources(BaseModel):
    greenhouse: list[str] = Field(default_factory=list)
    lever: list[str] = Field(default_factory=list)
    workday: list[WorkdayBoard] = Field(default_factory=list)
    generic_web: list[str] = Field(default_factory=list)


class Candidate(BaseModel):
    skills: list[str]
    locations: list[str]
    experience_years: float = Field(ge=0)
    resume_path: str

    @field_validator("skills", "locations")
    @classmethod
    def _non_empty(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("must contain at least one entry")
        return cleaned


class SearchRules(BaseModel):
    max_age_hours: int = Field(default=120, ge=8, le=120)
    match_threshold: int = Field(default=70, ge=0, le=100)
    email_min_score: int = Field(default=75, ge=0, le=100)
    exclude_terms: list[str] = Field(
        default_factory=lambda: ["Staffing Agency", "C2C", "Security Clearance", "Unpaid"]
    )


class JobProfile(BaseModel):
    candidate: Candidate
    search: SearchRules = Field(default_factory=SearchRules)
    sources: Sources


def load_profile(path: Path) -> JobProfile:
    """Parse and validate `JobBot/profile.yaml`.

    Raises:
        FileNotFoundError: path missing.
        ValueError: YAML is not a mapping or fails JobProfile validation.
    """
    if not path.is_file():
        raise FileNotFoundError(f"Profile YAML not found: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Profile YAML must be a mapping: {path}")
    return JobProfile.model_validate(raw)


def load_resume(profile: JobProfile, *, repo_root: Path, override: Path | None) -> str:
    path = override or (repo_root / profile.candidate.resume_path)
    if not path.is_file():
        raise FileNotFoundError(f"Resume file not found: {path}")
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"Resume file is empty: {path}")
    return text
