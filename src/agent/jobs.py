"""Job identity hash and posting window filters."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta, timezone
from html import unescape
from typing import Any

from pydantic import BaseModel, Field, computed_field

_TAG_RE = re.compile(r"<[^>]+>")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def job_hash(company: str, title: str, location: str) -> str:
    """MD5 of lowercase(Company_Name + Job_Title + Location)."""
    material = f"{company}{title}{location}".lower()
    return hashlib.md5(material.encode("utf-8"), usedforsecurity=False).hexdigest()


def strip_html(text: str) -> str:
    return unescape(_TAG_RE.sub(" ", text))


def parse_datetime(value: Any) -> datetime | None:
    """Parse ISO-8601, epoch seconds, or epoch milliseconds to UTC."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        ts = float(value)
        if ts > 10_000_000_000:
            ts = ts / 1000.0
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(raw)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    return None


def within_max_age(posted_at: datetime, *, max_age_hours: int, now: datetime | None = None) -> bool:
    current = now or utcnow()
    return posted_at >= current - timedelta(hours=max_age_hours)


def contains_excluded(text: str, terms: list[str]) -> bool:
    haystack = text.lower()
    return any(term.lower() in haystack for term in terms if term.strip())


class JobPosting(BaseModel):
    source: str
    company: str
    title: str
    location: str
    url: str
    posted_at: datetime
    description: str = ""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def job_hash(self) -> str:
        return job_hash(self.company, self.title, self.location)

    def blob(self) -> str:
        return f"{self.title}\n{self.company}\n{self.location}\n{self.description}"


class MatchedJob(BaseModel):
    posting: JobPosting
    match_score: int = Field(ge=0, le=100)
    reason: str
