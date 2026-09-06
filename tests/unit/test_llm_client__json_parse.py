from agent.llm_client import parse_json_object
from agent.errors import LlmError
import pytest


def test_parse_json_object__fenced_json__extracts_object() -> None:
    raw = "```json\n{\"match_score\": 81, \"reason\": \"Python listed\"}\n```"
    assert parse_json_object(raw)["match_score"] == 81


def test_parse_json_object__no_object__raises_llm_error() -> None:
    with pytest.raises(LlmError):
        parse_json_object("sorry I cannot")
