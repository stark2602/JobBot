from pydantic import BaseModel, Field

from agent.jobs import MatchedJob


class ExportInput(BaseModel):
    matched: list[MatchedJob]


class ExportOutput(BaseModel):
    csv_path: str
    rows_written: int = Field(ge=0)
    persisted: int = Field(ge=0)
