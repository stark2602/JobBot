from agent.cli import main
import pytest


def test_cli__help__exits_zero() -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
