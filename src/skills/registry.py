"""Alphabetical skill registry. Single registration point."""

from __future__ import annotations

from skills.export_csv.handler import SKILL as export_csv
from skills.ingest_jobs.handler import SKILL as ingest_jobs
from skills.manifest import SkillManifest
from skills.match_jobs.handler import SKILL as match_jobs
from skills.send_digest.handler import SKILL as send_digest

SKILLS: dict[str, SkillManifest] = {
    skill.name: skill
    for skill in (export_csv, ingest_jobs, match_jobs, send_digest)
}


def get_skill(name: str) -> SkillManifest:
    """Look up a registered skill.

    Raises:
        KeyError: unknown name.
    """
    return SKILLS[name]
