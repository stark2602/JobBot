from datetime import datetime, timezone

from agent.jobs import contains_excluded, job_hash, parse_datetime, within_max_age


def test_job_hash__concat_then_lowercase__stable_md5() -> None:
    first = job_hash("Acme", "Engineer", "Remote")
    assert first == job_hash("ACME", "ENGINEER", "REMOTE")
    assert len(first) == 32


def test_contains_excluded__c2c_in_description__true() -> None:
    assert contains_excluded("This is a C2C contract", ["C2C", "Unpaid"]) is True


def test_contains_excluded__clean_text__false() -> None:
    assert contains_excluded("Staff software engineer", ["Staffing Agency"]) is False


def test_within_max_age__old_posting__false() -> None:
    now = datetime(2026, 9, 5, 12, tzinfo=timezone.utc)
    posted = datetime(2026, 9, 4, 12, tzinfo=timezone.utc)
    assert within_max_age(posted, max_age_hours=12, now=now) is False


def test_parse_datetime__epoch_ms__utc() -> None:
    parsed = parse_datetime(1_725_000_000_000)
    assert parsed is not None
    assert parsed.tzinfo is not None
