import asyncio
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

from agent.jobs import JobPosting, MatchedJob
from conftest import make_config
from skills.manifest import SkillContext
from skills.send_digest.handler import handle
from skills.send_digest.schema import DigestInput


class RecordingSmtp:
    def __init__(self) -> None:
        self.sent: list[EmailMessage] = []

    def send(self, message: EmailMessage, *, host: str, port: int, user: str, password: str) -> None:
        _ = host, port, user, password
        self.sent.append(message)


def _matched(score: int) -> MatchedJob:
    posting = JobPosting(
        source="greenhouse",
        company="Acme",
        title="Python Engineer",
        location="Remote",
        url="https://boards.greenhouse.io/acme/jobs/1",
        posted_at=datetime.now(timezone.utc),
        description="Python",
    )
    return MatchedJob(posting=posting, match_score=score, reason="skills overlap")


def test_send_digest__send_email_false__skips(tmp_path: Path) -> None:
    cfg = make_config(tmp_path, send_email=False)
    ctx = SkillContext(
        deadline=datetime.now(timezone.utc).replace(year=2099),
        trace_id="t",
        granted_permissions=cfg.granted_permissions,
        config=cfg,
        extras={},
    )
    out = asyncio.run(handle(DigestInput(matched=[_matched(95)]), ctx))
    assert out.sent is False
    assert out.skipped_reason == "JOBBOT_SEND_EMAIL=false"
    assert out.top_count == 1


def test_send_digest__smtp_once_for_many_jobs(tmp_path: Path) -> None:
    smtp = RecordingSmtp()
    cfg = make_config(
        tmp_path,
        send_email=True,
        smtp_user="bot@outlook.com",
        smtp_password="app-password",
        digest_to="me@outlook.com",
    )
    ctx = SkillContext(
        deadline=datetime.now(timezone.utc).replace(year=2099),
        trace_id="t",
        granted_permissions=cfg.granted_permissions,
        config=cfg,
        extras={"smtp": smtp},
    )
    out = asyncio.run(handle(DigestInput(matched=[_matched(95), _matched(80)]), ctx))
    assert out.sent is True
    assert len(smtp.sent) == 1
