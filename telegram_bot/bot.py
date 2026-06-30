# telegram_bot/bot.py

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
from telegram_bot.handlers.time_message_handler import handle_time_message


async def start_command(
    update: Update,
    _context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Explain the supported UTC time formats to the user."""
    message = update.effective_message

    if message is None:
        return

    await message.reply_text(
        "Надішліть час у форматі 10:00 UTC, 10:00UTC або 10 UTC."
    )


def create_application() -> Application:
    """Create and configure the Telegram bot application."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    supported_chats = filters.ChatType.PRIVATE | filters.ChatType.GROUPS

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(
        MessageHandler(
            supported_chats & filters.TEXT & ~filters.COMMAND,
            handle_time_message,
        )
    )

    return application


def run_bot() -> None:
    """Run the Telegram bot using long polling."""
    application = create_application()
    print("CRYPTO CODER bot started.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run_bot()
