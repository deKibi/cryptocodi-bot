# telegram_bot/bot.py

# Standard Libraries
import logging
import time
from typing import Final, Optional

# Third-party Libraries
from telegram import BotCommand, Update
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
    COINGECKO_REQUESTS_PER_DAY_IS_CONFIGURED,
    CRYPTO_CONVERSIONS_PER_USER_PER_DAY,
    CRYPTO_CONVERSIONS_PER_USER_PER_DAY_IS_CONFIGURED,
    CRYPTO_MAX_MARKET_CAP_RANK,
    CRYPTO_MAX_MARKET_CAP_RANK_IS_CONFIGURED,
    DEFAULT_COINGECKO_REQUESTS_PER_DAY,
    DEFAULT_CRYPTO_CONVERSIONS_PER_USER_PER_DAY,
    DEFAULT_CRYPTO_MAX_MARKET_CAP_RANK,
    DEFAULT_MAX_CRYPTO_PAIRS_PER_MESSAGE,
    DEFAULT_MAX_TIME_MATCHES_PER_MESSAGE,
    MAX_CRYPTO_PAIRS_PER_MESSAGE,
    MAX_CRYPTO_PAIRS_PER_MESSAGE_IS_CONFIGURED,
    MAX_TIME_MATCHES_PER_MESSAGE,
    MAX_TIME_MATCHES_PER_MESSAGE_IS_CONFIGURED,
    PRIORITY_GROUP_CONVERT_LIMIT,
    PRIORITY_GROUPS_ID,
    PRIORITY_USER_CONVERT_LIMIT,
    PRIORITY_USERS_ID,
    TELEGRAM_BOT_TOKEN,
    log_configuration_warnings,
)
from telegram_bot.handlers.bot_info_callback_handler import (
    DELETE_BOT_INFO_CALLBACK_PATTERN,
    handle_delete_bot_info_callback,
)
from telegram_bot.handlers.calculator_message_handler import (
    handle_calculator_message,
)
from telegram_bot.handlers.crypto_message_handler import (
    handle_crypto_message,
    handle_delete_crypto_response,
)
from telegram_bot.handlers.id_command_handler import (
    handle_find_different_id_callback,
    handle_id_command,
    handle_shared_id_entity,
)
from telegram_bot.handlers.language_callback_handler import (
    BACK_TO_LANGUAGE_SETTINGS_CALLBACK_PATTERN,
    CHANGE_LANGUAGE_CALLBACK_PATTERN,
    SET_LANGUAGE_CALLBACK_PATTERN,
    handle_back_to_language_settings_callback,
    handle_change_language_callback,
    handle_language_command,
    handle_set_language_callback,
)
from telegram_bot.handlers.settings_command_handler import (
    DELETE_SETTINGS_CALLBACK_PATTERN,
    SETTINGS_BACK_CALLBACK_PATTERN,
    SETTINGS_HOME_CALLBACK_PATTERN,
    SETTINGS_LIMIT_MENU_CALLBACK_PATTERN,
    SETTINGS_SET_LIMIT_CALLBACK_PATTERN,
    SETTINGS_TOGGLE_CALLBACK_PATTERN,
    handle_delete_settings_callback,
    handle_settings_back_callback,
    handle_settings_command,
    handle_settings_home_callback,
    handle_settings_limit_menu_callback,
    handle_settings_set_limit_callback,
    handle_settings_toggle_callback,
)
from telegram_bot.handlers.time_message_handler import handle_time_message
from telegram_bot.keyboards.crypto_conversion_keyboard import (
    DELETE_CRYPTO_RESPONSE_CALLBACK,
)
from telegram_bot.keyboards.id_keyboard import FIND_DIFFERENT_ID_CALLBACK
from telegram_bot.keyboards.language_keyboard import (
    build_change_language_keyboard,
)
from telegram_bot.localization.language_preferences import (
    GROUP_CHAT_TYPES,
    USER_LANGUAGE_SCOPE,
    get_language_scope,
    initialize_chat_language,
    resolve_context_language,
    resolve_user_language,
)
from telegram_bot.localization.messages import get_message
from telegram_bot.logging_config import (
    configure_logging,
    format_log_metadata,
    get_update_metadata,
)
from telegram_bot.services.bot_invitation import (
    build_bot_invitation_url,
    parse_bot_inviter_user_id,
)


LOGGER = logging.getLogger(__name__)
STARTUP_DELAY_SECONDS: Final[int] = 3

BOT_COMMANDS = [
    BotCommand("start", get_message("command_start")),
    BotCommand("help", get_message("command_help")),
    BotCommand("id", get_message("command_id")),
    BotCommand("language", get_message("command_language")),
    BotCommand("settings", get_message("command_settings")),
]


def _format_configured_ids(configured_ids: frozenset[int]) -> str:
    if not configured_ids:
        return "not configured"

    return ", ".join(str(identifier) for identifier in sorted(configured_ids))


def _format_priority_subjects(configured_ids: frozenset[int]) -> str:
    if not configured_ids:
        return "not configured (disabled)"

    return _format_configured_ids(configured_ids)


def _format_priority_limit(
    configured_ids: frozenset[int],
    limit: Optional[int],
) -> str:
    if not configured_ids and limit is None:
        return "not configured (unused)"

    if not configured_ids:
        return f"{limit} (unused; priority IDs not configured)"

    if limit is None:
        return "not configured (using standard user limit)"

    return str(limit)


def _format_default_backed_value(
    value: int,
    default: int,
    is_configured: bool,
) -> str:
    if is_configured:
        return str(value)

    return f"not configured (using {default} default)"


def log_startup_configuration() -> None:
    """Log non-sensitive bot settings before Telegram polling starts."""
    LOGGER.info(
        "Startup configuration:\n"
        "  CoinGecko requests per UTC day: %s\n"
        "  Conversions per user per UTC day: %s\n"
        "  Maximum crypto pairs per message: %s\n"
        "  Maximum time matches per message: %s\n"
        "  In-message ticker rank limit: %s\n"
        "  Priority groups: %s\n"
        "  Priority group conversion limit: %s\n"
        "  Priority users: %s\n"
        "  Priority user conversion limit: %s",
        _format_default_backed_value(
            COINGECKO_REQUESTS_PER_DAY,
            DEFAULT_COINGECKO_REQUESTS_PER_DAY,
            COINGECKO_REQUESTS_PER_DAY_IS_CONFIGURED,
        ),
        _format_default_backed_value(
            CRYPTO_CONVERSIONS_PER_USER_PER_DAY,
            DEFAULT_CRYPTO_CONVERSIONS_PER_USER_PER_DAY,
            CRYPTO_CONVERSIONS_PER_USER_PER_DAY_IS_CONFIGURED,
        ),
        _format_default_backed_value(
            MAX_CRYPTO_PAIRS_PER_MESSAGE,
            DEFAULT_MAX_CRYPTO_PAIRS_PER_MESSAGE,
            MAX_CRYPTO_PAIRS_PER_MESSAGE_IS_CONFIGURED,
        ),
        _format_default_backed_value(
            MAX_TIME_MATCHES_PER_MESSAGE,
            DEFAULT_MAX_TIME_MATCHES_PER_MESSAGE,
            MAX_TIME_MATCHES_PER_MESSAGE_IS_CONFIGURED,
        ),
        _format_default_backed_value(
            CRYPTO_MAX_MARKET_CAP_RANK,
            DEFAULT_CRYPTO_MAX_MARKET_CAP_RANK,
            CRYPTO_MAX_MARKET_CAP_RANK_IS_CONFIGURED,
        ),
        _format_priority_subjects(PRIORITY_GROUPS_ID),
        _format_priority_limit(
            PRIORITY_GROUPS_ID,
            PRIORITY_GROUP_CONVERT_LIMIT,
        ),
        _format_priority_subjects(PRIORITY_USERS_ID),
        _format_priority_limit(
            PRIORITY_USERS_ID,
            PRIORITY_USER_CONVERT_LIMIT,
        ),
    )


async def setup_bot_commands(application: Application) -> None:
    """Register Telegram command descriptions for command autocomplete."""
    await application.bot.set_my_commands(BOT_COMMANDS)
    LOGGER.info("Telegram bot commands registered.")


async def _send_bot_info(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
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

    user = update.effective_user
    chat = update.effective_chat
    language = resolve_context_language(
        chat.id if chat is not None else None,
        chat.type if chat is not None else None,
        user.id if user is not None else None,
        user.language_code if user is not None else None,
    )
    language_scope = get_language_scope(
        chat.id if chat is not None else None,
        chat.type if chat is not None else None,
        user.id if user is not None else None,
    )
    invite_url = (
        build_bot_invitation_url(context.bot.username, user.id)
        if language_scope is not None
        and language_scope[0] == USER_LANGUAGE_SCOPE
        and user is not None
        else None
    )
    response_keyboard = (
        build_change_language_keyboard(
            *language_scope,
            user.id,
            invite_url=invite_url,
        )
        if language_scope is not None and user is not None
        else None
    )
    await message.reply_text(
        get_message("bot_info", language=language),
        parse_mode="HTML",
        reply_markup=response_keyboard,
    )


async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Send bot information for the start command."""
    chat = update.effective_chat
    user = update.effective_user
    inviter_user_id = parse_bot_inviter_user_id(context.args or ())

    if (
        chat is not None
        and chat.type in GROUP_CHAT_TYPES
        and user is not None
        and inviter_user_id == user.id
    ):
        inviter_language = resolve_user_language(
            user.id,
            user.language_code,
        )
        if initialize_chat_language(chat.id, inviter_language):
            LOGGER.info(
                "Invited group language initialized | "
                "chat_id=%s, inviter_user_id=%s, language=%s",
                chat.id,
                user.id,
                inviter_language,
            )

    await _send_bot_info(update, context, "start")


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Send bot information for the help command."""
    await _send_bot_info(update, context, "help")


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
            "language",
            handle_language_command,
            filters=supported_chats,
        )
    )
    application.add_handler(
        CommandHandler(
            "settings",
            handle_settings_command,
            filters=supported_chats,
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            handle_change_language_callback,
            pattern=CHANGE_LANGUAGE_CALLBACK_PATTERN,
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            handle_back_to_language_settings_callback,
            pattern=BACK_TO_LANGUAGE_SETTINGS_CALLBACK_PATTERN,
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            handle_set_language_callback,
            pattern=SET_LANGUAGE_CALLBACK_PATTERN,
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            handle_settings_home_callback,
            pattern=SETTINGS_HOME_CALLBACK_PATTERN,
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            handle_settings_back_callback,
            pattern=SETTINGS_BACK_CALLBACK_PATTERN,
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            handle_settings_toggle_callback,
            pattern=SETTINGS_TOGGLE_CALLBACK_PATTERN,
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            handle_settings_limit_menu_callback,
            pattern=SETTINGS_LIMIT_MENU_CALLBACK_PATTERN,
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            handle_settings_set_limit_callback,
            pattern=SETTINGS_SET_LIMIT_CALLBACK_PATTERN,
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            handle_delete_settings_callback,
            pattern=DELETE_SETTINGS_CALLBACK_PATTERN,
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            handle_delete_bot_info_callback,
            pattern=DELETE_BOT_INFO_CALLBACK_PATTERN,
        )
    )
    application.add_handler(
        CommandHandler("id", handle_id_command, filters=supported_chats)
    )
    application.add_handler(
        CallbackQueryHandler(
            handle_find_different_id_callback,
            pattern=f"^{FIND_DIFFERENT_ID_CALLBACK}$",
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
            filters.ChatType.PRIVATE
            & (
                filters.StatusUpdate.CHAT_SHARED
                | filters.StatusUpdate.USERS_SHARED
            ),
            handle_shared_id_entity,
        )
    )
    application.add_handler(
        MessageHandler(
            supported_chats
            & (filters.TEXT | filters.CAPTION)
            & ~filters.COMMAND,
            handle_crypto_message,
        )
    )
    application.add_handler(
        MessageHandler(
            supported_chats
            & (filters.TEXT | filters.CAPTION)
            & ~filters.COMMAND,
            handle_time_message,
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
