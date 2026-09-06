"""Outlook / Microsoft 365 SMTP digest sender."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Protocol

from agent.errors import SkillUpstreamError


class SmtpTransport(Protocol):
    def send(self, message: EmailMessage, *, host: str, port: int, user: str, password: str) -> None:
        ...


class StdlibSmtp:
    def send(self, message: EmailMessage, *, host: str, port: int, user: str, password: str) -> None:
        try:
            with smtplib.SMTP(host, port, timeout=30) as client:
                client.ehlo()
                client.starttls()
                client.login(user, password)
                client.send_message(message)
        except (OSError, smtplib.SMTPException) as exc:
            raise SkillUpstreamError(f"SMTP send failed: {exc}") from exc


def build_message(*, sender: str, to: str, subject: str, html: str, csv_bytes: bytes | None) -> EmailMessage:
    message = EmailMessage()
    message["From"] = sender
    message["To"] = to
    message["Subject"] = subject
    message.set_content("HTML digest attached; open in Outlook to view formatted jobs.")
    message.add_alternative(html, subtype="html")
    if csv_bytes is not None:
        message.add_attachment(
            csv_bytes,
            maintype="text",
            subtype="csv",
            filename="jobs.csv",
        )
    return message
