# telegram_bot/handlers/language_callback_handler.py

# Standard Libraries
import logging
import re
from typing import Final, Optional

# Third-party Libraries
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

# Custom Modules
from telegram_bot.keyboards.language_keyboard import (
    CHANGE_LANGUAGE_CALLBACK_PREFIX,
    SET_LANGUAGE_CALLBACK_PREFIX,
    build_language_selection_keyboard,
)
from telegram_bot.localization.language_preferences import (
    DEFAULT_LANGUAGE,
    resolve_user_language,
    save_user_language,
)
from telegram_bot.localization.messages import get_message


LOGGER = logging.getLogger(__name__)
CHANGE_LANGUAGE_CALLBACK_PATTERN: Final[str] = (
    rf"^{CHANGE_LANGUAGE_CALLBACK_PREFIX}:[1-9][0-9]*$"
)
SET_LANGUAGE_CALLBACK_PATTERN: Final[str] = (
    rf"^{SET_LANGUAGE_CALLBACK_PREFIX}:(?:en|uk|ru):[1-9][0-9]*$"
)
CHANGE_LANGUAGE_DATA_PATTERN: Final[re.Pattern[str]] = re.compile(
    rf"{CHANGE_LANGUAGE_CALLBACK_PREFIX}:(?P<user_id>[1-9][0-9]*)"
)
SET_LANGUAGE_DATA_PATTERN: Final[re.Pattern[str]] = re.compile(
    rf"{SET_LANGUAGE_CALLBACK_PREFIX}:"
    r"(?P<language>en|uk|ru):(?P<user_id>[1-9][0-9]*)"
)


def _parse_callback_owner(
    callback_data: Optional[str],
) -> Optional[int]:
    if callback_data is None:
        return None

    match = CHANGE_LANGUAGE_DATA_PATTERN.fullmatch(callback_data)

    if match is None:
        return None

    return int(match.group("user_id"))


async def handle_change_language_callback(
    update: Update,
    _context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Open the language selector for the bot-info message author."""
    callback_query = update.callback_query

    if callback_query is None:
        return

    await callback_query.answer()
    owner_id = _parse_callback_owner(callback_query.data)
    user = callback_query.from_user

    if owner_id != user.id:
        LOGGER.warning(
            "Language selection denied: user is not menu owner | "
            "owner_id=%s, user_id=%s",
            owner_id,
            user.id,
        )
        return

    language = resolve_user_language(user.id, user.language_code)
    await callback_query.edit_message_reply_markup(
        reply_markup=build_language_selection_keyboard(
            user.id,
            language,
        )
    )
    LOGGER.info(
        "Language selector opened | user_id=%s, language=%s",
        user.id,
        language,
    )


async def handle_set_language_callback(
    update: Update,
    _context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Persist a manual language and update the bot-info message."""
    callback_query = update.callback_query

    if callback_query is None or callback_query.data is None:
        return

    await callback_query.answer()
    match = SET_LANGUAGE_DATA_PATTERN.fullmatch(callback_query.data)

    if match is None:
        return

    owner_id = int(match.group("user_id"))
    user = callback_query.from_user

    if owner_id != user.id:
        LOGGER.warning(
            "Language change denied: user is not menu owner | "
            "owner_id=%s, user_id=%s",
            owner_id,
            user.id,
        )
        return

    selected_language = match.group("language")

    if not save_user_language(user.id, selected_language):
        selected_language = DEFAULT_LANGUAGE

    await callback_query.edit_message_text(
        text=get_message("bot_info", language=selected_language),
        parse_mode=ParseMode.HTML,
        reply_markup=build_language_selection_keyboard(
            user.id,
            selected_language,
        ),
    )
    LOGGER.info(
        "Language preference selected | user_id=%s, language=%s",
        user.id,
        selected_language,
    )
