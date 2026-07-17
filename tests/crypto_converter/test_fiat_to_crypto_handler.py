# tests/crypto_converter/test_fiat_to_crypto_handler.py

# Standard Libraries
import asyncio
from dataclasses import dataclass
from unittest.mock import AsyncMock, Mock

# Third-party Libraries
import pytest

# Custom Modules
from telegram_bot.handlers import crypto_message_handler
from telegram_bot.localization.messages import get_message


@dataclass
class FakeChat:
    id: int
    type: str


@dataclass
class FakeUser:
    id: int
    language_code: str
    username: str
    full_name: str


@dataclass
class FakeReplyMessage:
    message_id: int


class FakeMessage:
    def __init__(self, text: str) -> None:
        self.message_id = 100
        self.text = text
        self.caption = None
        self.reply_text = AsyncMock(
            return_value=FakeReplyMessage(message_id=200)
        )


class FakeUpdate:
    def __init__(self, text: str) -> None:
        self.effective_message = FakeMessage(text)
        self.effective_chat = FakeChat(id=123, type="private")
        self.effective_user = FakeUser(
            id=456,
            language_code="en",
            username="tester",
            full_name="Test User",
        )


class FakeContext:
    def __init__(self) -> None:
        self.bot_data: dict[str, object] = {}
        self.bot = AsyncMock()


def test_low_fiat_to_crypto_amount_replies_without_coin_resolution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    update = FakeUpdate("$0.09 BNB")
    context = FakeContext()
    resolve_coin = Mock(
        side_effect=AssertionError("resolve_coin should not be called")
    )
    acquire_conversion_attempt = Mock(
        side_effect=AssertionError(
            "conversion limit should not be acquired"
        )
    )

    monkeypatch.setattr(
        crypto_message_handler,
        "resolve_context_language",
        lambda *args: "en",
    )
    monkeypatch.setattr(
        crypto_message_handler,
        "resolve_coin",
        resolve_coin,
    )
    monkeypatch.setattr(
        crypto_message_handler.crypto_usage_limiter,
        "try_acquire_conversion_attempt",
        acquire_conversion_attempt,
    )

    asyncio.run(
        crypto_message_handler.handle_crypto_message(update, context)
    )

    update.effective_message.reply_text.assert_awaited_once_with(
        text=get_message("fiat_to_crypto_minimum_amount", language="en"),
        do_quote=True,
    )
    resolve_coin.assert_not_called()
    acquire_conversion_attempt.assert_not_called()
