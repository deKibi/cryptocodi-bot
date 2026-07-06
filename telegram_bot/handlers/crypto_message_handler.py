# telegram_bot/handlers/crypto_message_handler.py

# Standard Libraries
import asyncio
import html
import logging
from decimal import ROUND_HALF_UP, Decimal

# Third-party Libraries
from telegram import InlineKeyboardMarkup, Message, Update
from telegram.constants import ChatType, ParseMode
from telegram.error import TelegramError
from telegram.ext import ContextTypes

# Custom Modules
from calculator.calculator import CalculatorError
from config import MAX_CRYPTO_PAIRS_PER_MESSAGE
from crypto_calculator.crypto_calculator import (
    CalculatedCryptoExpression,
    ZeroCryptoAmountError,
    calculate_crypto_expression,
)
from crypto_converter.coin_ticker_resolver import BLOCKED_TICKERS, resolve_coin
from crypto_converter.crypto_amount_parser import (
    ResolvedCryptoAmount,
    contains_only_resolved_crypto_amounts,
    resolve_crypto_amounts_from_text,
)
from crypto_converter.crypto_price_converter import (
    CryptoPriceConversion,
    convert_resolved_coin_to_fiat,
)
from crypto_converter.usage_limiter import (
    CoinGeckoDailyRequestLimitExceeded,
    crypto_usage_limiter,
)
from telegram_bot.keyboards.crypto_conversion_keyboard import (
    build_crypto_conversion_keyboard,
)
from telegram_bot.localization.messages import get_message
from telegram_bot.logging_config import (
    format_log_metadata,
    get_update_metadata,
    log_detected_crypto_conversion,
)
from telegram_bot.state.message_reply_tracker import (
    forget_related_reply_message_id,
    get_related_reply_message_id,
    remember_deleted_reply,
    remember_related_reply_message_id,
    was_reply_deleted,
)
from telegram_bot.state.message_signature_tracker import (
    forget_message_signature,
    is_message_signature_unchanged,
    remember_message_signature,
)


LOGGER = logging.getLogger(__name__)
CRYPTO_MESSAGE_FEATURE = "crypto"
CRYPTO_RESPONSE_FEATURE = "crypto_response"


async def handle_delete_crypto_response(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Delete a crypto reply when requested by its source message author."""
    callback_query = update.callback_query

    if callback_query is None:
        return

    await callback_query.answer()
    response_message = callback_query.message

    if not isinstance(response_message, Message):
        LOGGER.warning("Crypto response deletion skipped: message unavailable")
        return

    source_message = response_message.reply_to_message
    source_user = source_message.from_user if source_message is not None else None

    if source_message is None or source_user is None:
        LOGGER.warning(
            "Crypto response deletion skipped: source message unavailable | "
            "chat_id=%s, response_message_id=%s",
            response_message.chat_id,
            response_message.message_id,
        )
        return

    if source_user.id != callback_query.from_user.id:
        LOGGER.warning(
            "Crypto response deletion denied: user is not source author | "
            "chat_id=%s, source_message_id=%s, user_id=%s",
            response_message.chat_id,
            source_message.message_id,
            callback_query.from_user.id,
        )
        return

    try:
        await response_message.delete()
    except TelegramError as error:
        LOGGER.warning(
            "Crypto response deletion failed: %s | "
            "chat_id=%s, response_message_id=%s",
            error,
            response_message.chat_id,
            response_message.message_id,
        )
        return

    forget_related_reply_message_id(
        context.bot_data,
        CRYPTO_MESSAGE_FEATURE,
        response_message.chat_id,
        source_message.message_id,
    )
    forget_message_signature(
        context.bot_data,
        CRYPTO_MESSAGE_FEATURE,
        response_message.chat_id,
        source_message.message_id,
    )
    forget_message_signature(
        context.bot_data,
        CRYPTO_RESPONSE_FEATURE,
        response_message.chat_id,
        source_message.message_id,
    )
    remember_deleted_reply(
        context.bot_data,
        CRYPTO_MESSAGE_FEATURE,
        response_message.chat_id,
        source_message.message_id,
    )
    LOGGER.info(
        "Crypto response deleted | chat_id=%s, source_message_id=%s, "
        "response_message_id=%s, user_id=%s",
        response_message.chat_id,
        source_message.message_id,
        response_message.message_id,
        callback_query.from_user.id,
    )


def _format_decimal(value: Decimal) -> str:
    formatted_value = format(value, ".8f").rstrip("0").rstrip(".")

    return formatted_value or "0"


def _format_fiat_amount(value: Decimal) -> str:
    if value >= 1:
        return format(value, ",.2f").replace(",", " ")

    return _format_decimal(value)


def _format_24h_change(value: Decimal) -> str:
    rounded_value = value.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
    return get_message(
        "crypto_24h_change",
        change=f"{rounded_value:+.2f}",
    )


def _format_coin_label(conversion: CryptoPriceConversion) -> str:
    coin_name = conversion.coin_name.strip() or conversion.ticker
    return get_message(
        "coin_label",
        coin_name=html.escape(coin_name),
        ticker=html.escape(conversion.ticker.lower()),
    )


def _format_crypto_conversion(
    conversion: CryptoPriceConversion,
    show_24h_change: bool,
) -> str:
    amount = _format_decimal(conversion.amount)
    total_usd = _format_fiat_amount(conversion.total_usd)
    total_uah = _format_fiat_amount(conversion.total_uah)
    coin_label = _format_coin_label(conversion)
    amount_prefix = "" if conversion.amount == Decimal("1") else f"{amount} "
    change_text = ""

    if show_24h_change and conversion.usd_24h_change is not None:
        change_text = get_message(
            "crypto_change_text",
            change=_format_24h_change(conversion.usd_24h_change),
        )

    return get_message(
        "crypto_conversion",
        amount_prefix=amount_prefix,
        coin_label=coin_label,
        change_text=change_text,
        total_usd=total_usd,
        total_uah=total_uah,
    )


def format_crypto_response(conversion: CryptoPriceConversion) -> str:
    """Format a cryptocurrency conversion for a Telegram reply."""
    return format_crypto_responses([conversion])


def format_crypto_responses(
    conversions: list[CryptoPriceConversion],
) -> str:
    """Format multiple cryptocurrency conversions in one Telegram reply."""
    formatted_conversions = (
        _format_crypto_conversion(
            conversion,
            show_24h_change=conversion.amount == Decimal("1"),
        )
        for conversion in conversions
    )

    return get_message(
        "crypto_responses",
        conversions="\n\n".join(formatted_conversions),
    )


def format_crypto_calculation_response(
    calculation: CalculatedCryptoExpression,
    conversion: CryptoPriceConversion,
) -> str:
    """Format a calculated crypto amount and its fiat conversion."""
    expression = "".join(calculation.display_expression.split())
    amount = _format_decimal(conversion.amount)
    total_usd = _format_fiat_amount(conversion.total_usd)
    total_uah = _format_fiat_amount(conversion.total_uah)
    coin_label = _format_coin_label(conversion)
    amount_prefix = "" if conversion.amount == Decimal("1") else f"{amount} "

    return get_message(
        "crypto_calculation_response",
        expression=html.escape(expression),
        amount=amount,
        amount_prefix=amount_prefix,
        coin_label=coin_label,
        total_usd=total_usd,
        total_uah=total_uah,
    )


def _get_unique_crypto_amounts(
    message_text: str,
    allow_embedded_usdt: bool,
) -> list[ResolvedCryptoAmount]:
    unique_crypto_amounts: list[ResolvedCryptoAmount] = []
    seen_pairs: set[tuple[Decimal, str]] = set()
    resolved_crypto_amounts = resolve_crypto_amounts_from_text(message_text)
    is_conversion_only = contains_only_resolved_crypto_amounts(
        message_text,
        resolved_crypto_amounts,
    )

    for resolved_crypto_amount in resolved_crypto_amounts:
        pair = (
            resolved_crypto_amount.amount,
            resolved_crypto_amount.coin.coin_id,
        )

        if (
            resolved_crypto_amount.coin.ticker in BLOCKED_TICKERS
            or resolved_crypto_amount.amount == 0
            or (
                resolved_crypto_amount.coin.ticker == "USDT"
                and not allow_embedded_usdt
                and not is_conversion_only
            )
            or pair in seen_pairs
        ):
            continue

        seen_pairs.add(pair)
        unique_crypto_amounts.append(resolved_crypto_amount)

        if len(unique_crypto_amounts) == MAX_CRYPTO_PAIRS_PER_MESSAGE:
            break

    return unique_crypto_amounts


async def _send_or_update_crypto_calculation_error(
    message: Message,
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    metadata_text: str,
) -> None:
    source_message_id = message.message_id
    error_message = get_message("calculation_error")
    response_signature = (error_message, ())
    related_reply_message_id = get_related_reply_message_id(
        context.bot_data,
        CRYPTO_MESSAGE_FEATURE,
        chat_id,
        source_message_id,
    )

    if related_reply_message_id is None:
        reply_message = await message.reply_text(
            text=error_message,
            do_quote=True,
        )
        remember_related_reply_message_id(
            context.bot_data,
            CRYPTO_MESSAGE_FEATURE,
            chat_id,
            source_message_id,
            reply_message.message_id,
        )
        remember_message_signature(
            context.bot_data,
            CRYPTO_RESPONSE_FEATURE,
            chat_id,
            source_message_id,
            response_signature,
        )
        LOGGER.info("Crypto calculation error reply sent | %s", metadata_text)
    elif not is_message_signature_unchanged(
        context.bot_data,
        CRYPTO_RESPONSE_FEATURE,
        chat_id,
        source_message_id,
        response_signature,
    ):
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=related_reply_message_id,
            text=error_message,
            reply_markup=InlineKeyboardMarkup([]),
        )
        remember_message_signature(
            context.bot_data,
            CRYPTO_RESPONSE_FEATURE,
            chat_id,
            source_message_id,
            response_signature,
        )
        LOGGER.info(
            "Crypto calculation error reply updated | %s",
            metadata_text,
        )


async def handle_crypto_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Reply with all supported crypto amounts found in a message."""
    message = update.effective_message

    if message is None:
        return

    message_text = message.text or message.caption

    if message_text is None:
        return

    chat = update.effective_chat

    if chat is None:
        return

    if was_reply_deleted(
        context.bot_data,
        CRYPTO_MESSAGE_FEATURE,
        chat.id,
        message.message_id,
    ):
        return

    try:
        crypto_calculation = calculate_crypto_expression(message_text)
    except ZeroCryptoAmountError:
        forget_message_signature(
            context.bot_data,
            CRYPTO_MESSAGE_FEATURE,
            chat.id,
            message.message_id,
        )
        return
    except CalculatorError as error:
        calculation_signature = (
            "crypto_calculation_error",
            "".join(message_text.split()).lower(),
        )

        if is_message_signature_unchanged(
            context.bot_data,
            CRYPTO_MESSAGE_FEATURE,
            chat.id,
            message.message_id,
            calculation_signature,
        ):
            return

        metadata_text = format_log_metadata(get_update_metadata(update))
        LOGGER.warning(
            "Crypto calculation failed: expression=%r, error=%s | %s",
            message_text,
            error,
            metadata_text,
        )
        await _send_or_update_crypto_calculation_error(
            message,
            context,
            chat.id,
            metadata_text,
        )
        remember_message_signature(
            context.bot_data,
            CRYPTO_MESSAGE_FEATURE,
            chat.id,
            message.message_id,
            calculation_signature,
        )
        return

    resolved_calculation_coin = None

    try:
        if crypto_calculation is not None:
            resolved_calculation_coin = await asyncio.to_thread(
                resolve_coin,
                crypto_calculation.ticker,
            )

        if resolved_calculation_coin is not None:
            resolved_crypto_amounts = [
                ResolvedCryptoAmount(
                    amount=crypto_calculation.amount,
                    coin=resolved_calculation_coin,
                    matched_text=crypto_calculation.matched_text,
                    start=0,
                    end=len(message_text),
                )
            ]
        else:
            crypto_calculation = None
            resolved_crypto_amounts = await asyncio.to_thread(
                _get_unique_crypto_amounts,
                message_text,
                chat.type == ChatType.PRIVATE,
            )
    except CoinGeckoDailyRequestLimitExceeded:
        metadata_text = format_log_metadata(get_update_metadata(update))
        LOGGER.warning(
            "Daily CoinGecko request limit reached during coin resolution | %s",
            metadata_text,
        )
        await message.reply_text(
            text=get_message("global_crypto_limit"),
            do_quote=True,
        )
        LOGGER.info(
            "Global limit reached reply sent | %s",
            metadata_text,
        )
        return

    if not resolved_crypto_amounts:
        forget_message_signature(
            context.bot_data,
            CRYPTO_MESSAGE_FEATURE,
            chat.id,
            message.message_id,
        )
        return

    if crypto_calculation is None:
        crypto_signature = tuple(
            (
                resolved_crypto_amount.amount,
                resolved_crypto_amount.coin.coin_id,
            )
            for resolved_crypto_amount in resolved_crypto_amounts
        )
    else:
        crypto_signature = (
            (
                "crypto_calculation",
                "".join(
                    crypto_calculation.calculation_expression.split()
                ),
                resolved_calculation_coin.coin_id,
            ),
        )

    if is_message_signature_unchanged(
        context.bot_data,
        CRYPTO_MESSAGE_FEATURE,
        chat.id,
        message.message_id,
        crypto_signature,
    ):
        return

    converted_matches: list[
        tuple[ResolvedCryptoAmount, CryptoPriceConversion]
    ] = []
    metadata = get_update_metadata(update)
    metadata_text = format_log_metadata(metadata)
    user_id = metadata["user_id"]
    chat_id = metadata["chat_id"]
    limit_reached_message: str | None = None
    limit_scope: str | None = None

    if not isinstance(user_id, int):
        user_id = None

    if not isinstance(chat_id, int):
        chat_id = None

    for resolved_crypto_amount in resolved_crypto_amounts:
        if not crypto_usage_limiter.try_acquire_conversion_attempt(
            user_id=user_id,
            chat_id=chat_id,
        ):
            limit_reached_message = get_message("personal_crypto_limit")
            limit_scope = "personal"
            LOGGER.warning(
                "Personal crypto conversion limit reached | %s",
                metadata_text,
            )
            break

        try:
            conversion = await asyncio.to_thread(
                convert_resolved_coin_to_fiat,
                resolved_crypto_amount.amount,
                resolved_crypto_amount.coin,
            )
        except CoinGeckoDailyRequestLimitExceeded:
            crypto_usage_limiter.release_conversion_attempt(
                user_id=user_id,
                chat_id=chat_id,
            )
            limit_reached_message = get_message("global_crypto_limit")
            limit_scope = "global"
            LOGGER.warning(
                "Global CoinGecko request limit reached | %s",
                metadata_text,
            )
            break
        except Exception:
            crypto_usage_limiter.release_conversion_attempt(
                user_id=user_id,
                chat_id=chat_id,
            )
            raise

        if not crypto_usage_limiter.try_complete_conversion(
            user_id=user_id,
            chat_id=chat_id,
        ):
            crypto_usage_limiter.release_conversion_attempt(
                user_id=user_id,
                chat_id=chat_id,
            )
            limit_reached_message = get_message("personal_crypto_limit")
            limit_scope = "personal"
            LOGGER.warning(
                "Personal crypto conversion limit reached while completing "
                "conversion | %s",
                metadata_text,
            )
            break

        converted_matches.append((resolved_crypto_amount, conversion))

    if converted_matches:
        conversions = [
            conversion
            for _resolved_crypto_amount, conversion in converted_matches
        ]
        matched_texts = [
            resolved_crypto_amount.matched_text
            for resolved_crypto_amount, _conversion in converted_matches
        ]

        LOGGER.info(
            "Crypto amounts detected: %d | matches=%r | %s",
            len(converted_matches),
            matched_texts,
            metadata_text,
        )
        log_detected_crypto_conversion(
            {
                "chat_type": metadata["chat_type"],
                "matches": [
                    {
                        "matched_text": resolved_crypto_amount.matched_text,
                        "parsed_amount": str(resolved_crypto_amount.amount),
                        "parsed_ticker": resolved_crypto_amount.coin.ticker,
                        "coin_id": conversion.coin_id,
                        "converted_amounts": {
                            "usd": str(conversion.total_usd),
                            "uah": str(conversion.total_uah),
                        },
                    }
                    for resolved_crypto_amount, conversion in converted_matches
                ],
            }
        )

        if crypto_calculation is None:
            response_text = format_crypto_responses(conversions)
        else:
            response_text = format_crypto_calculation_response(
                crypto_calculation,
                conversions[0],
            )
        response_keyboard = build_crypto_conversion_keyboard(conversions)
        response_signature = (
            response_text,
            tuple(
                (button.text, button.url)
                for row in response_keyboard.inline_keyboard
                for button in row
            ),
        )
        related_reply_message_id = get_related_reply_message_id(
            context.bot_data,
            CRYPTO_MESSAGE_FEATURE,
            chat.id,
            message.message_id,
        )

        if related_reply_message_id is None:
            reply_message = await message.reply_text(
                text=response_text,
                parse_mode=ParseMode.HTML,
                do_quote=True,
                reply_markup=response_keyboard,
            )
            remember_related_reply_message_id(
                context.bot_data,
                CRYPTO_MESSAGE_FEATURE,
                chat.id,
                message.message_id,
                reply_message.message_id,
            )
            remember_message_signature(
                context.bot_data,
                CRYPTO_RESPONSE_FEATURE,
                chat.id,
                message.message_id,
                response_signature,
            )
            LOGGER.info(
                "Crypto conversion reply sent: %d conversions | %s",
                len(converted_matches),
                metadata_text,
            )
        elif not is_message_signature_unchanged(
            context.bot_data,
            CRYPTO_RESPONSE_FEATURE,
            chat.id,
            message.message_id,
            response_signature,
        ):
            await context.bot.edit_message_text(
                chat_id=chat.id,
                message_id=related_reply_message_id,
                text=response_text,
                parse_mode=ParseMode.HTML,
                reply_markup=response_keyboard,
            )
            remember_message_signature(
                context.bot_data,
                CRYPTO_RESPONSE_FEATURE,
                chat.id,
                message.message_id,
                response_signature,
            )
            LOGGER.info(
                "Crypto conversion reply updated: %d conversions | %s",
                len(converted_matches),
                metadata_text,
            )
        else:
            LOGGER.info(
                "Crypto conversion reply unchanged: %d conversions | %s",
                len(converted_matches),
                metadata_text,
            )

    if limit_reached_message is not None:
        await message.reply_text(
            text=limit_reached_message,
            do_quote=True,
        )
        LOGGER.info(
            "%s limit reached reply sent | %s",
            (limit_scope or "unknown").capitalize(),
            metadata_text,
        )

    remember_message_signature(
        context.bot_data,
        CRYPTO_MESSAGE_FEATURE,
        chat.id,
        message.message_id,
        crypto_signature,
    )
