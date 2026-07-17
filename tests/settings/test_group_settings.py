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
        max_crypto_pairs_per_message_override=3,
        max_time_matches_per_message_override=1,
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
        max_crypto_pairs_per_message_override=2,
    )

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
        max_crypto_pairs_per_message_override=None,
        max_time_matches_per_message_override=3,
    )


def test_storage_migrates_old_not_null_limit_schema(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "settings.sqlite3"

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE group_feature_settings (
                chat_id INTEGER PRIMARY KEY,
                crypto_converter_enabled INTEGER NOT NULL CHECK (
                    crypto_converter_enabled IN (0, 1)
                ),
                calculator_enabled INTEGER NOT NULL CHECK (
                    calculator_enabled IN (0, 1)
                ),
                time_converter_enabled INTEGER NOT NULL CHECK (
                    time_converter_enabled IN (0, 1)
                ),
                max_crypto_pairs_per_message INTEGER NOT NULL CHECK (
                    max_crypto_pairs_per_message IN (1, 3, 5)
                ),
                max_time_matches_per_message INTEGER NOT NULL CHECK (
                    max_time_matches_per_message IN (1, 3, 5)
                )
            )
            """
        )
        connection.execute(
            """
            INSERT INTO group_feature_settings (
                chat_id,
                crypto_converter_enabled,
                calculator_enabled,
                time_converter_enabled,
                max_crypto_pairs_per_message,
                max_time_matches_per_message
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (-100, 1, 0, 1, 3, 5),
        )

    storage = GroupSettingsStorage(database_path)
    settings = storage.get_settings(-100)

    assert settings == GroupSettings(
        crypto_converter_enabled=True,
        calculator_enabled=False,
        time_converter_enabled=True,
        max_crypto_pairs_per_message=3,
        max_time_matches_per_message=5,
        max_crypto_pairs_per_message_override=3,
        max_time_matches_per_message_override=5,
    )

    with sqlite3.connect(database_path) as connection:
        columns = {
            str(row[1]): int(row[3])
            for row in connection.execute(
                "PRAGMA table_info(group_feature_settings)"
            ).fetchall()
        }

    assert columns["max_crypto_pairs_per_message"] == 0
    assert columns["max_time_matches_per_message"] == 0
