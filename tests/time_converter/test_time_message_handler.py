# tests/time_converter/test_time_message_handler.py

# Standard Libraries
import asyncio
from dataclasses import dataclass
from unittest.mock import AsyncMock

# Third-party Libraries
import pytest

# Custom Modules
from telegram_bot.handlers import time_message_handler


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


@pytest.mark.parametrize(
    ("initial_text", "edited_text", "expected_label"),
    [
        ("10:00 UTC+3", "10:00 GMT+3", "10:00 GMT+3"),
        ("10:00 GMT+3", "10:00 UTC+3", "10:00 UTC+3"),
    ],
)
def test_time_message_edit_updates_when_display_timezone_changes(
    monkeypatch: pytest.MonkeyPatch,
    initial_text: str,
    edited_text: str,
    expected_label: str,
) -> None:
    context = FakeContext()
    initial_update = FakeUpdate(initial_text)
    edited_update = FakeUpdate(edited_text)

    monkeypatch.setattr(
        time_message_handler,
        "resolve_context_language",
        lambda *args: "en",
    )
    monkeypatch.setattr(
        time_message_handler,
        "log_detected_time_conversion",
        lambda *args: None,
    )

    asyncio.run(
        time_message_handler.handle_time_message(initial_update, context)
    )
    asyncio.run(
        time_message_handler.handle_time_message(edited_update, context)
    )

    context.bot.edit_message_text.assert_awaited_once()
    edit_call = context.bot.edit_message_text.await_args

    assert edit_call is not None
    assert expected_label in edit_call.kwargs["text"]
