# telegram_bot/bot.py

# Standard Libraries
import logging

# Third-party Libraries
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Custom Modules
from config import TELEGRAM_BOT_TOKEN
from telegram_bot.handlers.crypto_message_handler import handle_crypto_message
from telegram_bot.handlers.time_message_handler import handle_time_message
from telegram_bot.logging_config import (
    configure_logging,
    format_log_metadata,
    get_update_metadata,
)


LOGGER = logging.getLogger(__name__)


async def start_command(
    update: Update,
    _context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Explain the supported UTC time formats to the user."""
    message = update.effective_message
    metadata = get_update_metadata(update)

    LOGGER.info(
        "Command received: /start | %s",
        format_log_metadata(metadata),
    )

    if message is None:
        return

    await message.reply_text(
        "Надішліть час у форматі 10:00 UTC, 10:00UTC або 10 UTC."
    )


async def handle_error(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Log unhandled errors raised while processing Telegram updates."""
    metadata_text = "update_metadata_unavailable"

    if isinstance(update, Update):
        metadata_text = format_log_metadata(get_update_metadata(update))

    error = context.error

    if error is None:
        LOGGER.error("Unhandled Telegram update error | %s", metadata_text)
        return

    LOGGER.error(
        "Unhandled Telegram update error | %s",
        metadata_text,
        exc_info=(type(error), error, error.__traceback__),
    )


def create_application() -> Application:
    """Create and configure the Telegram bot application."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    supported_chats = filters.ChatType.PRIVATE | filters.ChatType.GROUPS

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(
        MessageHandler(
            supported_chats
            & (filters.TEXT | filters.CAPTION)
            & ~filters.COMMAND,
            handle_time_message,
        )
    )
    application.add_handler(
        MessageHandler(
            supported_chats
            & (filters.TEXT | filters.CAPTION)
            & ~filters.COMMAND,
            handle_crypto_message,
        ),
        group=1,
    )
    application.add_error_handler(handle_error)

    return application


def run_bot() -> None:
    """Run the Telegram bot using long polling."""
    configure_logging()
    LOGGER.info("Bot started.")

    try:
        application = create_application()
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception:
        LOGGER.exception("Bot startup or polling failed.")
        raise
    finally:
        LOGGER.info("Bot stopped.")


if __name__ == "__main__":
    run_bot()
