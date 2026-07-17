# telegram_bot/handlers/settings_command_handler.py

# Standard Libraries
import logging
import re
from typing import Final, Optional

# Third-party Libraries
from telegram import Message, Update
from telegram.constants import ChatMemberStatus, ChatType, ParseMode
from telegram.error import TelegramError
from telegram.ext import ContextTypes

# Custom Modules
from telegram_bot.keyboards.settings_keyboard import (
    BOT_INFO_SETTINGS_CONTEXT,
    DELETE_SETTINGS_CALLBACK_PREFIX,
    SETTINGS_BACK_CALLBACK_PREFIX,
    SETTINGS_DEFAULT_LIMIT_CALLBACK_PREFIX,
    SETTINGS_HOME_CALLBACK_PREFIX,
    SETTINGS_LIMIT_MENU_CALLBACK_PREFIX,
    SETTINGS_SET_LIMIT_CALLBACK_PREFIX,
    SETTINGS_TOGGLE_CALLBACK_PREFIX,
    build_settings_home_keyboard,
    build_settings_limit_keyboard,
)
from telegram_bot.keyboards.language_keyboard import build_change_language_keyboard
from telegram_bot.localization.language_preferences import (
    CHAT_LANGUAGE_SCOPE,
    DEFAULT_LANGUAGE,
    GROUP_CHAT_TYPES,
    resolve_context_language,
)
from telegram_bot.localization.messages import get_message
from telegram_bot.logging_config import format_log_metadata, get_update_metadata
from telegram_bot.services.temporary_message_service import (
    send_temporary_message,
)
from telegram_bot.settings.group_settings import (
    ALLOWED_MESSAGE_LIMITS,
    GroupSettings,
    get_group_settings,
    update_group_setting,
)


LOGGER = logging.getLogger(__name__)
SETTINGS_MANAGER_STATUSES: Final[frozenset[str]] = frozenset(
    {ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR}
)
SETTINGS_CHAT_ID_PATTERN: Final[str] = r"-?[1-9][0-9]*"
SETTINGS_REQUESTER_ID_PATTERN: Final[str] = r"[1-9][0-9]*"
SETTINGS_BOT_INFO_CONTEXT_PATTERN: Final[str] = (
    rf"(?::{BOT_INFO_SETTINGS_CONTEXT}:{SETTINGS_REQUESTER_ID_PATTERN})?"
)
SETTINGS_HOME_CALLBACK_PATTERN: Final[str] = (
    rf"^{SETTINGS_HOME_CALLBACK_PREFIX}:"
    rf"{SETTINGS_CHAT_ID_PATTERN}{SETTINGS_BOT_INFO_CONTEXT_PATTERN}$"
)
SETTINGS_BACK_CALLBACK_PATTERN: Final[str] = (
    rf"^{SETTINGS_BACK_CALLBACK_PREFIX}:"
    rf"{SETTINGS_CHAT_ID_PATTERN}:{SETTINGS_REQUESTER_ID_PATTERN}$"
)
SETTINGS_TOGGLE_CALLBACK_PATTERN: Final[str] = (
    rf"^{SETTINGS_TOGGLE_CALLBACK_PREFIX}:"
    rf"{SETTINGS_CHAT_ID_PATTERN}:(?:crypto|calculator|time)"
    rf"{SETTINGS_BOT_INFO_CONTEXT_PATTERN}$"
)
SETTINGS_LIMIT_MENU_CALLBACK_PATTERN: Final[str] = (
    rf"^{SETTINGS_LIMIT_MENU_CALLBACK_PREFIX}:"
    rf"{SETTINGS_CHAT_ID_PATTERN}:(?:crypto|time)"
    rf"{SETTINGS_BOT_INFO_CONTEXT_PATTERN}$"
)
SETTINGS_SET_LIMIT_CALLBACK_PATTERN: Final[str] = (
    rf"^{SETTINGS_SET_LIMIT_CALLBACK_PREFIX}:"
    rf"{SETTINGS_CHAT_ID_PATTERN}:(?:crypto|time):(?:1|3|5)"
    rf"{SETTINGS_BOT_INFO_CONTEXT_PATTERN}$"
)
SETTINGS_DEFAULT_LIMIT_CALLBACK_PATTERN: Final[str] = (
    rf"^{SETTINGS_DEFAULT_LIMIT_CALLBACK_PREFIX}:"
    rf"{SETTINGS_CHAT_ID_PATTERN}:(?:crypto|time)"
    rf"{SETTINGS_BOT_INFO_CONTEXT_PATTERN}$"
)
DELETE_SETTINGS_CALLBACK_PATTERN: Final[str] = (
    rf"^{DELETE_SETTINGS_CALLBACK_PREFIX}:{SETTINGS_CHAT_ID_PATTERN}$"
)
SETTINGS_HOME_DATA_PATTERN: Final[re.Pattern[str]] = re.compile(
    rf"{SETTINGS_HOME_CALLBACK_PREFIX}:"
    r"(?P<chat_id>-?[1-9][0-9]*)"
    rf"(?::{BOT_INFO_SETTINGS_CONTEXT}:"
    r"(?P<requester_user_id>[1-9][0-9]*))?"
)
SETTINGS_BACK_DATA_PATTERN: Final[re.Pattern[str]] = re.compile(
    rf"{SETTINGS_BACK_CALLBACK_PREFIX}:"
    r"(?P<chat_id>-?[1-9][0-9]*):"
    r"(?P<requester_user_id>[1-9][0-9]*)"
)
SETTINGS_TOGGLE_DATA_PATTERN: Final[re.Pattern[str]] = re.compile(
    rf"{SETTINGS_TOGGLE_CALLBACK_PREFIX}:"
    r"(?P<chat_id>-?[1-9][0-9]*):"
    r"(?P<feature>crypto|calculator|time)"
    rf"(?::{BOT_INFO_SETTINGS_CONTEXT}:"
    r"(?P<requester_user_id>[1-9][0-9]*))?"
)
SETTINGS_LIMIT_MENU_DATA_PATTERN: Final[re.Pattern[str]] = re.compile(
    rf"{SETTINGS_LIMIT_MENU_CALLBACK_PREFIX}:"
    r"(?P<chat_id>-?[1-9][0-9]*):"
    r"(?P<limit_type>crypto|time)"
    rf"(?::{BOT_INFO_SETTINGS_CONTEXT}:"
    r"(?P<requester_user_id>[1-9][0-9]*))?"
)
SETTINGS_SET_LIMIT_DATA_PATTERN: Final[re.Pattern[str]] = re.compile(
    rf"{SETTINGS_SET_LIMIT_CALLBACK_PREFIX}:"
    r"(?P<chat_id>-?[1-9][0-9]*):"
    r"(?P<limit_type>crypto|time):"
    r"(?P<limit>1|3|5)"
    rf"(?::{BOT_INFO_SETTINGS_CONTEXT}:"
    r"(?P<requester_user_id>[1-9][0-9]*))?"
)
SETTINGS_DEFAULT_LIMIT_DATA_PATTERN: Final[re.Pattern[str]] = re.compile(
    rf"{SETTINGS_DEFAULT_LIMIT_CALLBACK_PREFIX}:"
    r"(?P<chat_id>-?[1-9][0-9]*):"
    r"(?P<limit_type>crypto|time)"
    rf"(?::{BOT_INFO_SETTINGS_CONTEXT}:"
    r"(?P<requester_user_id>[1-9][0-9]*))?"
)
DELETE_SETTINGS_DATA_PATTERN: Final[re.Pattern[str]] = re.compile(
    rf"{DELETE_SETTINGS_CALLBACK_PREFIX}:"
    r"(?P<chat_id>-?[1-9][0-9]*)"
)


async def _can_manage_settings(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
) -> bool:
    user = update.effective_user
    chat = update.effective_chat

    if user is None or chat is None or chat.id != chat_id:
        return False

    if chat.type not in GROUP_CHAT_TYPES:
        return False

    try:
        chat_administrators = await context.bot.get_chat_administrators(
            chat_id=chat_id,
        )
    except TelegramError as error:
        LOGGER.warning(
            "Group settings authorization failed: %s | "
            "chat_id=%s, user_id=%s",
            error,
            chat_id,
            user.id,
        )
        return False

    return any(
        chat_member.user.id == user.id
        and chat_member.status in SETTINGS_MANAGER_STATUSES
        for chat_member in chat_administrators
    )


def _resolve_settings_language(update: Update) -> str:
    chat = update.effective_chat
    user = update.effective_user

    return resolve_context_language(
        chat.id if chat is not None else None,
        chat.type if chat is not None else None,
        user.id if user is not None else None,
        user.language_code if user is not None else None,
    )


def _format_status(is_enabled: bool, language: str) -> str:
    return get_message(
        (
            "settings_status_enabled"
            if is_enabled
            else "settings_status_disabled"
        ),
        language=language,
    )


def format_settings_home(
    settings: GroupSettings,
    language: str = DEFAULT_LANGUAGE,
) -> str:
    """Format the settings home screen."""
    return get_message(
        "settings_home",
        language=language,
        crypto_status=_format_status(
            settings.crypto_converter_enabled,
            language,
        ),
        calculator_status=_format_status(
            settings.calculator_enabled,
            language,
        ),
        time_status=_format_status(
            settings.time_converter_enabled,
            language,
        ),
        max_crypto=settings.max_crypto_pairs_per_message,
        max_time=settings.max_time_matches_per_message,
    )


def _get_callback_chat_id(
    callback_data: Optional[str],
    pattern: re.Pattern[str],
) -> Optional[int]:
    if callback_data is None:
        return None

    match = pattern.fullmatch(callback_data)

    if match is None:
        return None

    return int(match.group("chat_id"))


def _get_bot_info_requester_user_id(
    match: re.Match[str],
) -> Optional[int]:
    requester_user_id = match.groupdict().get("requester_user_id")

    if requester_user_id is None:
        return None

    return int(requester_user_id)


async def _edit_to_settings_home(
    message: Message,
    chat_id: int,
    language: str,
    requester_user_id: Optional[int] = None,
) -> None:
    settings = get_group_settings(chat_id)
    await message.edit_text(
        text=format_settings_home(settings, language),
        parse_mode=ParseMode.HTML,
        reply_markup=build_settings_home_keyboard(
            chat_id,
            settings,
            requester_user_id=requester_user_id,
        ),
    )


async def handle_settings_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Show group settings for group admins."""
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if message is None or chat is None or user is None:
        return

    language = _resolve_settings_language(update)
    metadata_text = format_log_metadata(get_update_metadata(update))
    LOGGER.info("Command received: /settings | %s", metadata_text)

    if chat.type not in GROUP_CHAT_TYPES:
        await message.reply_text(
            text=get_message(
                "settings_private_only_groups",
                language=language,
            ),
            do_quote=True,
        )
        return

    if not await _can_manage_settings(update, context, chat.id):
        await send_temporary_message(
            message,
            context,
            text=get_message("settings_admin_only", language=language),
            update=update,
            log_label="Temporary settings notice",
            task_name="delete-non-admin-settings-notice",
        )
        LOGGER.warning(
            "Settings command denied | chat_id=%s, user_id=%s",
            chat.id,
            user.id,
        )
        return

    settings = get_group_settings(chat.id)
    await message.reply_text(
        text=format_settings_home(settings, language),
        parse_mode=ParseMode.HTML,
        do_quote=True,
        reply_markup=build_settings_home_keyboard(chat.id, settings),
    )
    LOGGER.info(
        "Settings command reply sent | chat_id=%s, user_id=%s",
        chat.id,
        user.id,
    )


async def handle_settings_home_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Return to settings home."""
    callback_query = update.callback_query

    if callback_query is None:
        return

    match = (
        SETTINGS_HOME_DATA_PATTERN.fullmatch(callback_query.data)
        if callback_query.data is not None
        else None
    )
    chat_id = int(match.group("chat_id")) if match is not None else None
    requester_user_id = (
        _get_bot_info_requester_user_id(match)
        if match is not None
        else None
    )

    if chat_id is None or not await _can_manage_settings(
        update,
        context,
        chat_id,
    ):
        await callback_query.answer(
            text=get_message(
                "settings_admin_only",
                language=_resolve_settings_language(update),
            ),
        )
        return

    await callback_query.answer()

    if isinstance(callback_query.message, Message):
        await _edit_to_settings_home(
            callback_query.message,
            chat_id,
            _resolve_settings_language(update),
            requester_user_id=requester_user_id,
        )


async def handle_settings_back_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Return from settings opened inside a bot-information message."""
    callback_query = update.callback_query

    if callback_query is None or callback_query.data is None:
        return

    match = SETTINGS_BACK_DATA_PATTERN.fullmatch(callback_query.data)

    if match is None:
        await callback_query.answer()
        return

    chat_id = int(match.group("chat_id"))
    requester_user_id = int(match.group("requester_user_id"))
    language = _resolve_settings_language(update)

    if not await _can_manage_settings(update, context, chat_id):
        await callback_query.answer(
            text=get_message("settings_admin_only", language=language),
        )
        return

    await callback_query.answer()

    if isinstance(callback_query.message, Message):
        await callback_query.message.edit_text(
            text=get_message("bot_info", language=language),
            parse_mode=ParseMode.HTML,
            reply_markup=build_change_language_keyboard(
                CHAT_LANGUAGE_SCOPE,
                chat_id,
                requester_user_id,
            ),
        )


async def handle_settings_toggle_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Toggle one boolean group setting."""
    callback_query = update.callback_query

    if callback_query is None or callback_query.data is None:
        return

    match = SETTINGS_TOGGLE_DATA_PATTERN.fullmatch(callback_query.data)

    if match is None:
        await callback_query.answer()
        return

    chat_id = int(match.group("chat_id"))
    feature = match.group("feature")
    requester_user_id = _get_bot_info_requester_user_id(match)
    language = _resolve_settings_language(update)

    if not await _can_manage_settings(update, context, chat_id):
        await callback_query.answer(
            text=get_message("settings_admin_only", language=language),
        )
        return

    setting_names = {
        "crypto": "crypto_converter_enabled",
        "calculator": "calculator_enabled",
        "time": "time_converter_enabled",
    }
    setting_name = setting_names[feature]
    current_settings = get_group_settings(chat_id)
    current_value = getattr(current_settings, setting_name)
    update_group_setting(chat_id, setting_name, not current_value)
    await callback_query.answer()

    if isinstance(callback_query.message, Message):
        await _edit_to_settings_home(
            callback_query.message,
            chat_id,
            language,
            requester_user_id=requester_user_id,
        )


async def handle_settings_limit_menu_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Open 1/3/5 settings submenu."""
    callback_query = update.callback_query

    if callback_query is None or callback_query.data is None:
        return

    match = SETTINGS_LIMIT_MENU_DATA_PATTERN.fullmatch(callback_query.data)

    if match is None:
        await callback_query.answer()
        return

    chat_id = int(match.group("chat_id"))
    limit_type = match.group("limit_type")
    requester_user_id = _get_bot_info_requester_user_id(match)
    language = _resolve_settings_language(update)

    if not await _can_manage_settings(update, context, chat_id):
        await callback_query.answer(
            text=get_message("settings_admin_only", language=language),
        )
        return

    settings = get_group_settings(chat_id)
    active_limit = (
        settings.max_crypto_pairs_per_message
        if limit_type == "crypto"
        else settings.max_time_matches_per_message
    )
    setting_name = get_message(
        (
            "settings_max_crypto_button"
            if limit_type == "crypto"
            else "settings_max_time_button"
        ),
        language=language,
    )
    await callback_query.answer()

    if isinstance(callback_query.message, Message):
        await callback_query.message.edit_text(
            text=get_message(
                "settings_limit_menu",
                language=language,
                setting_name=setting_name,
            ),
            parse_mode=ParseMode.HTML,
            reply_markup=build_settings_limit_keyboard(
                chat_id,
                limit_type,
                active_limit,
                requester_user_id=requester_user_id,
            ),
        )


async def handle_settings_set_limit_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Persist one message limit and return to settings home."""
    callback_query = update.callback_query

    if callback_query is None or callback_query.data is None:
        return

    match = SETTINGS_SET_LIMIT_DATA_PATTERN.fullmatch(callback_query.data)

    if match is None:
        await callback_query.answer()
        return

    chat_id = int(match.group("chat_id"))
    limit_type = match.group("limit_type")
    limit = int(match.group("limit"))
    requester_user_id = _get_bot_info_requester_user_id(match)
    language = _resolve_settings_language(update)

    if (
        limit not in ALLOWED_MESSAGE_LIMITS
        or not await _can_manage_settings(update, context, chat_id)
    ):
        await callback_query.answer(
            text=get_message("settings_admin_only", language=language),
        )
        return

    update_group_setting(
        chat_id,
        (
            "max_crypto_pairs_per_message"
            if limit_type == "crypto"
            else "max_time_matches_per_message"
        ),
        limit,
    )
    await callback_query.answer()

    if isinstance(callback_query.message, Message):
        await _edit_to_settings_home(
            callback_query.message,
            chat_id,
            language,
            requester_user_id=requester_user_id,
        )


async def handle_settings_default_limit_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Reset one message limit to the configured default."""
    callback_query = update.callback_query

    if callback_query is None or callback_query.data is None:
        return

    match = SETTINGS_DEFAULT_LIMIT_DATA_PATTERN.fullmatch(
        callback_query.data
    )

    if match is None:
        await callback_query.answer()
        return

    chat_id = int(match.group("chat_id"))
    limit_type = match.group("limit_type")
    requester_user_id = _get_bot_info_requester_user_id(match)
    language = _resolve_settings_language(update)

    if not await _can_manage_settings(update, context, chat_id):
        await callback_query.answer(
            text=get_message("settings_admin_only", language=language),
        )
        return

    update_group_setting(
        chat_id,
        (
            "max_crypto_pairs_per_message"
            if limit_type == "crypto"
            else "max_time_matches_per_message"
        ),
        None,
    )
    await callback_query.answer()

    if isinstance(callback_query.message, Message):
        await _edit_to_settings_home(
            callback_query.message,
            chat_id,
            language,
            requester_user_id=requester_user_id,
        )


async def handle_delete_settings_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Delete one settings menu message when requested by a group admin."""
    callback_query = update.callback_query

    if callback_query is None:
        return

    chat_id = _get_callback_chat_id(
        callback_query.data,
        DELETE_SETTINGS_DATA_PATTERN,
    )
    language = _resolve_settings_language(update)

    if chat_id is None or not await _can_manage_settings(
        update,
        context,
        chat_id,
    ):
        await callback_query.answer(
            text=get_message("settings_admin_only", language=language),
        )
        return

    await callback_query.answer()

    if not isinstance(callback_query.message, Message):
        return

    try:
        await callback_query.message.delete()
    except TelegramError as error:
        LOGGER.warning(
            "Settings menu deletion failed: %s | chat_id=%s, message_id=%s",
            error,
            callback_query.message.chat_id,
            callback_query.message.message_id,
        )
