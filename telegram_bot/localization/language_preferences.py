# telegram_bot/localization/language_preferences.py

# Standard Libraries
import logging
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Final, Optional


# Supported languages
DEFAULT_LANGUAGE: Final[str] = "en"
SUPPORTED_LANGUAGES: Final[frozenset[str]] = frozenset({"en", "uk", "ru"})
AUTO_SELECTION_SOURCE: Final[str] = "auto"
MANUAL_SELECTION_SOURCE: Final[str] = "manual"
SELECTION_SOURCES: Final[frozenset[str]] = frozenset(
    {AUTO_SELECTION_SOURCE, MANUAL_SELECTION_SOURCE}
)

# Language preference storage
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent.parent
USER_PREFERENCES_DATABASE_PATH: Final[Path] = (
    PROJECT_ROOT / "data" / "user_preferences.sqlite3"
)
SQLITE_TIMEOUT_SECONDS: Final[int] = 10

LOGGER = logging.getLogger(__name__)


def normalize_language_code(language_code: object) -> str:
    """Map a Telegram language code to one of the supported languages."""
    if not isinstance(language_code, str) or not language_code.strip():
        return DEFAULT_LANGUAGE

    normalized_code = language_code.strip().lower().replace("_", "-")
    primary_language = normalized_code.split("-", maxsplit=1)[0]

    if primary_language in SUPPORTED_LANGUAGES:
        return primary_language

    return DEFAULT_LANGUAGE


class LanguagePreferenceStorage:
    """Persist one language preference for each Telegram user."""

    def __init__(
        self,
        database_path: Path = USER_PREFERENCES_DATABASE_PATH,
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
                CREATE TABLE IF NOT EXISTS user_language_preferences (
                    user_id INTEGER PRIMARY KEY,
                    language TEXT NOT NULL CHECK (
                        language IN ('en', 'uk', 'ru')
                    ),
                    selection_source TEXT NOT NULL DEFAULT 'auto' CHECK (
                        selection_source IN ('auto', 'manual')
                    )
                )
                """
            )
            columns = {
                row[1]
                for row in connection.execute(
                    "PRAGMA table_info(user_language_preferences)"
                )
            }

            if "selection_source" not in columns:
                connection.execute(
                    """
                    ALTER TABLE user_language_preferences
                    ADD COLUMN selection_source TEXT NOT NULL DEFAULT 'auto'
                    CHECK (selection_source IN ('auto', 'manual'))
                    """
                )

            connection.commit()

    def get_preference(
        self,
        user_id: int,
    ) -> Optional[tuple[str, str]]:
        """Return a saved language and its selection source."""
        with closing(self._connect()) as connection:
            row = connection.execute(
                """
                SELECT language, selection_source
                FROM user_language_preferences
                WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()

        if row is None:
            return None

        return str(row[0]), str(row[1])

    def set_language(
        self,
        user_id: int,
        language: str,
        selection_source: str,
    ) -> None:
        """Insert or update a supported language preference."""
        if language not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language: {language}")

        if selection_source not in SELECTION_SOURCES:
            raise ValueError(
                f"Unsupported selection source: {selection_source}"
            )

        with closing(self._connect()) as connection:
            connection.execute(
                """
                INSERT INTO user_language_preferences (
                    user_id,
                    language,
                    selection_source
                )
                VALUES (?, ?, ?)
                ON CONFLICT (user_id)
                DO UPDATE SET
                    language = excluded.language,
                    selection_source = excluded.selection_source
                """,
                (user_id, language, selection_source),
            )
            connection.commit()


_language_preference_storage: Optional[LanguagePreferenceStorage] = None


def _get_language_preference_storage() -> LanguagePreferenceStorage:
    global _language_preference_storage

    if _language_preference_storage is None:
        _language_preference_storage = LanguagePreferenceStorage()

    return _language_preference_storage


def resolve_user_language(
    user_id: Optional[int],
    telegram_language_code: Optional[str],
) -> str:
    """Return a saved language or detect and persist it once."""
    if user_id is None:
        return DEFAULT_LANGUAGE

    try:
        storage = _get_language_preference_storage()
        stored_preference = storage.get_preference(user_id)

        if stored_preference is not None:
            stored_language, selection_source = stored_preference

            if (
                stored_language in SUPPORTED_LANGUAGES
                and selection_source in SELECTION_SOURCES
            ):
                return stored_language

            LOGGER.warning(
                "Invalid stored language preference; using English | "
                "user_id=%s",
                user_id,
            )
            return DEFAULT_LANGUAGE

        detected_language = normalize_language_code(telegram_language_code)
        storage.set_language(
            user_id,
            detected_language,
            AUTO_SELECTION_SOURCE,
        )
        return detected_language
    except (OSError, sqlite3.Error):
        LOGGER.exception(
            "Failed to resolve language preference; using English | "
            "user_id=%s",
            user_id,
        )
        return DEFAULT_LANGUAGE


def save_user_language(user_id: int, language: str) -> bool:
    """Persist a manual language selection and report whether it succeeded."""
    if language not in SUPPORTED_LANGUAGES:
        return False

    try:
        _get_language_preference_storage().set_language(
            user_id,
            language,
            MANUAL_SELECTION_SOURCE,
        )
    except (OSError, sqlite3.Error):
        LOGGER.exception(
            "Failed to save language preference | user_id=%s, language=%s",
            user_id,
            language,
        )
        return False

    return True
