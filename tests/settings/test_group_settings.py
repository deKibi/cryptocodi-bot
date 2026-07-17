# tests/settings/test_group_settings.py

# Standard Libraries
import sqlite3
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


def test_save_group_settings_persists_feature_flags_and_limit_overrides(
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
        max_crypto_pairs_per_message_is_overridden=True,
        max_time_matches_per_message_is_overridden=True,
    )

    assert group_settings.save_group_settings(-100, saved_settings)

    group_settings._group_settings_cache.clear()
    assert group_settings.get_group_settings(-100) == saved_settings


def test_save_group_settings_rejects_unsupported_limit_override(
    tmp_path: Path,
) -> None:
    storage = GroupSettingsStorage(tmp_path / "settings.sqlite3")
    invalid_settings = GroupSettings(max_crypto_pairs_per_message=2)

    with pytest.raises(ValueError):
        storage.save_settings(-100, invalid_settings)


def test_reset_crypto_limit_uses_default_without_changing_time_override(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _use_temporary_storage(monkeypatch, tmp_path / "settings.sqlite3")
    monkeypatch.setattr(
        group_settings,
        "MAX_CRYPTO_PAIRS_PER_MESSAGE",
        10,
    )
    monkeypatch.setattr(
        group_settings,
        "MAX_TIME_MATCHES_PER_MESSAGE",
        8,
    )

    group_settings.update_group_setting(
        -100,
        "max_crypto_pairs_per_message",
        1,
    )
    group_settings.update_group_setting(
        -100,
        "max_time_matches_per_message",
        3,
    )
    updated_settings = group_settings.update_group_setting(
        -100,
        "max_crypto_pairs_per_message",
        None,
    )

    assert updated_settings == GroupSettings(
        max_crypto_pairs_per_message=10,
        max_time_matches_per_message=3,
        max_time_matches_per_message_is_overridden=True,
    )


def test_feature_toggle_does_not_remove_limit_overrides(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _use_temporary_storage(monkeypatch, tmp_path / "settings.sqlite3")
    group_settings.update_group_setting(
        -100,
        "max_crypto_pairs_per_message",
        1,
    )
    group_settings.update_group_setting(
        -100,
        "max_time_matches_per_message",
        3,
    )

    updated_settings = group_settings.update_group_setting(
        -100,
        "calculator_enabled",
        False,
    )

    assert updated_settings == GroupSettings(
        calculator_enabled=False,
        max_crypto_pairs_per_message=1,
        max_time_matches_per_message=3,
        max_crypto_pairs_per_message_is_overridden=True,
        max_time_matches_per_message_is_overridden=True,
    )


def test_limit_override_equal_to_default_remains_explicit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _use_temporary_storage(monkeypatch, tmp_path / "settings.sqlite3")
    monkeypatch.setattr(
        group_settings,
        "MAX_CRYPTO_PAIRS_PER_MESSAGE",
        5,
    )

    updated_settings = group_settings.update_group_setting(
        -100,
        "max_crypto_pairs_per_message",
        5,
    )

    assert updated_settings == GroupSettings(
        max_crypto_pairs_per_message=5,
        max_crypto_pairs_per_message_is_overridden=True,
    )


def test_default_limit_removes_explicit_override(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _use_temporary_storage(monkeypatch, tmp_path / "settings.sqlite3")
    group_settings.update_group_setting(
        -100,
        "max_time_matches_per_message",
        5,
    )

    updated_settings = group_settings.update_group_setting(
        -100,
        "max_time_matches_per_message",
        None,
    )

    assert updated_settings == GroupSettings()


def test_storage_uses_separate_not_null_limit_override_table(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "settings.sqlite3"

    GroupSettingsStorage(database_path)

    with sqlite3.connect(database_path) as connection:
        feature_columns = {
            str(row[1]): int(row[3])
            for row in connection.execute(
                "PRAGMA table_info(group_feature_settings)"
            ).fetchall()
        }
        override_columns = {
            str(row[1]): int(row[3])
            for row in connection.execute(
                "PRAGMA table_info(group_limit_overrides)"
            ).fetchall()
        }

    assert "max_crypto_pairs_per_message" not in feature_columns
    assert "max_time_matches_per_message" not in feature_columns
    assert override_columns["limit_value"] == 1
