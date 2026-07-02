# telegram_bot/handlers/calculator_message_handler.py

# Standard Libraries
import html
import logging

# Third-party Libraries
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

# Custom Modules
from calculator.calculator import CalculatorError, calculate
from calculator.expression_parser import parse_expression
from telegram_bot.logging_config import (
    format_log_metadata,
    get_update_metadata,
    log_detected_calculation,
)


LOGGER = logging.getLogger(__name__)
CALCULATION_ERROR_MESSAGE = "Не вдалося обчислити вираз."


def format_calculation_response(
    expression: str,
    result: int | float,
) -> str:
    """Format a calculation expression and result for a Telegram reply."""
    compact_expression = "".join(expression.split())

    return (
        f"<b>{html.escape(compact_expression)}</b> = "
        f"<code>{html.escape(str(result))}</code>"
    )


async def handle_calculator_message(
    update: Update,
    _context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Reply with a result when the entire message is an expression."""
    message = update.effective_message

    if message is None:
        return

    message_text = message.text or message.caption

    if message_text is None:
        return

    expression = parse_expression(message_text)

    if expression is None:
        return

    metadata = get_update_metadata(update)
    metadata_text = format_log_metadata(metadata)

    LOGGER.info(
        "Calculator expression detected: %r | %s",
        expression,
        metadata_text,
    )

    try:
        result = calculate(expression)
    except CalculatorError as error:
        LOGGER.warning(
            "Calculation failed: expression=%r, error=%s | %s",
            expression,
            error,
            metadata_text,
        )
        await message.reply_text(
            text=CALCULATION_ERROR_MESSAGE,
            do_quote=True,
        )
        LOGGER.info("Calculation error reply sent | %s", metadata_text)
        return

    log_detected_calculation(
        {
            "chat_type": metadata["chat_type"],
            "expression": expression,
            "result": result,
        }
    )

    await message.reply_text(
        text=format_calculation_response(expression, result),
        parse_mode=ParseMode.HTML,
        do_quote=True,
    )

    LOGGER.info(
        "Calculation reply sent: expression=%r, result=%r | %s",
        expression,
        result,
        metadata_text,
    )
