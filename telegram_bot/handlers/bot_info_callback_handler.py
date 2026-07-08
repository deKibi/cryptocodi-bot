# telegram_bot/handlers/bot_info_callback_handler.py

# Standard Libraries
import logging
import re
from typing import Final

# Third-party Libraries
from telegram import Message, Update
from telegram.constants import ChatMemberStatus, ChatType
from telegram.error import TelegramError
from telegram.ext import ContextTypes

# Custom Modules
from telegram_bot.keyboards.language_keyboard import (
    DELETE_BOT_INFO_CALLBACK_PREFIX,
)
from telegram_bot.localization.language_preferences import (
    resolve_context_language,
)
from telegram_bot.localization.messages import get_message


LOGGER = logging.getLogger(__name__)
DELETE_BOT_INFO_CALLBACK_PATTERN: Final[str] = (
    rf"^{DELETE_BOT_INFO_CALLBACK_PREFIX}:[1-9][0-9]*$"
)
DELETE_BOT_INFO_DATA_PATTERN: Final[re.Pattern[str]] = re.compile(
    rf"{DELETE_BOT_INFO_CALLBACK_PREFIX}:"
    r"(?P<requester_user_id>[1-9][0-9]*)"
)
GROUP_ADMIN_STATUSES: Final[frozenset[str]] = frozenset(
    {ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR}
)


async def _is_group_admin(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    user_id: int,
) -> bool:
    try:
        administrators = await context.bot.get_chat_administrators(chat_id)
    except TelegramError as error:
        LOGGER.warning(
            "Bot info deletion authorization failed: %s | "
            "chat_id=%s, user_id=%s",
            error,
            chat_id,
            user_id,
        )
        return False

    return any(
        member.user.id == user_id
        and member.status in GROUP_ADMIN_STATUSES
        for member in administrators
    )


async def handle_delete_bot_info_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Delete bot information for its requester or a group admin."""
    callback_query = update.callback_query
    chat = update.effective_chat
    user = update.effective_user

    if callback_query is None or chat is None or user is None:
        return

    match = DELETE_BOT_INFO_DATA_PATTERN.fullmatch(
        callback_query.data or "",
    )
    response_message = callback_query.message

    if match is None or not isinstance(response_message, Message):
        await callback_query.answer()
        LOGGER.warning("Bot info deletion skipped: callback is invalid")
        return

    requester_user_id = int(match.group("requester_user_id"))
    can_delete = user.id == requester_user_id

    if not can_delete and chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}:
        can_delete = await _is_group_admin(context, chat.id, user.id)

    if not can_delete:
        language = resolve_context_language(
            chat.id,
            chat.type,
            user.id,
            user.language_code,
        )
        await callback_query.answer(
            text=get_message("bot_info_delete_denied", language=language),
        )
        LOGGER.warning(
            "Bot info deletion denied | chat_id=%s, "
            "requester_user_id=%s, user_id=%s",
            chat.id,
            requester_user_id,
            user.id,
        )
        return

    await callback_query.answer()

    try:
        await response_message.delete()
    except TelegramError as error:
        LOGGER.warning(
            "Bot info deletion failed: %s | "
            "chat_id=%s, response_message_id=%s",
            error,
            response_message.chat_id,
            response_message.message_id,
        )
        return

    LOGGER.info(
        "Bot info deleted | chat_id=%s, response_message_id=%s, "
        "requester_user_id=%s, user_id=%s",
        response_message.chat_id,
        response_message.message_id,
        requester_user_id,
        user.id,
    )
