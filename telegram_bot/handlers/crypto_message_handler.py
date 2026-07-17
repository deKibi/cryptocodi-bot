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
from crypto_converter.coin_ticker_resolver import (
    BLOCKED_TICKERS,
    FIAT_TICKERS,
    resolve_coin,
)
from crypto_converter.crypto_amount_parser import (
    ResolvedCryptoAmount,
    contains_only_resolved_crypto_amounts,
    resolve_crypto_amounts_from_text,
)
from crypto_converter.fiat_to_crypto_parser import (
    ParsedFiatToCryptoConversion,
    ParsedLowFiatToCryptoAmount,
    parse_fiat_to_crypto_conversion,
)
from crypto_converter.crypto_price_converter import (
    CryptoPriceConversion,
    FiatToCryptoConversion,
    convert_fiat_to_resolved_crypto,
    convert_resolved_coin_to_fiat,
)
from crypto_converter.coingecko_client import CoinGeckoPriceUnavailableError
from crypto_converter.usage_limiter import (
    CoinGeckoDailyRequestLimitExceeded,
    crypto_usage_limiter,
)
from telegram_bot.keyboards.crypto_conversion_keyboard import (
    build_crypto_conversion_keyboard,
)
from telegram_bot.localization.language_preferences import (
    DEFAULT_LANGUAGE,
    resolve_context_language,
)
from telegram_bot.localization.messages import get_message
from telegram_bot.logging_config import (
    format_log_metadata,
    get_update_metadata,
    log_detected_crypto_conversion,
)
from telegram_bot.services.delete_authorization import can_delete_bot_response
from telegram_bot.services.number_formatter import format_large_number
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
REVERSE_CRYPTO_USD_PRECISION_STEP = Decimal("0.1")
MAX_REVERSE_CRYPTO_DECIMAL_PLACES = 8


async def handle_delete_crypto_response(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Delete a crypto reply when requested by its source message author."""
    callback_query = update.callback_query

    if callback_query is None:
        return

    response_message = callback_query.message

    if not isinstance(response_message, Message):
        await callback_query.answer()
        LOGGER.warning("Crypto response deletion skipped: message unavailable")
        return

    source_message = response_message.reply_to_message
    source_user = source_message.from_user if source_message is not None else None

    if source_message is None or source_user is None:
        await callback_query.answer()
        LOGGER.warning(
            "Crypto response deletion skipped: source message unavailable | "
            "chat_id=%s, response_message_id=%s",
            response_message.chat_id,
            response_message.message_id,
        )
        return

    acting_user = callback_query.from_user
    can_delete = await can_delete_bot_response(
        context,
        response_message.chat_id,
        response_message.chat.type,
        source_user.id,
        acting_user.id,
    )

    if not can_delete:
        language = resolve_context_language(
            response_message.chat_id,
            response_message.chat.type,
            acting_user.id,
            acting_user.language_code,
        )
        await callback_query.answer(
            text=get_message("delete_denied", language=language),
        )
        LOGGER.warning(
            "Crypto response deletion denied | "
            "chat_id=%s, source_message_id=%s, user_id=%s",
            response_message.chat_id,
            source_message.message_id,
            acting_user.id,
        )
        return

    await callback_query.answer()

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
        acting_user.id,
    )


async def _cleanup_tracked_crypto_response(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    source_message_id: int,
    metadata_text: str,
) -> None:
    related_reply_message_id = get_related_reply_message_id(
        context.bot_data,
        CRYPTO_MESSAGE_FEATURE,
        chat_id,
        source_message_id,
    )

    if related_reply_message_id is not None:
        try:
            await context.bot.delete_message(
                chat_id=chat_id,
                message_id=related_reply_message_id,
            )
            LOGGER.info(
                "Stale crypto response deleted | %s",
                metadata_text,
            )
        except TelegramError as error:
            LOGGER.warning(
                "Stale crypto response deletion failed: %s | %s",
                error,
                metadata_text,
            )

    forget_related_reply_message_id(
        context.bot_data,
        CRYPTO_MESSAGE_FEATURE,
        chat_id,
        source_message_id,
    )
    forget_message_signature(
        context.bot_data,
        CRYPTO_MESSAGE_FEATURE,
        chat_id,
        source_message_id,
    )
    forget_message_signature(
        context.bot_data,
        CRYPTO_RESPONSE_FEATURE,
        chat_id,
        source_message_id,
    )


def _format_decimal(value: Decimal) -> str:
    formatted_value = format(value, ".8f").rstrip("0").rstrip(".")

    return format_large_number(formatted_value or "0")


def _format_fiat_amount(value: Decimal) -> str:
    if abs(value) >= 1:
        return format_large_number(format(value, ".2f"))

    return _format_decimal(value)


def _format_24h_change(
    value: Decimal,
    language: str = DEFAULT_LANGUAGE,
) -> str:
    rounded_value = value.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
    return get_message(
        "crypto_24h_change",
        language=language,
        change=f"{rounded_value:+.2f}",
    )


def _format_coin_label(
    conversion: CryptoPriceConversion,
    language: str = DEFAULT_LANGUAGE,
) -> str:
    coin_name = conversion.coin_name.strip() or conversion.ticker
    return get_message(
        "coin_label",
        language=language,
        coin_name=html.escape(coin_name),
        ticker=html.escape(conversion.ticker.lower()),
    )


def _format_crypto_conversion(
    conversion: CryptoPriceConversion,
    show_24h_change: bool,
    language: str = DEFAULT_LANGUAGE,
) -> str:
    amount = _format_decimal(conversion.amount)
    total_usd = _format_fiat_amount(conversion.total_usd)
    total_uah = _format_fiat_amount(conversion.total_uah)
    coin_label = _format_coin_label(conversion, language)
    amount_prefix = "" if conversion.amount == Decimal("1") else f"{amount} "
    change_text = ""

    if show_24h_change and conversion.usd_24h_change is not None:
        change_text = get_message(
            "crypto_change_text",
            language=language,
            change=_format_24h_change(
                conversion.usd_24h_change,
                language,
            ),
        )

    return get_message(
        "crypto_conversion",
        language=language,
        amount_prefix=amount_prefix,
        coin_label=coin_label,
        change_text=change_text,
        total_usd=total_usd,
        total_uah=total_uah,
    )


def format_crypto_response(
    conversion: CryptoPriceConversion,
    language: str = DEFAULT_LANGUAGE,
) -> str:
    """Format a cryptocurrency conversion for a Telegram reply."""
    return format_crypto_responses([conversion], language)


def format_crypto_responses(
    conversions: list[CryptoPriceConversion],
    language: str = DEFAULT_LANGUAGE,
) -> str:
    """Format multiple cryptocurrency conversions in one Telegram reply."""
    formatted_conversions = (
        _format_crypto_conversion(
            conversion,
            show_24h_change=conversion.amount == Decimal("1"),
            language=language,
        )
        for conversion in conversions
    )

    return get_message(
        "crypto_responses",
        language=language,
        conversions="\n\n".join(formatted_conversions),
    )


def format_crypto_calculation_response(
    calculation: CalculatedCryptoExpression,
    conversion: CryptoPriceConversion,
    language: str = DEFAULT_LANGUAGE,
) -> str:
    """Format a calculated crypto amount and its fiat conversion."""
    expression = "".join(calculation.display_expression.split())
    amount = _format_decimal(conversion.amount)
    total_usd = _format_fiat_amount(conversion.total_usd)
    total_uah = _format_fiat_amount(conversion.total_uah)
    coin_label = _format_coin_label(conversion, language)
    amount_prefix = "" if conversion.amount == Decimal("1") else f"{amount} "

    return get_message(
        "crypto_calculation_response",
        language=language,
        expression=html.escape(expression),
        amount=amount,
        amount_prefix=amount_prefix,
        coin_label=coin_label,
        total_usd=total_usd,
        total_uah=total_uah,
    )


def _format_reverse_crypto_amount(
    conversion: FiatToCryptoConversion,
) -> str:
    crypto_amount = conversion.crypto_conversion.amount
    unit_price_usd = conversion.crypto_conversion.unit_price_usd
    decimal_places = 0
    crypto_step = Decimal("1")

    while (
        decimal_places < MAX_REVERSE_CRYPTO_DECIMAL_PLACES
        and crypto_step * unit_price_usd > REVERSE_CRYPTO_USD_PRECISION_STEP
    ):
        decimal_places += 1
        crypto_step /= Decimal("10")

    quantizer = Decimal("1").scaleb(-decimal_places)
    rounded_amount = crypto_amount.quantize(
        quantizer,
        rounding=ROUND_HALF_UP,
    )

    if rounded_amount == 0 and crypto_amount > 0:
        decimal_places = max(decimal_places, -crypto_amount.adjusted())
        quantizer = Decimal("1").scaleb(-decimal_places)
        rounded_amount = crypto_amount.quantize(
            quantizer,
            rounding=ROUND_HALF_UP,
        )

        while rounded_amount == 0:
            decimal_places += 1
            quantizer = Decimal("1").scaleb(-decimal_places)
            rounded_amount = crypto_amount.quantize(
                quantizer,
                rounding=ROUND_HALF_UP,
            )

    formatted_amount = (
        f"{rounded_amount:.{decimal_places}f}"
        if decimal_places
        else f"{rounded_amount:.0f}"
    )

    if "." in formatted_amount:
        formatted_amount = formatted_amount.rstrip("0").rstrip(".")

    return format_large_number(formatted_amount or "0")


def format_fiat_to_crypto_response(
    conversion: FiatToCryptoConversion,
    language: str = DEFAULT_LANGUAGE,
) -> str:
    """Format a USD to cryptocurrency conversion for a Telegram reply."""
    usd_amount = _format_decimal(conversion.usd_amount)
    crypto_amount = _format_reverse_crypto_amount(conversion)
    ticker = html.escape(conversion.crypto_conversion.ticker)

    return get_message(
        "fiat_to_crypto_response",
        language=language,
        usd_amount=usd_amount,
        ticker=ticker,
        crypto_amount=crypto_amount,
    )


def _get_unique_crypto_amounts(
    message_text: str,
    allow_embedded_usdt: bool,
) -> list[ResolvedCryptoAmount]:
    unique_crypto_amounts: list[ResolvedCryptoAmount] = []
    seen_pairs: set[tuple[Decimal, str, str]] = set()
    exact_crypto_amounts = resolve_crypto_amounts_from_text(message_text)
    is_conversion_only = contains_only_resolved_crypto_amounts(
        message_text,
        exact_crypto_amounts,
    )

    if is_conversion_only:
        resolved_crypto_amounts = exact_crypto_amounts
    else:
        resolved_crypto_amounts = resolve_crypto_amounts_from_text(
            message_text,
            top_ranked_only=True,
        )

    for resolved_crypto_amount in resolved_crypto_amounts:
        pair = (
            resolved_crypto_amount.amount,
            resolved_crypto_amount.coin.coin_id,
            resolved_crypto_amount.coin.ticker,
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
    language: str = DEFAULT_LANGUAGE,
) -> None:
    source_message_id = message.message_id
    error_message = get_message("calculation_error", language=language)
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


async def _send_or_update_fiat_to_crypto_minimum_error(
    message: Message,
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    metadata_text: str,
    language: str = DEFAULT_LANGUAGE,
) -> None:
    source_message_id = message.message_id
    error_message = get_message(
        "fiat_to_crypto_minimum_amount",
        language=language,
    )
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
        LOGGER.info("Fiat to crypto minimum reply sent | %s", metadata_text)
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
        LOGGER.info("Fiat to crypto minimum reply updated | %s", metadata_text)


async def _send_or_update_fiat_to_crypto_target_error(
    message: Message,
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    metadata_text: str,
    language: str = DEFAULT_LANGUAGE,
) -> None:
    source_message_id = message.message_id
    error_message = get_message(
        "fiat_to_crypto_target_must_be_crypto",
        language=language,
    )
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
        LOGGER.info("Fiat to crypto target reply sent | %s", metadata_text)
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
        LOGGER.info("Fiat to crypto target reply updated | %s", metadata_text)


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
        await _cleanup_tracked_crypto_response(
            context,
            chat.id,
            message.message_id,
            format_log_metadata(get_update_metadata(update)),
        )
        return
    except CalculatorError as error:
        user = update.effective_user
        language = resolve_context_language(
            chat.id,
            chat.type,
            user.id if user is not None else None,
            user.language_code if user is not None else None,
        )
        calculation_signature = (
            "crypto_calculation_error",
            "".join(message_text.split()).lower(),
            language,
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
            language,
        )
        remember_message_signature(
            context.bot_data,
            CRYPTO_MESSAGE_FEATURE,
            chat.id,
            message.message_id,
            calculation_signature,
        )
        return

    fiat_to_crypto_request: ParsedFiatToCryptoConversion | None = None
    resolved_calculation_coin = None
    resolved_fiat_to_crypto_coin = None

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
            parsed_fiat_to_crypto_request = parse_fiat_to_crypto_conversion(
                message_text,
            )

            if isinstance(
                parsed_fiat_to_crypto_request,
                ParsedLowFiatToCryptoAmount,
            ):
                user = update.effective_user
                language = resolve_context_language(
                    chat.id,
                    chat.type,
                    user.id if user is not None else None,
                    user.language_code if user is not None else None,
                )
                minimum_signature = (
                    language,
                    (
                        "fiat_to_crypto_minimum",
                        parsed_fiat_to_crypto_request.usd_amount,
                        parsed_fiat_to_crypto_request.ticker,
                    ),
                )

                if is_message_signature_unchanged(
                    context.bot_data,
                    CRYPTO_MESSAGE_FEATURE,
                    chat.id,
                    message.message_id,
                    minimum_signature,
                ):
                    return

                metadata_text = format_log_metadata(get_update_metadata(update))
                LOGGER.info(
                    "Fiat to crypto amount below minimum: amount=%s, "
                    "ticker=%s | %s",
                    parsed_fiat_to_crypto_request.usd_amount,
                    parsed_fiat_to_crypto_request.ticker,
                    metadata_text,
                )
                await _send_or_update_fiat_to_crypto_minimum_error(
                    message,
                    context,
                    chat.id,
                    metadata_text,
                    language,
                )
                remember_message_signature(
                    context.bot_data,
                    CRYPTO_MESSAGE_FEATURE,
                    chat.id,
                    message.message_id,
                    minimum_signature,
                )
                return

            if parsed_fiat_to_crypto_request is not None:
                fiat_to_crypto_request = parsed_fiat_to_crypto_request
                resolved_fiat_to_crypto_coin = await asyncio.to_thread(
                    resolve_coin,
                    fiat_to_crypto_request.ticker,
                )

                if (
                    resolved_fiat_to_crypto_coin is not None
                    and resolved_fiat_to_crypto_coin.ticker in FIAT_TICKERS
                ):
                    user = update.effective_user
                    language = resolve_context_language(
                        chat.id,
                        chat.type,
                        user.id if user is not None else None,
                        user.language_code if user is not None else None,
                    )
                    target_signature = (
                        language,
                        (
                            "fiat_to_crypto_target_must_be_crypto",
                            fiat_to_crypto_request.usd_amount,
                            resolved_fiat_to_crypto_coin.ticker,
                        ),
                    )

                    if is_message_signature_unchanged(
                        context.bot_data,
                        CRYPTO_MESSAGE_FEATURE,
                        chat.id,
                        message.message_id,
                        target_signature,
                    ):
                        return

                    metadata_text = format_log_metadata(
                        get_update_metadata(update)
                    )
                    LOGGER.info(
                        "Fiat to crypto target is not crypto: amount=%s, "
                        "ticker=%s | %s",
                        fiat_to_crypto_request.usd_amount,
                        resolved_fiat_to_crypto_coin.ticker,
                        metadata_text,
                    )
                    await _send_or_update_fiat_to_crypto_target_error(
                        message,
                        context,
                        chat.id,
                        metadata_text,
                        language,
                    )
                    remember_message_signature(
                        context.bot_data,
                        CRYPTO_MESSAGE_FEATURE,
                        chat.id,
                        message.message_id,
                        target_signature,
                    )
                    return

                resolved_crypto_amounts = []
            else:
                resolved_crypto_amounts = await asyncio.to_thread(
                    _get_unique_crypto_amounts,
                    message_text,
                    chat.type == ChatType.PRIVATE,
                )
    except CoinGeckoDailyRequestLimitExceeded:
        user = update.effective_user
        language = resolve_context_language(
            chat.id,
            chat.type,
            user.id if user is not None else None,
            user.language_code if user is not None else None,
        )
        metadata_text = format_log_metadata(get_update_metadata(update))
        LOGGER.warning(
            "Daily CoinGecko request limit reached during coin resolution | %s",
            metadata_text,
        )
        await _cleanup_tracked_crypto_response(
            context,
            chat.id,
            message.message_id,
            metadata_text,
        )
        await message.reply_text(
            text=get_message("global_crypto_limit", language=language),
            do_quote=True,
        )
        LOGGER.info(
            "Global limit reached reply sent | %s",
            metadata_text,
        )
        return

    if not resolved_crypto_amounts and resolved_fiat_to_crypto_coin is None:
        await _cleanup_tracked_crypto_response(
            context,
            chat.id,
            message.message_id,
            format_log_metadata(get_update_metadata(update)),
        )
        return

    user = update.effective_user
    language = resolve_context_language(
        chat.id,
        chat.type,
        user.id if user is not None else None,
        user.language_code if user is not None else None,
    )

    if (
        fiat_to_crypto_request is not None
        and resolved_fiat_to_crypto_coin is not None
    ):
        crypto_signature = (
            language,
            (
                "fiat_to_crypto",
                fiat_to_crypto_request.usd_amount,
                resolved_fiat_to_crypto_coin.coin_id,
                resolved_fiat_to_crypto_coin.ticker,
            ),
        )
    elif crypto_calculation is None:
        amount_signature = tuple(
            (
                resolved_crypto_amount.amount,
                resolved_crypto_amount.coin.coin_id,
                resolved_crypto_amount.coin.ticker,
            )
            for resolved_crypto_amount in resolved_crypto_amounts
        )
        crypto_signature = (language, amount_signature)
    else:
        crypto_signature = (
            language,
            (
                "crypto_calculation",
                "".join(
                    crypto_calculation.calculation_expression.split()
                ),
                resolved_calculation_coin.coin_id,
                resolved_calculation_coin.ticker,
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
    fiat_to_crypto_conversion: FiatToCryptoConversion | None = None
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

    if (
        fiat_to_crypto_request is not None
        and resolved_fiat_to_crypto_coin is not None
    ):
        conversion_attempt_reserved = (
            crypto_usage_limiter.try_acquire_conversion_attempt(
                user_id=user_id,
                chat_id=chat_id,
            )
        )

        if not conversion_attempt_reserved:
            limit_reached_message = get_message(
                "personal_crypto_limit",
                language=language,
            )
            limit_scope = "personal"
            LOGGER.warning(
                "Personal crypto conversion limit reached | %s",
                metadata_text,
            )
        else:
            try:
                fiat_to_crypto_conversion = await asyncio.to_thread(
                    convert_fiat_to_resolved_crypto,
                    fiat_to_crypto_request.usd_amount,
                    resolved_fiat_to_crypto_coin,
                )
            except CoinGeckoDailyRequestLimitExceeded:
                crypto_usage_limiter.release_conversion_attempt(
                    user_id=user_id,
                    chat_id=chat_id,
                )
                limit_reached_message = get_message(
                    "global_crypto_limit",
                    language=language,
                )
                limit_scope = "global"
                LOGGER.warning(
                    "Global CoinGecko request limit reached | %s",
                    metadata_text,
                )
            except CoinGeckoPriceUnavailableError:
                crypto_usage_limiter.release_conversion_attempt(
                    user_id=user_id,
                    chat_id=chat_id,
                )
                LOGGER.info(
                    "CoinGecko price unavailable for %s (%s) | %s",
                    resolved_fiat_to_crypto_coin.ticker,
                    resolved_fiat_to_crypto_coin.coin_id,
                    metadata_text,
                )
            except Exception:
                crypto_usage_limiter.release_conversion_attempt(
                    user_id=user_id,
                    chat_id=chat_id,
                )
                raise
            else:
                if fiat_to_crypto_conversion is None:
                    crypto_usage_limiter.release_conversion_attempt(
                        user_id=user_id,
                        chat_id=chat_id,
                    )
                elif not crypto_usage_limiter.try_complete_conversion(
                    user_id=user_id,
                    chat_id=chat_id,
                ):
                    crypto_usage_limiter.release_conversion_attempt(
                        user_id=user_id,
                        chat_id=chat_id,
                    )
                    fiat_to_crypto_conversion = None
                    limit_reached_message = get_message(
                        "personal_crypto_limit",
                        language=language,
                    )
                    limit_scope = "personal"
                    LOGGER.warning(
                        "Personal crypto conversion limit reached while "
                        "completing conversion | %s",
                        metadata_text,
                    )
    else:
        for resolved_crypto_amount in resolved_crypto_amounts:
            if not crypto_usage_limiter.try_acquire_conversion_attempt(
                user_id=user_id,
                chat_id=chat_id,
            ):
                limit_reached_message = get_message(
                    "personal_crypto_limit",
                    language=language,
                )
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
                limit_reached_message = get_message(
                    "global_crypto_limit",
                    language=language,
                )
                limit_scope = "global"
                LOGGER.warning(
                    "Global CoinGecko request limit reached | %s",
                    metadata_text,
                )
                break
            except CoinGeckoPriceUnavailableError:
                crypto_usage_limiter.release_conversion_attempt(
                    user_id=user_id,
                    chat_id=chat_id,
                )
                LOGGER.info(
                    "CoinGecko price unavailable for %s (%s) | %s",
                    resolved_crypto_amount.coin.ticker,
                    resolved_crypto_amount.coin.coin_id,
                    metadata_text,
                )
                continue
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
                limit_reached_message = get_message(
                    "personal_crypto_limit",
                    language=language,
                )
                limit_scope = "personal"
                LOGGER.warning(
                    "Personal crypto conversion limit reached while "
                    "completing conversion | %s",
                    metadata_text,
                )
                break

            converted_matches.append((resolved_crypto_amount, conversion))

    if converted_matches or fiat_to_crypto_conversion is not None:
        conversions = [
            conversion
            for _resolved_crypto_amount, conversion in converted_matches
        ]
        matched_texts = []

        if fiat_to_crypto_conversion is not None:
            conversions = [fiat_to_crypto_conversion.crypto_conversion]
            matched_texts = [fiat_to_crypto_request.matched_text]
        else:
            matched_texts = [
                resolved_crypto_amount.matched_text
                for resolved_crypto_amount, _conversion in converted_matches
            ]

        LOGGER.info(
            "Crypto amounts detected: %d | matches=%r | %s",
            len(conversions),
            matched_texts,
            metadata_text,
        )

        if fiat_to_crypto_conversion is not None:
            log_detected_crypto_conversion(
                {
                    "chat_type": metadata["chat_type"],
                    "matches": [
                        {
                            "matched_text": fiat_to_crypto_request.matched_text,
                            "parsed_amount": str(
                                fiat_to_crypto_request.usd_amount
                            ),
                            "parsed_ticker": "USD",
                            "coin_id": (
                                fiat_to_crypto_conversion
                                .crypto_conversion
                                .coin_id
                            ),
                            "converted_amounts": {
                                "crypto": str(
                                    fiat_to_crypto_conversion
                                    .crypto_conversion
                                    .amount
                                ),
                                "ticker": (
                                    fiat_to_crypto_conversion
                                    .crypto_conversion
                                    .ticker
                                ),
                            },
                        }
                    ],
                }
            )
            response_text = format_fiat_to_crypto_response(
                fiat_to_crypto_conversion,
                language,
            )
        elif crypto_calculation is None:
            log_detected_crypto_conversion(
                {
                    "chat_type": metadata["chat_type"],
                    "matches": [
                        {
                            "matched_text": resolved_crypto_amount.matched_text,
                            "parsed_amount": str(
                                resolved_crypto_amount.amount
                            ),
                            "parsed_ticker": resolved_crypto_amount.coin.ticker,
                            "coin_id": conversion.coin_id,
                            "converted_amounts": {
                                "usd": str(conversion.total_usd),
                                "uah": str(conversion.total_uah),
                            },
                        }
                        for resolved_crypto_amount, conversion
                        in converted_matches
                    ],
                }
            )
            response_text = format_crypto_responses(conversions, language)
        else:
            log_detected_crypto_conversion(
                {
                    "chat_type": metadata["chat_type"],
                    "matches": [
                        {
                            "matched_text": resolved_crypto_amount.matched_text,
                            "parsed_amount": str(
                                resolved_crypto_amount.amount
                            ),
                            "parsed_ticker": resolved_crypto_amount.coin.ticker,
                            "coin_id": conversion.coin_id,
                            "converted_amounts": {
                                "usd": str(conversion.total_usd),
                                "uah": str(conversion.total_uah),
                            },
                        }
                        for resolved_crypto_amount, conversion
                        in converted_matches
                    ],
                }
            )
            response_text = format_crypto_calculation_response(
                crypto_calculation,
                conversions[0],
                language,
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
    elif limit_reached_message is not None:
        await _cleanup_tracked_crypto_response(
            context,
            chat.id,
            message.message_id,
            metadata_text,
        )
    else:
        await _cleanup_tracked_crypto_response(
            context,
            chat.id,
            message.message_id,
            metadata_text,
        )
        return

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
