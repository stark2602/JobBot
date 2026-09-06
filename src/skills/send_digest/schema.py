from pydantic import BaseModel, Field

from agent.jobs import MatchedJob


class DigestInput(BaseModel):
    matched: list[MatchedJob]
    csv_path: str = ""


class DigestOutput(BaseModel):
    sent: bool
    skipped_reason: str | None = None
    top_count: int = Field(ge=0, default=0)
    good_count: int = Field(ge=0, default=0)
    subject: str = ""
