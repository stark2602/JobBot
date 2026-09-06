from pathlib import Path

from tools.csv_export import append_jobs
from tools.sqlite_store import JobStore, StoredJob


def test_job_store__insert_then_exists(tmp_path: Path) -> None:
    store = JobStore(tmp_path / "jobs.sqlite")
    row = StoredJob(
        job_hash="abc",
        company="Acme",
        title="Eng",
        location="Remote",
        url="https://example.test/jobs/1",
        match_score=90,
        reason="fit",
        source="greenhouse",
        posted_at="2026-09-05T00:00:00+00:00",
        seen_at="2026-09-05T01:00:00Z",
    )
    assert store.exists("abc") is False
    store.insert(row)
    assert store.exists("abc") is True
    store.insert(row)
    assert store.exists("abc") is True


def test_append_jobs__writes_header_once(tmp_path: Path) -> None:
    path = tmp_path / "jobs.csv"
    row = StoredJob(
        job_hash="abc",
        company="Acme",
        title="Eng",
        location="Remote",
        url="https://example.test/jobs/1",
        match_score=90,
        reason="fit",
        source="greenhouse",
        posted_at="2026-09-05T00:00:00+00:00",
        seen_at="2026-09-05T01:00:00Z",
    )
    append_jobs(path, [row])
    append_jobs(path, [row])
    text = path.read_text(encoding="utf-8")
    assert text.count("job_hash") == 1
    assert text.count("abc") == 2
