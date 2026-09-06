from datetime import datetime

from pydantic import BaseModel, Field

from agent.jobs import JobPosting


class IngestInput(BaseModel):
    """No extra fields — profile comes from SkillContext extras."""


class IngestOutput(BaseModel):
    jobs: list[JobPosting] = Field(default_factory=list)
    source_errors: list[str] = Field(default_factory=list)
    fetched_at: datetime
