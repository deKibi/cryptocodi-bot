# telegram_bot/services/delete_authorization.py

# Standard Libraries
import logging
from typing import Final

# Third-party Libraries
from telegram.constants import ChatMemberStatus, ChatType
from telegram.error import TelegramError
from telegram.ext import ContextTypes


LOGGER = logging.getLogger(__name__)
GROUP_ADMIN_STATUSES: Final[frozenset[str]] = frozenset(
    {ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR}
)


async def can_delete_bot_response(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    chat_type: str,
    requester_user_id: int,
    acting_user_id: int,
) -> bool:
    """Return whether a user may delete one requested bot response."""
    if acting_user_id == requester_user_id:
        return True

    if chat_type not in {ChatType.GROUP, ChatType.SUPERGROUP}:
        return False

    try:
        administrators = await context.bot.get_chat_administrators(chat_id)
    except TelegramError as error:
        LOGGER.warning(
            "Bot response deletion authorization failed: %s | "
            "chat_id=%s, user_id=%s",
            error,
            chat_id,
            acting_user_id,
        )
        return False

    return any(
        member.user.id == acting_user_id
        and member.status in GROUP_ADMIN_STATUSES
        for member in administrators
    )
