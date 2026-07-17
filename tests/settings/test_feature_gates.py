# tests/settings/test_feature_gates.py

# Standard Libraries
import asyncio
from dataclasses import dataclass
from unittest.mock import AsyncMock, Mock

# Third-party Libraries
import pytest

# Custom Modules
from telegram_bot.handlers import (
    calculator_message_handler,
    crypto_message_handler,
    time_message_handler,
)
from telegram_bot.settings.group_settings import GroupSettings


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


class FakeMessage:
    def __init__(self, text: str) -> None:
        self.message_id = 100
        self.text = text
        self.caption = None
        self.reply_text = AsyncMock()


class FakeUpdate:
    def __init__(self, text: str) -> None:
        self.effective_message = FakeMessage(text)
        self.effective_chat = FakeChat(id=-100, type="supergroup")
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


def test_disabled_crypto_converter_skips_crypto_handler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    update = FakeUpdate("1 BTC")
    context = FakeContext()
    calculate_crypto_expression = Mock(
        side_effect=AssertionError("crypto parser should not run")
    )
    monkeypatch.setattr(
        crypto_message_handler,
        "get_effective_chat_settings",
        lambda *args: GroupSettings(crypto_converter_enabled=False),
    )
    monkeypatch.setattr(
        crypto_message_handler,
        "calculate_crypto_expression",
        calculate_crypto_expression,
    )

    asyncio.run(crypto_message_handler.handle_crypto_message(update, context))

    calculate_crypto_expression.assert_not_called()
    update.effective_message.reply_text.assert_not_called()


def test_disabled_time_converter_skips_time_handler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    update = FakeUpdate("10:00 UTC")
    context = FakeContext()
    parse_times_from_text = Mock(
        side_effect=AssertionError("time parser should not run")
    )
    monkeypatch.setattr(
        time_message_handler,
        "get_effective_chat_settings",
        lambda *args: GroupSettings(time_converter_enabled=False),
    )
    monkeypatch.setattr(
        time_message_handler,
        "parse_times_from_text",
        parse_times_from_text,
    )

    asyncio.run(time_message_handler.handle_time_message(update, context))

    parse_times_from_text.assert_not_called()
    update.effective_message.reply_text.assert_not_called()


def test_disabled_calculator_skips_calculator_handler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    update = FakeUpdate("2+2")
    context = FakeContext()
    parse_expression = Mock(
        side_effect=AssertionError("calculator parser should not run")
    )
    monkeypatch.setattr(
        calculator_message_handler,
        "get_effective_chat_settings",
        lambda *args: GroupSettings(calculator_enabled=False),
    )
    monkeypatch.setattr(
        calculator_message_handler,
        "parse_expression",
        parse_expression,
    )

    asyncio.run(
        calculator_message_handler.handle_calculator_message(update, context)
    )

    parse_expression.assert_not_called()
    update.effective_message.reply_text.assert_not_called()
