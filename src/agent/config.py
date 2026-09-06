"""Single typed config object. All env access goes through `load_config`."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from agent.errors import ConfigError

EnvName = Literal["local", "staging", "production"]
MatcherBackend = Literal["llm", "heuristic"]
LlmProvider = Literal["gemini", "groq"]


def _load_dotenv(path: Path) -> None:
    """Load KEY=VALUE pairs from `.env` into os.environ if the file exists.

    Does not override variables already set. Missing file is a no-op.
    """
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _optional_env(name: str) -> str | None:
    value = os.environ.get(name)
    if value is None or value.strip() == "":
        return None
    return value.strip()


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw.strip())
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer, got {raw!r}") from exc


def _float_env(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw.strip())
    except ValueError as exc:
        raise ConfigError(f"{name} must be a float, got {raw!r}") from exc


def _bool_env(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ConfigError(f"{name} must be a boolean, got {raw!r}")


class Budget(BaseModel):
    """Hard caps enforced by the executor every iteration."""

    max_steps: int = Field(ge=1)
    max_wall_clock_s: float = Field(gt=0)
    max_cost_usd: float = Field(ge=0)


class AppConfig(BaseModel):
    """Process-wide JobBot configuration. Load once via `load_config`."""

    env: EnvName
    matcher_backend: MatcherBackend
    llm_provider: LlmProvider
    llm_model: str
    llm_api_key: str | None
    send_email: bool
    auto_confirm_email: bool
    smtp_host: str
    smtp_port: int = Field(ge=1, le=65535)
    smtp_user: str | None
    smtp_password: str | None
    digest_to: str | None
    sqlite_path: Path
    csv_path: Path
    profile_path: Path
    resume_override: Path | None
    budget: Budget
    granted_permissions: list[str]
    allowed_skills: list[str]

    @model_validator(mode="after")
    def _fail_closed_on_missing_secrets(self) -> AppConfig:
        if self.matcher_backend == "llm" and not self.llm_api_key:
            raise ConfigError(
                "JOBBOT_MATCHER_BACKEND=llm requires JOBBOT_LLM_API_KEY "
                "(free Gemini or Groq key). Set matcher to heuristic to run offline."
            )
        if self.send_email:
            missing: list[str] = []
            if not self.smtp_user:
                missing.append("JOBBOT_SMTP_USER")
            if not self.smtp_password:
                missing.append("JOBBOT_SMTP_PASSWORD")
            if not self.digest_to:
                missing.append("JOBBOT_DIGEST_TO")
            if missing:
                raise ConfigError(
                    "JOBBOT_SEND_EMAIL=true requires: " + ", ".join(missing)
                )
        return self


def load_config(*, repo_root: Path | None = None, dotenv_path: Path | None = None) -> AppConfig:
    """Load `.env` then environment into a validated `AppConfig`.

    Raises:
        ConfigError: missing/invalid env or LLM/SMTP required fields absent.
    """
    root = repo_root or Path.cwd()
    _load_dotenv(dotenv_path or root / ".env")

    env_raw = os.environ.get("JOBBOT_ENV", "local").strip().lower()
    if env_raw not in {"local", "staging", "production"}:
        raise ConfigError(f"JOBBOT_ENV must be local|staging|production, got {env_raw!r}")

    matcher = os.environ.get("JOBBOT_MATCHER_BACKEND", "llm").strip().lower()
    if matcher not in {"llm", "heuristic"}:
        raise ConfigError(f"JOBBOT_MATCHER_BACKEND must be llm|heuristic, got {matcher!r}")

    provider = os.environ.get("JOBBOT_LLM_PROVIDER", "gemini").strip().lower()
    if provider not in {"gemini", "groq"}:
        raise ConfigError(f"JOBBOT_LLM_PROVIDER must be gemini|groq, got {provider!r}")

    default_model = "gemini-2.0-flash" if provider == "gemini" else "llama-3.1-8b-instant"

    sqlite_path = Path(_optional_env("JOBBOT_SQLITE_PATH") or "data/jobs.sqlite")
    csv_path = Path(_optional_env("JOBBOT_CSV_PATH") or "data/jobs.csv")
    profile_path = Path(_optional_env("JOBBOT_PROFILE_PATH") or "JobBot/profile.yaml")
    resume_raw = _optional_env("JOBBOT_RESUME_PATH")

    if not sqlite_path.is_absolute():
        sqlite_path = root / sqlite_path
    if not csv_path.is_absolute():
        csv_path = root / csv_path
    if not profile_path.is_absolute():
        profile_path = root / profile_path
    resume_path = (root / resume_raw) if resume_raw and not Path(resume_raw).is_absolute() else (
        Path(resume_raw) if resume_raw else None
    )

    send_email = _bool_env("JOBBOT_SEND_EMAIL", False)
    return AppConfig(
        env=env_raw,  # type: ignore[arg-type]
        matcher_backend=matcher,  # type: ignore[arg-type]
        llm_provider=provider,  # type: ignore[arg-type]
        llm_model=_optional_env("JOBBOT_LLM_MODEL") or default_model,
        llm_api_key=_optional_env("JOBBOT_LLM_API_KEY"),
        send_email=send_email,
        auto_confirm_email=_bool_env("JOBBOT_AUTO_CONFIRM_EMAIL", True),
        smtp_host=_optional_env("JOBBOT_SMTP_HOST") or "smtp.office365.com",
        smtp_port=_int_env("JOBBOT_SMTP_PORT", 587),
        smtp_user=_optional_env("JOBBOT_SMTP_USER"),
        smtp_password=_optional_env("JOBBOT_SMTP_PASSWORD"),
        digest_to=_optional_env("JOBBOT_DIGEST_TO"),
        sqlite_path=sqlite_path,
        csv_path=csv_path,
        profile_path=profile_path,
        resume_override=resume_path,
        budget=Budget(
            max_steps=_int_env("JOBBOT_MAX_STEPS", 12),
            max_wall_clock_s=_float_env("JOBBOT_MAX_WALL_CLOCK_S", 240.0),
            max_cost_usd=_float_env("JOBBOT_MAX_COST_USD", 0.0),
        ),
        granted_permissions=[
            "network",
            "filesystem:read",
            "filesystem:write",
            "send_email",
        ],
        allowed_skills=["export_csv", "ingest_jobs", "match_jobs", "send_digest"],
    )
