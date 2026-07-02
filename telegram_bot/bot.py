# telegram_bot/bot.py

# Standard Libraries
import logging
import time
from typing import Final, Optional

# Third-party Libraries
from telegram import BotCommand, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Custom Modules
from config import (
    COINGECKO_REQUESTS_PER_DAY,
    CRYPTO_CONVERSIONS_PER_USER_PER_DAY,
    MAX_CRYPTO_PAIRS_PER_MESSAGE,
    PRIORITY_GROUP_CONVERT_LIMIT,
    PRIORITY_GROUPS_ID,
    PRIORITY_USER_CONVERT_LIMIT,
    PRIORITY_USERS_ID,
    TELEGRAM_BOT_TOKEN,
    log_configuration_warnings,
)
from telegram_bot.handlers.crypto_message_handler import handle_crypto_message
from telegram_bot.handlers.time_message_handler import handle_time_message
from telegram_bot.logging_config import (
    configure_logging,
    format_log_metadata,
    get_update_metadata,
)


LOGGER = logging.getLogger(__name__)
STARTUP_DELAY_SECONDS: Final[int] = 5

START_MESSAGE = """Привіт! Це @cryptocodi bot.

<b>Що бот вміє зараз:</b>
• знаходити UTC-час у повідомленнях і переводити його в Kyiv та CET (центральноєвропейський час, Vien)
• знаходити суми криптовалют у повідомленнях і приблизно переводити їх в USD та UAH.

<b>Приклади:</b>

<code>10:00 UTC</code>
<code>0.3 BNB</code>
<code>25k USDT</code>

Автор: @deKibi
Канал: @cryptocodi

<b>Донати:</b>
EVM: <code>0x5F762ed1B0d2328A3639D609D24A67FDEf0804C6</code>
SOL: <code>AbmqpL1WkhxfUnRza5pNcxXZHYFzTsThjY1kEZLoBBGJ</code>"""

BOT_COMMANDS = [
    BotCommand("start", "Show bot info and supported formats"),
]


def _format_configured_ids(configured_ids: frozenset[int]) -> str:
    if not configured_ids:
        return "not configured"

    return ", ".join(str(identifier) for identifier in sorted(configured_ids))


def _format_optional_limit(limit: Optional[int]) -> str:
    if limit is None:
        return "not configured"

    return str(limit)


def log_startup_configuration() -> None:
    """Log non-sensitive bot settings before Telegram polling starts."""
    LOGGER.info(
        "Startup configuration:\n"
        "  CoinGecko requests per UTC day: %d\n"
        "  Conversions per user per UTC day: %d\n"
        "  Maximum crypto pairs per message: %d\n"
        "  Priority group IDs: %s\n"
        "  Priority group conversion limit: %s\n"
        "  Priority user IDs: %s\n"
        "  Priority user conversion limit: %s",
        COINGECKO_REQUESTS_PER_DAY,
        CRYPTO_CONVERSIONS_PER_USER_PER_DAY,
        MAX_CRYPTO_PAIRS_PER_MESSAGE,
        _format_configured_ids(PRIORITY_GROUPS_ID),
        _format_optional_limit(PRIORITY_GROUP_CONVERT_LIMIT),
        _format_configured_ids(PRIORITY_USERS_ID),
        _format_optional_limit(PRIORITY_USER_CONVERT_LIMIT),
    )


async def setup_bot_commands(application: Application) -> None:
    """Register Telegram command descriptions for command autocomplete."""
    await application.bot.set_my_commands(BOT_COMMANDS)
    LOGGER.info("Telegram bot commands registered.")


async def start_command(
    update: Update,
    _context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Send the bot start message with supported formats and project links."""
    message = update.effective_message
    metadata = get_update_metadata(update)

    LOGGER.info(
        "Command received: /start | %s",
        format_log_metadata(metadata),
    )

    if message is None:
        return

    await message.reply_text(START_MESSAGE, parse_mode="HTML")


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
    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(setup_bot_commands)
        .build()
    )
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
    LOGGER.info("Configuration loaded and validated.")
    log_startup_configuration()
    log_configuration_warnings()
    LOGGER.info(
        "Telegram polling starts in %d seconds. Press Ctrl+C to cancel.",
        STARTUP_DELAY_SECONDS,
    )

    try:
        time.sleep(STARTUP_DELAY_SECONDS)
    except KeyboardInterrupt:
        LOGGER.info("Bot startup cancelled by user.")
        return

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
