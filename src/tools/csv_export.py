"""Append-only CSV of jobs that passed matching in a run."""

from __future__ import annotations

import csv
from pathlib import Path

from tools.sqlite_store import StoredJob

CSV_FIELDS = [
    "job_hash",
    "company",
    "title",
    "location",
    "url",
    "match_score",
    "reason",
    "source",
    "posted_at",
    "seen_at",
]


def append_jobs(path: Path, jobs: list[StoredJob]) -> Path:
    """Create the CSV with a header if needed, then append rows.

    Raises:
        OSError: path not writable.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not path.exists()
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        if new_file:
            writer.writeheader()
        for job in jobs:
            writer.writerow(job.model_dump())
    return path
