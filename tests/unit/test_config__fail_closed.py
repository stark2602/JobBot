from pathlib import Path

import pytest

from agent.config import ConfigError, load_config


def test_load_config__llm_without_key__raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JOBBOT_MATCHER_BACKEND", "llm")
    monkeypatch.delenv("JOBBOT_LLM_API_KEY", raising=False)
    monkeypatch.setenv("JOBBOT_SEND_EMAIL", "false")
    with pytest.raises(ConfigError, match="JOBBOT_LLM_API_KEY"):
        load_config(repo_root=tmp_path, dotenv_path=tmp_path / "missing.env")


def test_load_config__heuristic_ok(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JOBBOT_MATCHER_BACKEND", "heuristic")
    monkeypatch.setenv("JOBBOT_SEND_EMAIL", "false")
    cfg = load_config(repo_root=tmp_path, dotenv_path=tmp_path / "missing.env")
    assert cfg.matcher_backend == "heuristic"
    assert cfg.sqlite_path == tmp_path / "data" / "jobs.sqlite"
