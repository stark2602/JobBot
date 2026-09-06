"""Skill-layer error aliases (executor distinguishes retry vs halt)."""

from agent.errors import SkillPermissionDenied, SkillTimeoutError, SkillUpstreamError

__all__ = ["SkillPermissionDenied", "SkillTimeoutError", "SkillUpstreamError"]
