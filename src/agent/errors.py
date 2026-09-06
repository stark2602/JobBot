"""Typed failures used by the runtime and skills."""


class AgentError(Exception):
    """Base error for the agent runtime."""


class ConfigError(AgentError):
    """Missing or invalid configuration. Fail loudly; never guess."""


class BudgetExceeded(AgentError):
    """Executor hit max steps, wall-clock, or cost."""


class GuardrailBlocked(AgentError):
    """Input or output guardrail refused the action."""


class LlmError(AgentError):
    """Model adapter failure (timeout, HTTP, or invalid structured output)."""


class SkillTimeoutError(AgentError):
    """Skill aborted because Context.deadline was reached."""


class SkillPermissionDenied(AgentError):
    """Skill declared a permission the bot was not granted."""


class SkillUpstreamError(AgentError):
    """Retryable failure talking to an external system."""
