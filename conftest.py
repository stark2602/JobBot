"""Test helpers exposed at repo root so test modules can import `from conftest import make_config`."""

from tests.conftest import make_config

__all__ = ["make_config"]
