# telegram_bot/settings/group_settings.py

# Standard Libraries
import logging
import sqlite3
from collections import OrderedDict
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Optional

# Custom Modules
from config import MAX_CRYPTO_PAIRS_PER_MESSAGE, MAX_TIME_MATCHES_PER_MESSAGE
from telegram_bot.localization.language_preferences import (
    BOT_SETTINGS_DATABASE_PATH,
    GROUP_CHAT_TYPES,
    SQLITE_TIMEOUT_SECONDS,
)


# Group settings
ALLOWED_MESSAGE_LIMITS: Final[tuple[int, ...]] = (1, 3, 5)
CRYPTO_LIMIT_TYPE: Final[str] = "crypto"
TIME_LIMIT_TYPE: Final[str] = "time"
LIMIT_TYPES: Final[frozenset[str]] = frozenset(
    {CRYPTO_LIMIT_TYPE, TIME_LIMIT_TYPE}
)
MAX_CACHED_GROUP_SETTINGS: Final[int] = 10_000

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class GroupSettings:
    """Represent effective bot settings for one chat context."""

    crypto_converter_enabled: bool = True
    calculator_enabled: bool = True
    time_converter_enabled: bool = True
    max_crypto_pairs_per_message: int = MAX_CRYPTO_PAIRS_PER_MESSAGE
    max_time_matches_per_message: int = MAX_TIME_MATCHES_PER_MESSAGE


GroupSettingsCache = OrderedDict[int, GroupSettings]


class GroupSettingsStorage:
    """Persist group-specific bot settings."""

    def __init__(
        self,
        database_path: Path = BOT_SETTINGS_DATABASE_PATH,
    ) -> None:
        self._database_path = database_path
        self._initialize_database()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(
            database=self._database_path,
            timeout=SQLITE_TIMEOUT_SECONDS,
        )

    def _initialize_database(self) -> None:
        self._database_path.parent.mkdir(parents=True, exist_ok=True)

        with closing(self._connect()) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS group_feature_settings (
                    chat_id INTEGER PRIMARY KEY,
                    crypto_converter_enabled INTEGER NOT NULL CHECK (
                        crypto_converter_enabled IN (0, 1)
                    ),
                    calculator_enabled INTEGER NOT NULL CHECK (
                        calculator_enabled IN (0, 1)
                    ),
                    time_converter_enabled INTEGER NOT NULL CHECK (
                        time_converter_enabled IN (0, 1)
                    )
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS group_limit_overrides (
                    chat_id INTEGER NOT NULL,
                    limit_type TEXT NOT NULL CHECK (
                        limit_type IN ('crypto', 'time')
                    ),
                    limit_value INTEGER NOT NULL CHECK (
                        limit_value IN (1, 3, 5)
                    ),
                    PRIMARY KEY (chat_id, limit_type)
                )
                """
            )
            connection.commit()

    def get_settings(self, chat_id: int) -> Optional[GroupSettings]:
        """Return saved group settings, if present."""
        with closing(self._connect()) as connection:
            feature_row = connection.execute(
                """
                SELECT
                    crypto_converter_enabled,
                    calculator_enabled,
                    time_converter_enabled
                FROM group_feature_settings
                WHERE chat_id = ?
                """,
                (chat_id,),
            ).fetchone()
            limit_rows = connection.execute(
                """
                SELECT limit_type, limit_value
                FROM group_limit_overrides
                WHERE chat_id = ?
                """,
                (chat_id,),
            ).fetchall()

        if feature_row is None and not limit_rows:
            return None

        limit_overrides = {
            str(limit_type): int(limit_value)
            for limit_type, limit_value in limit_rows
        }

        return GroupSettings(
            crypto_converter_enabled=(
                True if feature_row is None else bool(feature_row[0])
            ),
            calculator_enabled=(
                True if feature_row is None else bool(feature_row[1])
            ),
            time_converter_enabled=(
                True if feature_row is None else bool(feature_row[2])
            ),
            max_crypto_pairs_per_message=limit_overrides.get(
                CRYPTO_LIMIT_TYPE,
                MAX_CRYPTO_PAIRS_PER_MESSAGE,
            ),
            max_time_matches_per_message=limit_overrides.get(
                TIME_LIMIT_TYPE,
                MAX_TIME_MATCHES_PER_MESSAGE,
            ),
        )

    def save_feature_settings(
        self,
        chat_id: int,
        settings: GroupSettings,
    ) -> None:
        """Insert or update boolean feature settings for a group."""
        with closing(self._connect()) as connection:
            connection.execute(
                """
                INSERT INTO group_feature_settings (
                    chat_id,
                    crypto_converter_enabled,
                    calculator_enabled,
                    time_converter_enabled
                )
                VALUES (?, ?, ?, ?)
                ON CONFLICT (chat_id)
                DO UPDATE SET
                    crypto_converter_enabled =
                        excluded.crypto_converter_enabled,
                    calculator_enabled = excluded.calculator_enabled,
                    time_converter_enabled =
                        excluded.time_converter_enabled
                """,
                (
                    chat_id,
                    int(settings.crypto_converter_enabled),
                    int(settings.calculator_enabled),
                    int(settings.time_converter_enabled),
                ),
            )
            connection.commit()

    def set_limit_override(
        self,
        chat_id: int,
        limit_type: str,
        limit_value: int,
    ) -> None:
        """Insert or update one explicit group message-limit override."""
        _validate_limit_override(limit_type, limit_value)

        with closing(self._connect()) as connection:
            connection.execute(
                """
                INSERT INTO group_limit_overrides (
                    chat_id,
                    limit_type,
                    limit_value
                )
                VALUES (?, ?, ?)
                ON CONFLICT (chat_id, limit_type)
                DO UPDATE SET limit_value = excluded.limit_value
                """,
                (chat_id, limit_type, limit_value),
            )
            connection.commit()

    def delete_limit_override(
        self,
        chat_id: int,
        limit_type: str,
    ) -> None:
        """Delete one explicit group message-limit override."""
        _validate_limit_type(limit_type)

        with closing(self._connect()) as connection:
            connection.execute(
                """
                DELETE FROM group_limit_overrides
                WHERE chat_id = ?
                  AND limit_type = ?
                """,
                (chat_id, limit_type),
            )
            connection.commit()

    def save_settings(
        self,
        chat_id: int,
        settings: GroupSettings,
    ) -> None:
        """Insert or update all supported group settings."""
        self.save_feature_settings(chat_id, settings)
        self._sync_limit_override(
            chat_id,
            CRYPTO_LIMIT_TYPE,
            settings.max_crypto_pairs_per_message,
            MAX_CRYPTO_PAIRS_PER_MESSAGE,
        )
        self._sync_limit_override(
            chat_id,
            TIME_LIMIT_TYPE,
            settings.max_time_matches_per_message,
            MAX_TIME_MATCHES_PER_MESSAGE,
        )

    def _sync_limit_override(
        self,
        chat_id: int,
        limit_type: str,
        limit_value: int,
        default_limit: int,
    ) -> None:
        if limit_value == default_limit:
            self.delete_limit_override(chat_id, limit_type)
            return

        self.set_limit_override(chat_id, limit_type, limit_value)


_group_settings_storage: Optional[GroupSettingsStorage] = None
_group_settings_cache: GroupSettingsCache = OrderedDict()


def _validate_limit_type(limit_type: str) -> None:
    if limit_type not in LIMIT_TYPES:
        raise ValueError("Unsupported limit type")


def _validate_limit_override(limit_type: str, limit_value: int) -> None:
    _validate_limit_type(limit_type)

    if limit_value not in ALLOWED_MESSAGE_LIMITS:
        raise ValueError("Unsupported message limit")


def _get_group_settings_storage() -> GroupSettingsStorage:
    global _group_settings_storage

    if _group_settings_storage is None:
        _group_settings_storage = GroupSettingsStorage()

    return _group_settings_storage


def _remember_group_settings(chat_id: int, settings: GroupSettings) -> None:
    _group_settings_cache[chat_id] = settings
    _group_settings_cache.move_to_end(chat_id)

    while len(_group_settings_cache) > MAX_CACHED_GROUP_SETTINGS:
        _group_settings_cache.popitem(last=False)


def get_default_group_settings() -> GroupSettings:
    """Return default settings matching current bot behavior."""
    return GroupSettings(
        max_crypto_pairs_per_message=MAX_CRYPTO_PAIRS_PER_MESSAGE,
        max_time_matches_per_message=MAX_TIME_MATCHES_PER_MESSAGE,
    )


def get_group_settings(chat_id: int) -> GroupSettings:
    """Return saved group settings or defaults when absent/unavailable."""
    cached_settings = _group_settings_cache.get(chat_id)

    if cached_settings is not None:
        _group_settings_cache.move_to_end(chat_id)
        return cached_settings

    try:
        stored_settings = _get_group_settings_storage().get_settings(chat_id)
    except (OSError, sqlite3.Error):
        LOGGER.exception(
            "Failed to read group settings; using defaults | chat_id=%s",
            chat_id,
        )
        return get_default_group_settings()

    if stored_settings is None:
        return get_default_group_settings()

    _remember_group_settings(chat_id, stored_settings)
    return stored_settings


def get_effective_chat_settings(
    chat_id: Optional[int],
    chat_type: object,
) -> GroupSettings:
    """Return group settings for groups and defaults for other chats."""
    if chat_type in GROUP_CHAT_TYPES and chat_id is not None:
        return get_group_settings(chat_id)

    return get_default_group_settings()


def save_group_settings(chat_id: int, settings: GroupSettings) -> bool:
    """Persist settings for a group chat."""
    try:
        _get_group_settings_storage().save_settings(chat_id, settings)
    except (OSError, sqlite3.Error, ValueError):
        LOGGER.exception(
            "Failed to save group settings | chat_id=%s",
            chat_id,
        )
        return False

    _remember_group_settings(chat_id, settings)
    return True


def _save_feature_settings(
    chat_id: int,
    settings: GroupSettings,
) -> Optional[GroupSettings]:
    try:
        _get_group_settings_storage().save_feature_settings(
            chat_id,
            settings,
        )
    except (OSError, sqlite3.Error):
        LOGGER.exception(
            "Failed to save group feature settings | chat_id=%s",
            chat_id,
        )
        return None

    _remember_group_settings(chat_id, settings)
    return settings


def _set_limit_override(
    chat_id: int,
    limit_type: str,
    limit_value: int,
) -> Optional[GroupSettings]:
    try:
        _get_group_settings_storage().set_limit_override(
            chat_id,
            limit_type,
            limit_value,
        )
    except (OSError, sqlite3.Error, ValueError):
        LOGGER.exception(
            "Failed to save group limit override | chat_id=%s, "
            "limit_type=%s",
            chat_id,
            limit_type,
        )
        return None

    _group_settings_cache.pop(chat_id, None)
    updated_settings = get_group_settings(chat_id)
    _remember_group_settings(chat_id, updated_settings)
    return updated_settings


def _delete_limit_override(
    chat_id: int,
    limit_type: str,
) -> Optional[GroupSettings]:
    try:
        _get_group_settings_storage().delete_limit_override(
            chat_id,
            limit_type,
        )
    except (OSError, sqlite3.Error, ValueError):
        LOGGER.exception(
            "Failed to delete group limit override | chat_id=%s, "
            "limit_type=%s",
            chat_id,
            limit_type,
        )
        return None

    _group_settings_cache.pop(chat_id, None)
    updated_settings = get_group_settings(chat_id)
    _remember_group_settings(chat_id, updated_settings)
    return updated_settings


def update_group_setting(
    chat_id: int,
    setting_name: str,
    value: bool | int | None,
) -> Optional[GroupSettings]:
    """Update one group setting and return the effective saved settings."""
    current_settings = get_group_settings(chat_id)

    if setting_name == "crypto_converter_enabled":
        return _save_feature_settings(
            chat_id,
            GroupSettings(
                crypto_converter_enabled=bool(value),
                calculator_enabled=current_settings.calculator_enabled,
                time_converter_enabled=current_settings.time_converter_enabled,
                max_crypto_pairs_per_message=(
                    current_settings.max_crypto_pairs_per_message
                ),
                max_time_matches_per_message=(
                    current_settings.max_time_matches_per_message
                ),
            ),
        )

    if setting_name == "calculator_enabled":
        return _save_feature_settings(
            chat_id,
            GroupSettings(
                crypto_converter_enabled=(
                    current_settings.crypto_converter_enabled
                ),
                calculator_enabled=bool(value),
                time_converter_enabled=current_settings.time_converter_enabled,
                max_crypto_pairs_per_message=(
                    current_settings.max_crypto_pairs_per_message
                ),
                max_time_matches_per_message=(
                    current_settings.max_time_matches_per_message
                ),
            ),
        )

    if setting_name == "time_converter_enabled":
        return _save_feature_settings(
            chat_id,
            GroupSettings(
                crypto_converter_enabled=(
                    current_settings.crypto_converter_enabled
                ),
                calculator_enabled=current_settings.calculator_enabled,
                time_converter_enabled=bool(value),
                max_crypto_pairs_per_message=(
                    current_settings.max_crypto_pairs_per_message
                ),
                max_time_matches_per_message=(
                    current_settings.max_time_matches_per_message
                ),
            ),
        )

    if setting_name == "max_crypto_pairs_per_message":
        if value is None:
            return _delete_limit_override(chat_id, CRYPTO_LIMIT_TYPE)

        return _set_limit_override(
            chat_id,
            CRYPTO_LIMIT_TYPE,
            int(value),
        )

    if setting_name == "max_time_matches_per_message":
        if value is None:
            return _delete_limit_override(chat_id, TIME_LIMIT_TYPE)

        return _set_limit_override(
            chat_id,
            TIME_LIMIT_TYPE,
            int(value),
        )

    return None
