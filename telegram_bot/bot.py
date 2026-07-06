# telegram_bot/bot.py

# Standard Libraries
import logging
import time
from html import escape
from typing import Final, Optional

# Third-party Libraries
from telegram import BotCommand, Chat, Update, User
from telegram.ext import (
    Application,
    CallbackQueryHandler,
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
from telegram_bot.services.account_creation_date import (
    estimate_account_creation_month,
)
from telegram_bot.handlers.calculator_message_handler import (
    handle_calculator_message,
)
from telegram_bot.handlers.crypto_message_handler import (
    handle_crypto_message,
    handle_delete_crypto_response,
)
from telegram_bot.keyboards.crypto_conversion_keyboard import (
    DELETE_CRYPTO_RESPONSE_CALLBACK,
)
from telegram_bot.handlers.time_message_handler import handle_time_message
from telegram_bot.logging_config import (
    configure_logging,
    format_log_metadata,
    get_update_metadata,
)


LOGGER = logging.getLogger(__name__)
STARTUP_DELAY_SECONDS: Final[int] = 3

BOT_INFO_MESSAGE = """Привіт! Це @cryptocodi bot.

<b>Що бот вміє зараз:</b>
• знаходити UTC-час у повідомленнях і переводити його в Kyiv та CET (центральноєвропейський час, Vien)
• знаходити суми криптовалют у повідомленнях і приблизно переводити їх в USD та UAH
• обчислювати прості математичні вирази.

<b>Приклади:</b>

<code>10:00 UTC</code>
<code>0.3 BNB</code>
<code>25k USDT</code>
<code>(10 + 5) / 3</code>

Автор: @deKibi
Канал: @cryptocodi

Вихідний код: <a href="https://github.com/deKibi/cryptocodi-bot">GitHub</a>"""

BOT_COMMANDS = [
    BotCommand("start", "Show bot info and supported formats"),
    BotCommand("help", "Show bot help and usage examples"),
    BotCommand("id", "Show chat and user IDs"),
]


def _format_configured_ids(configured_ids: frozenset[int]) -> str:
    if not configured_ids:
        return "not configured"

    return ", ".join(str(identifier) for identifier in sorted(configured_ids))


def _format_optional_limit(limit: Optional[int]) -> str:
    if limit is None:
        return "not configured"

    return str(limit)


def _format_id_value(
    value: Optional[object],
    prefix: str = "",
    monospace: bool = False,
) -> str:
    """Format an optional Telegram field for the ID command response."""
    if value is None or value == "":
        return "-"

    formatted_value = f"{escape(prefix)}{escape(str(value))}"

    if monospace:
        return f"<code>{formatted_value}</code>"

    return formatted_value


def _format_id_message(chat: Chat, user: User) -> str:
    """Format current chat and user details for the ID command."""
    creation_month = estimate_account_creation_month(user.id)

    return "\n".join(
        (
            "<b>CHAT:</b>",
            f"  <b>title:</b> {_format_id_value(chat.title)}",
            f"  <b>type:</b> {_format_id_value(chat.type, monospace=True)}",
            "  <b>username:</b> "
            f"{_format_id_value(chat.username, prefix='@')}",
            f"  <b>ID:</b> {_format_id_value(chat.id, monospace=True)}",
            "",
            "<b>YOU:</b>",
            f"  <b>first name:</b> {_format_id_value(user.first_name)}",
            f"  <b>last name:</b> {_format_id_value(user.last_name)}",
            "  <b>username:</b> "
            f"{_format_id_value(user.username, prefix='@')}",
            "  <b>language:</b> "
            f"{_format_id_value(user.language_code, monospace=True)}",
            f"  <b>ID:</b> {_format_id_value(user.id, monospace=True)}",
            "⭐<b>Creation date</b>⭐ <b>(approximately):</b> "
            f"{_format_id_value(creation_month, monospace=True)}",
        )
    )


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


async def _send_bot_info(
    update: Update,
    command_name: str,
) -> None:
    """Send shared bot information for an informational command."""
    message = update.effective_message
    metadata = get_update_metadata(update)

    LOGGER.info(
        "Command received: /%s | %s",
        command_name,
        format_log_metadata(metadata),
    )

    if message is None:
        return

    await message.reply_text(BOT_INFO_MESSAGE, parse_mode="HTML")


async def start_command(
    update: Update,
    _context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Send bot information for the start command."""
    await _send_bot_info(update, "start")


async def help_command(
    update: Update,
    _context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Send bot information for the help command."""
    await _send_bot_info(update, "help")


async def id_command(
    update: Update,
    _context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Send information about the current chat and command author."""
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    metadata = get_update_metadata(update)

    LOGGER.info(
        "Command received: /id | %s",
        format_log_metadata(metadata),
    )

    if message is None or chat is None or user is None:
        return

    await message.reply_text(
        _format_id_message(chat=chat, user=user),
        parse_mode="HTML",
        do_quote=True,
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
    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(setup_bot_commands)
        .build()
    )
    supported_chats = filters.ChatType.PRIVATE | filters.ChatType.GROUPS

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(
        CommandHandler(
            "id",
            id_command,
            filters=supported_chats & filters.UpdateType.MESSAGE,
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            handle_delete_crypto_response,
            pattern=f"^{DELETE_CRYPTO_RESPONSE_CALLBACK}$",
        )
    )
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
    application.add_handler(
        MessageHandler(
            supported_chats
            & (filters.TEXT | filters.CAPTION)
            & ~filters.COMMAND,
            handle_calculator_message,
        ),
        group=2,
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
