"""Outlook SMTP digest. Side effect; bot config sets auto_confirm_email=true for cron."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from agent.errors import SkillPermissionDenied, SkillTimeoutError
from skills.manifest import CostEstimate, SkillContext, SkillManifest
from skills.send_digest.html import render_html, split_tiers
from skills.send_digest.schema import DigestInput, DigestOutput
from tools.smtp_mailer import SmtpTransport, StdlibSmtp, build_message


async def handle(inp: DigestInput, ctx: SkillContext) -> DigestOutput:
    if datetime.now(timezone.utc) >= ctx.deadline:
        raise SkillTimeoutError("send_digest deadline exceeded")
    top, good = split_tiers(inp.matched)
    subject = f"JobBot digest: {len(top)} top, {len(good)} good fits"
    if not ctx.config.send_email:
        return DigestOutput(
            sent=False,
            skipped_reason="JOBBOT_SEND_EMAIL=false",
            top_count=len(top),
            good_count=len(good),
            subject=subject,
        )
    if not ctx.config.auto_confirm_email:
        return DigestOutput(
            sent=False,
            skipped_reason="auto_confirm_email is false; refusing irreversible send",
            top_count=len(top),
            good_count=len(good),
            subject=subject,
        )
    if "send_email" not in ctx.granted_permissions:
        raise SkillPermissionDenied("send_digest requires send_email")
    if not top and not good:
        return DigestOutput(
            sent=False,
            skipped_reason="no jobs at email thresholds",
            top_count=0,
            good_count=0,
            subject=subject,
        )
    html = render_html(top, good)
    csv_bytes: bytes | None = None
    if inp.csv_path:
        csv_file = Path(inp.csv_path)
        if csv_file.is_file():
            csv_bytes = csv_file.read_bytes()
    user = ctx.config.smtp_user
    password = ctx.config.smtp_password
    to = ctx.config.digest_to
    if not user or not password or not to:
        raise SkillPermissionDenied("SMTP identity incomplete despite send_email=true")
    message = build_message(
        sender=user,
        to=to,
        subject=subject,
        html=html,
        csv_bytes=csv_bytes,
    )
    transport: SmtpTransport = ctx.extras.get("smtp") or StdlibSmtp()
    transport.send(
        message,
        host=ctx.config.smtp_host,
        port=ctx.config.smtp_port,
        user=user,
        password=password,
    )
    return DigestOutput(
        sent=True,
        skipped_reason=None,
        top_count=len(top),
        good_count=len(good),
        subject=subject,
    )


SKILL = SkillManifest(
    name="send_digest",
    description=(
        "Send one Outlook HTML digest grouping Top Matches (90-100) and Good Fits (75-89) "
        "with direct ATS links. Use after export_csv. Never send one email per job."
    ),
    input_schema=DigestInput,
    output_schema=DigestOutput,
    permissions=["send_email"],
    cost_estimate=CostEstimate(usd=0.0, latency_s=2.0),
    idempotent=False,
    handler=handle,
)
