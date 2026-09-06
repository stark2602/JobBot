"""SQLite persistence for job hashes (idempotency)."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel


class StoredJob(BaseModel):
    job_hash: str
    company: str
    title: str
    location: str
    url: str
    match_score: int
    reason: str
    source: str
    posted_at: str
    seen_at: str


class JobStore:
    """Lightweight long-term memory. Fail if the parent directory cannot be created."""

    def __init__(self, path: Path) -> None:
        self._path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_hash TEXT PRIMARY KEY,
                    company TEXT NOT NULL,
                    title TEXT NOT NULL,
                    location TEXT NOT NULL,
                    url TEXT NOT NULL,
                    match_score INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    source TEXT NOT NULL,
                    posted_at TEXT NOT NULL,
                    seen_at TEXT NOT NULL
                )
                """
            )

    def exists(self, job_hash: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM jobs WHERE job_hash = ?", (job_hash,)
            ).fetchone()
        return row is not None

    def insert(self, job: StoredJob) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO jobs (
                    job_hash, company, title, location, url, match_score, reason,
                    source, posted_at, seen_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.job_hash,
                    job.company,
                    job.title,
                    job.location,
                    job.url,
                    job.match_score,
                    job.reason,
                    job.source,
                    job.posted_at,
                    job.seen_at,
                ),
            )

    def seen_at_now(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
