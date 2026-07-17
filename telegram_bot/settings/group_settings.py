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
    max_crypto_pairs_per_message_override: Optional[int] = None
    max_time_matches_per_message_override: Optional[int] = None


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
            self._ensure_table_schema(connection)
            connection.commit()

    def _create_table(self, connection: sqlite3.Connection) -> None:
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
                max_crypto_pairs_per_message INTEGER CHECK (
                    max_crypto_pairs_per_message IS NULL
                    OR max_crypto_pairs_per_message IN (1, 3, 5)
                ),
                max_time_matches_per_message INTEGER CHECK (
                    max_time_matches_per_message IS NULL
                    OR max_time_matches_per_message IN (1, 3, 5)
                )
            )
            """
        )

    def _ensure_table_schema(self, connection: sqlite3.Connection) -> None:
        table_exists = connection.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'group_feature_settings'
            """
        ).fetchone()

        if table_exists is None:
            self._create_table(connection)
            return

        if self._requires_nullable_limit_migration(connection):
            self._migrate_to_nullable_limit_overrides(connection)

    def _requires_nullable_limit_migration(
        self,
        connection: sqlite3.Connection,
    ) -> bool:
        columns = {
            str(row[1]): int(row[3])
            for row in connection.execute(
                "PRAGMA table_info(group_feature_settings)"
            ).fetchall()
        }

        return (
            columns.get("max_crypto_pairs_per_message") == 1
            or columns.get("max_time_matches_per_message") == 1
        )

    def _migrate_to_nullable_limit_overrides(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        connection.execute(
            """
            ALTER TABLE group_feature_settings
            RENAME TO group_feature_settings_old
            """
        )
        self._create_table(connection)
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
            SELECT
                chat_id,
                crypto_converter_enabled,
                calculator_enabled,
                time_converter_enabled,
                max_crypto_pairs_per_message,
                max_time_matches_per_message
            FROM group_feature_settings_old
            """
        )
        connection.execute("DROP TABLE group_feature_settings_old")

    def get_settings(self, chat_id: int) -> Optional[GroupSettings]:
        """Return saved group settings, if present."""
        with closing(self._connect()) as connection:
            row = connection.execute(
                """
                SELECT
                    crypto_converter_enabled,
                    calculator_enabled,
                    time_converter_enabled,
                    max_crypto_pairs_per_message,
                    max_time_matches_per_message
                FROM group_feature_settings
                WHERE chat_id = ?
                """,
                (chat_id,),
            ).fetchone()

        if row is None:
            return None

        crypto_limit_override = (
            int(row[3]) if row[3] is not None else None
        )
        time_limit_override = int(row[4]) if row[4] is not None else None

        return GroupSettings(
            crypto_converter_enabled=bool(row[0]),
            calculator_enabled=bool(row[1]),
            time_converter_enabled=bool(row[2]),
            max_crypto_pairs_per_message=(
                crypto_limit_override
                if crypto_limit_override is not None
                else MAX_CRYPTO_PAIRS_PER_MESSAGE
            ),
            max_time_matches_per_message=(
                time_limit_override
                if time_limit_override is not None
                else MAX_TIME_MATCHES_PER_MESSAGE
            ),
            max_crypto_pairs_per_message_override=crypto_limit_override,
            max_time_matches_per_message_override=time_limit_override,
        )

    def save_settings(
        self,
        chat_id: int,
        settings: GroupSettings,
    ) -> None:
        """Insert or update all group settings."""
        _validate_settings(settings)

        with closing(self._connect()) as connection:
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
                ON CONFLICT (chat_id)
                DO UPDATE SET
                    crypto_converter_enabled =
                        excluded.crypto_converter_enabled,
                    calculator_enabled = excluded.calculator_enabled,
                    time_converter_enabled =
                        excluded.time_converter_enabled,
                    max_crypto_pairs_per_message =
                        excluded.max_crypto_pairs_per_message,
                    max_time_matches_per_message =
                        excluded.max_time_matches_per_message
                """,
                (
                    chat_id,
                    int(settings.crypto_converter_enabled),
                    int(settings.calculator_enabled),
                    int(settings.time_converter_enabled),
                    settings.max_crypto_pairs_per_message_override,
                    settings.max_time_matches_per_message_override,
                ),
            )
            connection.commit()


_group_settings_storage: Optional[GroupSettingsStorage] = None
_group_settings_cache: GroupSettingsCache = OrderedDict()


def _validate_settings(settings: GroupSettings) -> None:
    crypto_limit_override = settings.max_crypto_pairs_per_message_override
    time_limit_override = settings.max_time_matches_per_message_override

    if (
        crypto_limit_override is not None
        and crypto_limit_override not in ALLOWED_MESSAGE_LIMITS
    ):
        raise ValueError("Unsupported crypto pairs limit")

    if (
        time_limit_override is not None
        and time_limit_override not in ALLOWED_MESSAGE_LIMITS
    ):
        raise ValueError("Unsupported time matches limit")


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


def update_group_setting(
    chat_id: int,
    setting_name: str,
    value: bool | int | None,
) -> Optional[GroupSettings]:
    """Update one group setting and return the effective saved settings."""
    current_settings = get_group_settings(chat_id)

    if setting_name == "crypto_converter_enabled":
        updated_settings = GroupSettings(
            crypto_converter_enabled=bool(value),
            calculator_enabled=current_settings.calculator_enabled,
            time_converter_enabled=current_settings.time_converter_enabled,
            max_crypto_pairs_per_message=(
                current_settings.max_crypto_pairs_per_message
            ),
            max_time_matches_per_message=(
                current_settings.max_time_matches_per_message
            ),
            max_crypto_pairs_per_message_override=(
                current_settings.max_crypto_pairs_per_message_override
            ),
            max_time_matches_per_message_override=(
                current_settings.max_time_matches_per_message_override
            ),
        )
    elif setting_name == "calculator_enabled":
        updated_settings = GroupSettings(
            crypto_converter_enabled=current_settings.crypto_converter_enabled,
            calculator_enabled=bool(value),
            time_converter_enabled=current_settings.time_converter_enabled,
            max_crypto_pairs_per_message=(
                current_settings.max_crypto_pairs_per_message
            ),
            max_time_matches_per_message=(
                current_settings.max_time_matches_per_message
            ),
            max_crypto_pairs_per_message_override=(
                current_settings.max_crypto_pairs_per_message_override
            ),
            max_time_matches_per_message_override=(
                current_settings.max_time_matches_per_message_override
            ),
        )
    elif setting_name == "time_converter_enabled":
        updated_settings = GroupSettings(
            crypto_converter_enabled=current_settings.crypto_converter_enabled,
            calculator_enabled=current_settings.calculator_enabled,
            time_converter_enabled=bool(value),
            max_crypto_pairs_per_message=(
                current_settings.max_crypto_pairs_per_message
            ),
            max_time_matches_per_message=(
                current_settings.max_time_matches_per_message
            ),
            max_crypto_pairs_per_message_override=(
                current_settings.max_crypto_pairs_per_message_override
            ),
            max_time_matches_per_message_override=(
                current_settings.max_time_matches_per_message_override
            ),
        )
    elif setting_name == "max_crypto_pairs_per_message":
        crypto_limit_override = int(value) if value is not None else None
        updated_settings = GroupSettings(
            crypto_converter_enabled=current_settings.crypto_converter_enabled,
            calculator_enabled=current_settings.calculator_enabled,
            time_converter_enabled=current_settings.time_converter_enabled,
            max_crypto_pairs_per_message=(
                crypto_limit_override
                if crypto_limit_override is not None
                else MAX_CRYPTO_PAIRS_PER_MESSAGE
            ),
            max_time_matches_per_message=(
                current_settings.max_time_matches_per_message
            ),
            max_crypto_pairs_per_message_override=crypto_limit_override,
            max_time_matches_per_message_override=(
                current_settings.max_time_matches_per_message_override
            ),
        )
    elif setting_name == "max_time_matches_per_message":
        time_limit_override = int(value) if value is not None else None
        updated_settings = GroupSettings(
            crypto_converter_enabled=current_settings.crypto_converter_enabled,
            calculator_enabled=current_settings.calculator_enabled,
            time_converter_enabled=current_settings.time_converter_enabled,
            max_crypto_pairs_per_message=(
                current_settings.max_crypto_pairs_per_message
            ),
            max_time_matches_per_message=(
                time_limit_override
                if time_limit_override is not None
                else MAX_TIME_MATCHES_PER_MESSAGE
            ),
            max_crypto_pairs_per_message_override=(
                current_settings.max_crypto_pairs_per_message_override
            ),
            max_time_matches_per_message_override=time_limit_override,
        )
    else:
        return None

    if not save_group_settings(chat_id, updated_settings):
        return None

    return updated_settings
