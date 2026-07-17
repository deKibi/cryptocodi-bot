# tests/settings/test_group_settings.py

# Standard Libraries
from pathlib import Path

# Third-party Libraries
import pytest

# Custom Modules
from telegram_bot.settings import group_settings
from telegram_bot.settings.group_settings import (
    GroupSettings,
    GroupSettingsStorage,
)


def _use_temporary_storage(
    monkeypatch: pytest.MonkeyPatch,
    database_path: Path,
) -> None:
    monkeypatch.setattr(
        group_settings,
        "_group_settings_storage",
        GroupSettingsStorage(database_path),
    )
    group_settings._group_settings_cache.clear()


def test_get_group_settings_returns_defaults_when_absent(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _use_temporary_storage(monkeypatch, tmp_path / "settings.sqlite3")

    settings = group_settings.get_group_settings(-100)

    assert settings == group_settings.get_default_group_settings()


def test_save_group_settings_persists_values(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _use_temporary_storage(monkeypatch, tmp_path / "settings.sqlite3")
    saved_settings = GroupSettings(
        crypto_converter_enabled=False,
        calculator_enabled=False,
        time_converter_enabled=True,
        max_crypto_pairs_per_message=3,
        max_time_matches_per_message=1,
    )

    assert group_settings.save_group_settings(-100, saved_settings)

    group_settings._group_settings_cache.clear()
    assert group_settings.get_group_settings(-100) == saved_settings


def test_save_group_settings_rejects_unsupported_limits(
    tmp_path: Path,
) -> None:
    storage = GroupSettingsStorage(tmp_path / "settings.sqlite3")
    invalid_settings = GroupSettings(
        max_crypto_pairs_per_message=2,
    )

    with pytest.raises(ValueError):
        storage.save_settings(-100, invalid_settings)
