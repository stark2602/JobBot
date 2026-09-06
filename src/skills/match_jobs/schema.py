from pydantic import BaseModel, Field

from agent.jobs import JobPosting, MatchedJob


class MatchInput(BaseModel):
    jobs: list[JobPosting]
    resume: str
    skills: list[str]
    locations: list[str]
    experience_years: float
    exclude_terms: list[str]
    match_threshold: int = 70


class MatchOutput(BaseModel):
    matched: list[MatchedJob] = Field(default_factory=list)
    skipped_hashes: list[str] = Field(default_factory=list)
    dropped_below_threshold: int = 0
    excluded: int = 0
