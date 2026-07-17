# telegram_bot/services/temporary_message_service.py

# Standard Libraries
import asyncio
import logging
from typing import Final, Optional

# Third-party Libraries
from telegram import Message, Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes


# Temporary messages
DEFAULT_TEMPORARY_MESSAGE_TTL_SECONDS: Final[int] = 15

LOGGER = logging.getLogger(__name__)


async def delete_temporary_message(
    message: Message,
    delay_seconds: int = DEFAULT_TEMPORARY_MESSAGE_TTL_SECONDS,
    log_label: str = "Temporary message",
) -> None:
    """Delete a bot message after a short delay without raising to handlers."""
    await asyncio.sleep(delay_seconds)

    try:
        await message.delete()
    except TelegramError as error:
        LOGGER.warning(
            "%s deletion failed: %s | chat_id=%s, message_id=%s",
            log_label,
            error,
            message.chat_id,
            message.message_id,
        )


async def send_temporary_message(
    message: Message,
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
    delay_seconds: int = DEFAULT_TEMPORARY_MESSAGE_TTL_SECONDS,
    task_name: str = "delete-temporary-message",
    log_label: str = "Temporary message",
    do_quote: bool = True,
    update: Optional[Update] = None,
) -> Message:
    """Send a reply and schedule deletion of that bot reply."""
    notice_message = await message.reply_text(
        text=text,
        do_quote=do_quote,
    )
    delete_task = delete_temporary_message(
        notice_message,
        delay_seconds=delay_seconds,
        log_label=log_label,
    )

    if update is None:
        context.application.create_task(
            delete_task,
            name=task_name,
        )
    else:
        context.application.create_task(
            delete_task,
            update=update,
            name=task_name,
        )

    return notice_message
