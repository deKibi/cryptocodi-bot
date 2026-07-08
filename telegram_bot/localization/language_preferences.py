# telegram_bot/localization/language_preferences.py

# Standard Libraries
import logging
import sqlite3
from collections import OrderedDict
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

# Language scopes
USER_LANGUAGE_SCOPE: Final[str] = "user"
CHAT_LANGUAGE_SCOPE: Final[str] = "chat"
PRIVATE_CHAT_TYPE: Final[str] = "private"
GROUP_CHAT_TYPES: Final[frozenset[str]] = frozenset(
    {"group", "supergroup"}
)

# Language preference storage
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent.parent
BOT_SETTINGS_DATABASE_PATH: Final[Path] = (
    PROJECT_ROOT / "data" / "bot_settings.sqlite3"
)
SQLITE_TIMEOUT_SECONDS: Final[int] = 10
MAX_CACHED_LANGUAGE_PREFERENCES: Final[int] = 10_000

LanguagePreference = tuple[str, str]
LanguageScopeKey = tuple[str, int]
LanguagePreferenceCache = OrderedDict[LanguageScopeKey, LanguagePreference]

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
    """Persist separate language settings for users and chats."""

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
                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id INTEGER PRIMARY KEY,
                    language_code TEXT NOT NULL CHECK (
                        language_code IN ('en', 'uk', 'ru')
                    ),
                    selection_source TEXT NOT NULL CHECK (
                        selection_source IN ('auto', 'manual')
                    )
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_settings (
                    chat_id INTEGER PRIMARY KEY,
                    language_code TEXT NOT NULL CHECK (
                        language_code IN ('en', 'uk', 'ru')
                    ),
                    selection_source TEXT NOT NULL CHECK (
                        selection_source IN ('auto', 'manual')
                    )
                )
                """
            )
            connection.commit()

    def get_user_preference(
        self,
        user_id: int,
    ) -> Optional[LanguagePreference]:
        """Return a saved user language and selection source."""
        with closing(self._connect()) as connection:
            row = connection.execute(
                """
                SELECT language_code, selection_source
                FROM user_settings
                WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()

        if row is None:
            return None

        return str(row[0]), str(row[1])

    def get_chat_preference(
        self,
        chat_id: int,
    ) -> Optional[LanguagePreference]:
        """Return a saved chat language and selection source."""
        with closing(self._connect()) as connection:
            row = connection.execute(
                """
                SELECT language_code, selection_source
                FROM chat_settings
                WHERE chat_id = ?
                """,
                (chat_id,),
            ).fetchone()

        if row is None:
            return None

        return str(row[0]), str(row[1])

    def set_user_language(
        self,
        user_id: int,
        language: str,
        selection_source: str,
    ) -> None:
        """Insert or update a user language preference."""
        _validate_language_preference(language, selection_source)

        with closing(self._connect()) as connection:
            connection.execute(
                """
                INSERT INTO user_settings (
                    user_id,
                    language_code,
                    selection_source
                )
                VALUES (?, ?, ?)
                ON CONFLICT (user_id)
                DO UPDATE SET
                    language_code = excluded.language_code,
                    selection_source = excluded.selection_source
                """,
                (user_id, language, selection_source),
            )
            connection.commit()

    def set_chat_language(
        self,
        chat_id: int,
        language: str,
        selection_source: str,
    ) -> None:
        """Insert or update a chat language preference."""
        _validate_language_preference(language, selection_source)

        with closing(self._connect()) as connection:
            connection.execute(
                """
                INSERT INTO chat_settings (
                    chat_id,
                    language_code,
                    selection_source
                )
                VALUES (?, ?, ?)
                ON CONFLICT (chat_id)
                DO UPDATE SET
                    language_code = excluded.language_code,
                    selection_source = excluded.selection_source
                """,
                (chat_id, language, selection_source),
            )
            connection.commit()


def _validate_language_preference(
    language: str,
    selection_source: str,
) -> None:
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language: {language}")

    if selection_source not in SELECTION_SOURCES:
        raise ValueError(
            f"Unsupported selection source: {selection_source}"
        )


_language_preference_storage: Optional[LanguagePreferenceStorage] = None
_language_preference_cache: LanguagePreferenceCache = OrderedDict()


def _get_language_preference_storage() -> LanguagePreferenceStorage:
    global _language_preference_storage

    if _language_preference_storage is None:
        _language_preference_storage = LanguagePreferenceStorage()

    return _language_preference_storage


def _remember_language_preference(
    scope_key: LanguageScopeKey,
    preference: LanguagePreference,
) -> None:
    _language_preference_cache[scope_key] = preference
    _language_preference_cache.move_to_end(scope_key)

    while len(_language_preference_cache) > MAX_CACHED_LANGUAGE_PREFERENCES:
        _language_preference_cache.popitem(last=False)


def _is_valid_preference(preference: LanguagePreference) -> bool:
    language, selection_source = preference
    return (
        language in SUPPORTED_LANGUAGES
        and selection_source in SELECTION_SOURCES
    )


def _get_stored_preference(
    scope_type: str,
    scope_id: int,
) -> Optional[LanguagePreference]:
    storage = _get_language_preference_storage()

    if scope_type == USER_LANGUAGE_SCOPE:
        return storage.get_user_preference(scope_id)

    if scope_type == CHAT_LANGUAGE_SCOPE:
        return storage.get_chat_preference(scope_id)

    raise ValueError(f"Unsupported language scope: {scope_type}")


def _set_stored_language(
    scope_type: str,
    scope_id: int,
    language: str,
    selection_source: str,
) -> None:
    storage = _get_language_preference_storage()

    if scope_type == USER_LANGUAGE_SCOPE:
        storage.set_user_language(scope_id, language, selection_source)
        return

    if scope_type == CHAT_LANGUAGE_SCOPE:
        storage.set_chat_language(scope_id, language, selection_source)
        return

    raise ValueError(f"Unsupported language scope: {scope_type}")


def _resolve_scope_language(
    scope_type: str,
    scope_id: int,
    telegram_language_code: object,
) -> str:
    scope_key = (scope_type, scope_id)
    cached_preference = _language_preference_cache.get(scope_key)

    if cached_preference is not None:
        _language_preference_cache.move_to_end(scope_key)
        return cached_preference[0]

    try:
        stored_preference = _get_stored_preference(scope_type, scope_id)

        if stored_preference is not None:
            if _is_valid_preference(stored_preference):
                _remember_language_preference(scope_key, stored_preference)
                return stored_preference[0]

            LOGGER.warning(
                "Invalid stored language preference; using English | "
                "scope_type=%s, scope_id=%s",
                scope_type,
                scope_id,
            )
            _remember_language_preference(
                scope_key,
                (DEFAULT_LANGUAGE, AUTO_SELECTION_SOURCE),
            )
            return DEFAULT_LANGUAGE

        detected_language = normalize_language_code(telegram_language_code)
        preference = (detected_language, AUTO_SELECTION_SOURCE)
        _set_stored_language(
            scope_type,
            scope_id,
            detected_language,
            AUTO_SELECTION_SOURCE,
        )
        _remember_language_preference(scope_key, preference)
        return detected_language
    except (OSError, sqlite3.Error):
        LOGGER.exception(
            "Failed to resolve language preference; using English | "
            "scope_type=%s, scope_id=%s",
            scope_type,
            scope_id,
        )
        return DEFAULT_LANGUAGE


def resolve_user_language(
    user_id: Optional[int],
    telegram_language_code: object,
) -> str:
    """Return one stable language for a private-chat user."""
    if user_id is None:
        return DEFAULT_LANGUAGE

    return _resolve_scope_language(
        USER_LANGUAGE_SCOPE,
        user_id,
        telegram_language_code,
    )


def resolve_chat_language(
    chat_id: Optional[int],
    first_user_language_code: object,
) -> str:
    """Return one stable language shared by all users in a chat."""
    if chat_id is None:
        return DEFAULT_LANGUAGE

    return _resolve_scope_language(
        CHAT_LANGUAGE_SCOPE,
        chat_id,
        first_user_language_code,
    )


def get_existing_chat_language(chat_id: int) -> Optional[str]:
    """Return an existing chat language without creating a setting."""
    scope_key = (CHAT_LANGUAGE_SCOPE, chat_id)
    cached_preference = _language_preference_cache.get(scope_key)

    if cached_preference is not None:
        _language_preference_cache.move_to_end(scope_key)
        return cached_preference[0]

    try:
        stored_preference = _get_stored_preference(
            CHAT_LANGUAGE_SCOPE,
            chat_id,
        )
    except (OSError, sqlite3.Error):
        LOGGER.exception(
            "Failed to read existing chat language | chat_id=%s",
            chat_id,
        )
        return None

    if stored_preference is None:
        return None

    if not _is_valid_preference(stored_preference):
        LOGGER.warning(
            "Invalid stored chat language preference | chat_id=%s",
            chat_id,
        )
        return DEFAULT_LANGUAGE

    _remember_language_preference(scope_key, stored_preference)
    return stored_preference[0]


def resolve_context_language(
    chat_id: Optional[int],
    chat_type: object,
    user_id: Optional[int],
    telegram_language_code: object,
) -> str:
    """Resolve a user language in private or a shared language in groups."""
    if chat_type == PRIVATE_CHAT_TYPE:
        return resolve_user_language(user_id, telegram_language_code)

    if chat_type in GROUP_CHAT_TYPES:
        return resolve_chat_language(chat_id, telegram_language_code)

    return DEFAULT_LANGUAGE


def get_language_scope(
    chat_id: Optional[int],
    chat_type: object,
    user_id: Optional[int],
) -> Optional[LanguageScopeKey]:
    """Return the preference scope used by a Telegram chat context."""
    if chat_type == PRIVATE_CHAT_TYPE and user_id is not None:
        return USER_LANGUAGE_SCOPE, user_id

    if chat_type in GROUP_CHAT_TYPES and chat_id is not None:
        return CHAT_LANGUAGE_SCOPE, chat_id

    return None


def _save_scope_language(
    scope_type: str,
    scope_id: int,
    language: str,
) -> bool:
    if language not in SUPPORTED_LANGUAGES:
        return False

    try:
        _set_stored_language(
            scope_type,
            scope_id,
            language,
            MANUAL_SELECTION_SOURCE,
        )
    except (OSError, sqlite3.Error):
        LOGGER.exception(
            "Failed to save language preference | "
            "scope_type=%s, scope_id=%s, language=%s",
            scope_type,
            scope_id,
            language,
        )
        return False

    _remember_language_preference(
        (scope_type, scope_id),
        (language, MANUAL_SELECTION_SOURCE),
    )
    return True


def save_user_language(user_id: int, language: str) -> bool:
    """Persist a manual user language selection."""
    return _save_scope_language(USER_LANGUAGE_SCOPE, user_id, language)


def save_chat_language(chat_id: int, language: str) -> bool:
    """Persist a manual chat language selection."""
    return _save_scope_language(CHAT_LANGUAGE_SCOPE, chat_id, language)
