# tests/settings/test_config_message_limits.py

# Third-party Libraries
import pytest

# Custom Modules
from config import get_positive_int_env_or_default


def test_positive_int_env_or_default_accepts_positive_integer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TEST_LIMIT", "10")

    assert get_positive_int_env_or_default("TEST_LIMIT", 5) == 10


def test_positive_int_env_or_default_falls_back_for_invalid_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TEST_LIMIT", "abc")

    assert get_positive_int_env_or_default("TEST_LIMIT", 5) == 5


def test_positive_int_env_or_default_falls_back_for_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TEST_LIMIT", "0")

    assert get_positive_int_env_or_default("TEST_LIMIT", 5) == 5
