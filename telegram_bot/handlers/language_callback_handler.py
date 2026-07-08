# telegram_bot/handlers/language_callback_handler.py

# Standard Libraries
import asyncio
import logging
import re
from typing import Final, Optional

# Third-party Libraries
from telegram import Message, Update
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.error import TelegramError
from telegram.ext import ContextTypes

# Custom Modules
from telegram_bot.keyboards.language_keyboard import (
    BACK_TO_LANGUAGE_SETTINGS_CALLBACK_PREFIX,
    BOT_INFO_LANGUAGE_RESPONSE,
    COMMAND_LANGUAGE_RESPONSE,
    CHANGE_LANGUAGE_CALLBACK_PREFIX,
    SET_LANGUAGE_CALLBACK_PREFIX,
    build_change_language_keyboard,
    build_language_selection_keyboard,
)
from telegram_bot.localization.language_preferences import (
    CHAT_LANGUAGE_SCOPE,
    DEFAULT_LANGUAGE,
    USER_LANGUAGE_SCOPE,
    get_language_scope,
    get_existing_chat_language,
    resolve_context_language,
    resolve_chat_language,
    resolve_user_language,
    save_chat_language,
    save_user_language,
)
from telegram_bot.localization.messages import get_message


LOGGER = logging.getLogger(__name__)
NON_ADMIN_LANGUAGE_NOTICE_SECONDS: Final[int] = 15
LANGUAGE_SCOPE_CALLBACK_REGEX: Final[str] = (
    r"(?:user:[1-9][0-9]*|chat:-[1-9][0-9]*)"
)
CHANGE_LANGUAGE_CALLBACK_PATTERN: Final[str] = (
    rf"^{CHANGE_LANGUAGE_CALLBACK_PREFIX}:"
    rf"{LANGUAGE_SCOPE_CALLBACK_REGEX}$"
)
BACK_TO_LANGUAGE_SETTINGS_CALLBACK_PATTERN: Final[str] = (
    rf"^{BACK_TO_LANGUAGE_SETTINGS_CALLBACK_PREFIX}:"
    rf"{LANGUAGE_SCOPE_CALLBACK_REGEX}$"
)
SET_LANGUAGE_CALLBACK_PATTERN: Final[str] = (
    rf"^{SET_LANGUAGE_CALLBACK_PREFIX}:(?:en|uk|ru):"
    rf"{LANGUAGE_SCOPE_CALLBACK_REGEX}"
    rf"(?::{COMMAND_LANGUAGE_RESPONSE})?$"
)
CHANGE_LANGUAGE_DATA_PATTERN: Final[re.Pattern[str]] = re.compile(
    rf"{CHANGE_LANGUAGE_CALLBACK_PREFIX}:"
    r"(?P<scope_type>user|chat):(?P<scope_id>-?[1-9][0-9]*)"
)
BACK_TO_LANGUAGE_SETTINGS_DATA_PATTERN: Final[re.Pattern[str]] = re.compile(
    rf"{BACK_TO_LANGUAGE_SETTINGS_CALLBACK_PREFIX}:"
    r"(?P<scope_type>user|chat):(?P<scope_id>-?[1-9][0-9]*)"
)
SET_LANGUAGE_DATA_PATTERN: Final[re.Pattern[str]] = re.compile(
    rf"{SET_LANGUAGE_CALLBACK_PREFIX}:"
    r"(?P<language>en|uk|ru):"
    r"(?P<scope_type>user|chat):(?P<scope_id>-?[1-9][0-9]*)"
    rf"(?::(?P<response_mode>{COMMAND_LANGUAGE_RESPONSE}))?"
)
GROUP_LANGUAGE_MANAGER_STATUSES: Final[frozenset[str]] = frozenset(
    {ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR}
)

LanguageScope = tuple[str, int]


async def _delete_temporary_message(message: Message) -> None:
    await asyncio.sleep(NON_ADMIN_LANGUAGE_NOTICE_SECONDS)

    try:
        await message.delete()
    except TelegramError as error:
        LOGGER.warning(
            "Temporary language notice deletion failed: %s | "
            "chat_id=%s, message_id=%s",
            error,
            message.chat_id,
            message.message_id,
        )


def _parse_language_scope(
    callback_data: Optional[str],
    pattern: re.Pattern[str],
) -> Optional[LanguageScope]:
    if callback_data is None:
        return None

    match = pattern.fullmatch(callback_data)

    if match is None:
        return None

    scope_type = match.group("scope_type")
    scope_id = int(match.group("scope_id"))

    if scope_type == USER_LANGUAGE_SCOPE and scope_id > 0:
        return scope_type, scope_id

    if scope_type == CHAT_LANGUAGE_SCOPE and scope_id < 0:
        return scope_type, scope_id

    return None


async def _can_manage_language_scope(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    scope: LanguageScope,
) -> bool:
    user = update.effective_user

    if user is None:
        return False

    scope_type, scope_id = scope

    if scope_type == USER_LANGUAGE_SCOPE:
        return user.id == scope_id

    chat = update.effective_chat

    if chat is None or chat.id != scope_id:
        return False

    try:
        chat_administrators = await context.bot.get_chat_administrators(
            chat_id=scope_id,
        )
    except TelegramError as error:
        LOGGER.warning(
            "Group language authorization failed: %s | "
            "chat_id=%s, user_id=%s",
            error,
            scope_id,
            user.id,
        )
        return False

    return any(
        chat_member.user.id == user.id
        and chat_member.status in GROUP_LANGUAGE_MANAGER_STATUSES
        for chat_member in chat_administrators
    )


def _resolve_scope_language(
    scope: LanguageScope,
    telegram_language_code: object,
) -> str:
    scope_type, scope_id = scope

    if scope_type == USER_LANGUAGE_SCOPE:
        return resolve_user_language(scope_id, telegram_language_code)

    return resolve_chat_language(scope_id, telegram_language_code)


def _save_scope_language(
    scope: LanguageScope,
    language: str,
) -> bool:
    scope_type, scope_id = scope

    if scope_type == USER_LANGUAGE_SCOPE:
        return save_user_language(scope_id, language)

    return save_chat_language(scope_id, language)


async def handle_change_language_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Open language selection for an authorized user or group admin."""
    callback_query = update.callback_query

    if callback_query is None:
        return

    await callback_query.answer()
    scope = _parse_language_scope(
        callback_query.data,
        CHANGE_LANGUAGE_DATA_PATTERN,
    )

    if scope is None or not await _can_manage_language_scope(
        update,
        context,
        scope,
    ):
        LOGGER.warning(
            "Language selection denied | scope=%r, user_id=%s",
            scope,
            callback_query.from_user.id,
        )
        return

    user = callback_query.from_user
    language = _resolve_scope_language(scope, user.language_code)
    await callback_query.edit_message_reply_markup(
        reply_markup=build_language_selection_keyboard(
            *scope,
            language,
        )
    )
    LOGGER.info(
        "Language selector opened | scope=%r, user_id=%s, language=%s",
        scope,
        user.id,
        language,
    )


async def handle_back_to_language_settings_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Close the bot-info selector without changing its language."""
    callback_query = update.callback_query

    if callback_query is None:
        return

    await callback_query.answer()
    scope = _parse_language_scope(
        callback_query.data,
        BACK_TO_LANGUAGE_SETTINGS_DATA_PATTERN,
    )

    if scope is None or not await _can_manage_language_scope(
        update,
        context,
        scope,
    ):
        LOGGER.warning(
            "Language selector close denied | scope=%r, user_id=%s",
            scope,
            callback_query.from_user.id,
        )
        return

    await callback_query.edit_message_reply_markup(
        reply_markup=build_change_language_keyboard(*scope),
    )
    LOGGER.info(
        "Language selector closed | scope=%r, user_id=%s",
        scope,
        callback_query.from_user.id,
    )


async def handle_language_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Show language selection for a user or authorized group admin."""
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if message is None or chat is None or user is None:
        return

    scope = get_language_scope(chat.id, chat.type, user.id)

    if scope is None:
        return

    if not await _can_manage_language_scope(
        update,
        context,
        scope,
    ):
        LOGGER.warning(
            "Language command denied | scope=%r, user_id=%s",
            scope,
            user.id,
        )

        if scope[0] == CHAT_LANGUAGE_SCOPE:
            language = (
                get_existing_chat_language(scope[1])
                or DEFAULT_LANGUAGE
            )
            notice_message = await message.reply_text(
                text=get_message(
                    "group_language_admin_only",
                    language=language,
                ),
                do_quote=True,
            )
            context.application.create_task(
                _delete_temporary_message(notice_message),
                update=update,
                name="delete-non-admin-language-notice",
            )

        return

    language = resolve_context_language(
        chat.id,
        chat.type,
        user.id,
        user.language_code,
    )
    await message.reply_text(
        text=get_message("choose_language", language=language),
        do_quote=True,
        reply_markup=build_language_selection_keyboard(
            *scope,
            language,
            COMMAND_LANGUAGE_RESPONSE,
        ),
    )
    LOGGER.info(
        "Language command reply sent | scope=%r, user_id=%s, language=%s",
        scope,
        user.id,
        language,
    )


async def handle_set_language_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Persist a manual language for an authorized user or group admin."""
    callback_query = update.callback_query

    if callback_query is None or callback_query.data is None:
        return

    await callback_query.answer()
    match = SET_LANGUAGE_DATA_PATTERN.fullmatch(callback_query.data)
    scope = _parse_language_scope(
        callback_query.data,
        SET_LANGUAGE_DATA_PATTERN,
    )

    if (
        match is None
        or scope is None
        or not await _can_manage_language_scope(update, context, scope)
    ):
        LOGGER.warning(
            "Language change denied | scope=%r, user_id=%s",
            scope,
            callback_query.from_user.id,
        )
        return

    selected_language = match.group("language")
    response_mode = match.group("response_mode")

    if not _save_scope_language(scope, selected_language):
        selected_language = DEFAULT_LANGUAGE

    is_command_response = response_mode == COMMAND_LANGUAGE_RESPONSE
    await callback_query.edit_message_text(
        text=get_message(
            (
                "language_changed"
                if is_command_response
                else "bot_info"
            ),
            language=selected_language,
        ),
        parse_mode=ParseMode.HTML,
        reply_markup=(
            None
            if is_command_response
            else build_change_language_keyboard(*scope)
        ),
    )
    LOGGER.info(
        "Language preference selected | scope=%r, user_id=%s, language=%s",
        scope,
        callback_query.from_user.id,
        selected_language,
    )
