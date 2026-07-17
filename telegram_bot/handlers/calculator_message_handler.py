# telegram_bot/handlers/calculator_message_handler.py

# Standard Libraries
import html
import logging

# Third-party Libraries
from telegram import Update
from telegram.constants import ParseMode
from telegram.error import TelegramError
from telegram.ext import ContextTypes

# Custom Modules
from calculator.calculator import CalculatorError, calculate
from calculator.expression_parser import (
    ALTERNATIVE_OPERATORS,
    parse_expression,
)
from telegram_bot.localization.language_preferences import (
    DEFAULT_LANGUAGE,
    resolve_context_language,
)
from telegram_bot.localization.messages import get_message
from telegram_bot.logging_config import (
    format_log_metadata,
    get_update_metadata,
    log_detected_calculation,
)
from telegram_bot.services.number_formatter import format_large_number
from telegram_bot.state.message_reply_tracker import (
    forget_related_reply_message_id,
    get_related_reply_message_id,
    remember_related_reply_message_id,
)
from telegram_bot.settings.group_settings import get_effective_chat_settings
from telegram_bot.state.message_signature_tracker import (
    forget_message_signature,
    is_message_signature_unchanged,
    remember_message_signature,
)


LOGGER = logging.getLogger(__name__)
CALCULATOR_MESSAGE_FEATURE = "calculator"
MAX_VISIBLE_DECIMAL_PLACES = 5


def _get_visible_fraction(fractional_part: str) -> str:
    visible_fraction = fractional_part[:MAX_VISIBLE_DECIMAL_PLACES].rstrip("0")

    if visible_fraction:
        return visible_fraction

    for index, digit in enumerate(
        fractional_part[MAX_VISIBLE_DECIMAL_PLACES:],
        start=MAX_VISIBLE_DECIMAL_PLACES,
    ):
        if digit != "0":
            return fractional_part[:index + 1].rstrip("0")

    return ""


def _format_calculation_result(result: int | float) -> str:
    if isinstance(result, float) and result.is_integer():
        formatted_result = str(int(result))
    elif isinstance(result, float):
        integer_part, _separator, fractional_part = format(
            result,
            ".15f",
        ).partition(".")
        formatted_fraction = _get_visible_fraction(fractional_part)
        formatted_result = integer_part

        if formatted_fraction:
            formatted_result = f"{formatted_result}.{formatted_fraction}"
    else:
        formatted_result = str(result)

    if formatted_result == "-0":
        formatted_result = "0"

    return format_large_number(formatted_result)


def format_calculation_response(
    expression: str,
    result: int | float,
    language: str = DEFAULT_LANGUAGE,
) -> str:
    """Format a calculation expression and result for a Telegram reply."""
    compact_expression = "".join(expression.split())
    formatted_result = _format_calculation_result(result)

    return get_message(
        "calculation_response",
        language=language,
        expression=html.escape(compact_expression),
        result=html.escape(formatted_result),
    )


async def _cleanup_tracked_calculator_response(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    source_message_id: int,
) -> None:
    related_reply_message_id = get_related_reply_message_id(
        context.bot_data,
        CALCULATOR_MESSAGE_FEATURE,
        chat_id,
        source_message_id,
    )

    if related_reply_message_id is not None:
        try:
            await context.bot.delete_message(
                chat_id=chat_id,
                message_id=related_reply_message_id,
            )
        except TelegramError as error:
            LOGGER.warning(
                "Stale calculation response deletion failed: %s | "
                "chat_id=%s, source_message_id=%s",
                error,
                chat_id,
                source_message_id,
            )

    forget_related_reply_message_id(
        context.bot_data,
        CALCULATOR_MESSAGE_FEATURE,
        chat_id,
        source_message_id,
    )
    forget_message_signature(
        context.bot_data,
        CALCULATOR_MESSAGE_FEATURE,
        chat_id,
        source_message_id,
    )


async def handle_calculator_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Reply with a result when the entire message is an expression."""
    message = update.effective_message

    if message is None:
        return

    message_text = message.text or message.caption

    if message_text is None:
        return

    chat = update.effective_chat

    if chat is None:
        return

    settings = get_effective_chat_settings(chat.id, chat.type)

    if not settings.calculator_enabled:
        await _cleanup_tracked_calculator_response(
            context,
            chat.id,
            message.message_id,
        )
        return

    expression = parse_expression(message_text)
    display_expression = message_text.strip().translate(
        ALTERNATIVE_OPERATORS
    )

    if expression is None:
        forget_message_signature(
            context.bot_data,
            CALCULATOR_MESSAGE_FEATURE,
            chat.id,
            message.message_id,
        )
        return

    user = update.effective_user
    language = resolve_context_language(
        chat.id,
        chat.type,
        user.id if user is not None else None,
        user.language_code if user is not None else None,
    )
    expression_signature = ("".join(expression.split()), language)

    if is_message_signature_unchanged(
        context.bot_data,
        CALCULATOR_MESSAGE_FEATURE,
        chat.id,
        message.message_id,
        expression_signature,
    ):
        return

    metadata = get_update_metadata(update)
    metadata_text = format_log_metadata(metadata)

    LOGGER.info(
        "Calculator expression detected: %r | %s",
        display_expression,
        metadata_text,
    )

    try:
        result = calculate(expression)
    except CalculatorError as error:
        error_message = get_message("calculation_error", language=language)
        LOGGER.warning(
            "Calculation failed: expression=%r, error=%s | %s",
            display_expression,
            error,
            metadata_text,
        )
        related_reply_message_id = get_related_reply_message_id(
            context.bot_data,
            CALCULATOR_MESSAGE_FEATURE,
            chat.id,
            message.message_id,
        )

        if related_reply_message_id is None:
            reply_message = await message.reply_text(
                text=error_message,
                do_quote=True,
            )
            remember_related_reply_message_id(
                context.bot_data,
                CALCULATOR_MESSAGE_FEATURE,
                chat.id,
                message.message_id,
                reply_message.message_id,
            )
            LOGGER.info("Calculation error reply sent | %s", metadata_text)
        else:
            await context.bot.edit_message_text(
                chat_id=chat.id,
                message_id=related_reply_message_id,
                text=error_message,
            )
            LOGGER.info("Calculation error reply updated | %s", metadata_text)

        remember_message_signature(
            context.bot_data,
            CALCULATOR_MESSAGE_FEATURE,
            chat.id,
            message.message_id,
            expression_signature,
        )
        return

    log_detected_calculation(
        {
            "chat_type": metadata["chat_type"],
            "expression": display_expression,
            "result": result,
        }
    )

    response_text = format_calculation_response(
        display_expression,
        result,
        language,
    )
    related_reply_message_id = get_related_reply_message_id(
        context.bot_data,
        CALCULATOR_MESSAGE_FEATURE,
        chat.id,
        message.message_id,
    )

    if related_reply_message_id is None:
        reply_message = await message.reply_text(
            text=response_text,
            parse_mode=ParseMode.HTML,
            do_quote=True,
        )
        remember_related_reply_message_id(
            context.bot_data,
            CALCULATOR_MESSAGE_FEATURE,
            chat.id,
            message.message_id,
            reply_message.message_id,
        )
        LOGGER.info(
            "Calculation reply sent: expression=%r, result=%r | %s",
            display_expression,
            result,
            metadata_text,
        )
    else:
        await context.bot.edit_message_text(
            chat_id=chat.id,
            message_id=related_reply_message_id,
            text=response_text,
            parse_mode=ParseMode.HTML,
        )
        LOGGER.info(
            "Calculation reply updated: expression=%r, result=%r | %s",
            display_expression,
            result,
            metadata_text,
        )

    remember_message_signature(
        context.bot_data,
        CALCULATOR_MESSAGE_FEATURE,
        chat.id,
        message.message_id,
        expression_signature,
    )
