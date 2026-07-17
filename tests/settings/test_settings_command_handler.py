# tests/settings/test_settings_command_handler.py

# Standard Libraries
import asyncio
from dataclasses import dataclass
from unittest.mock import AsyncMock

# Third-party Libraries
import pytest
from telegram.constants import ChatMemberStatus

# Custom Modules
from telegram_bot.handlers import settings_command_handler
from telegram_bot.localization.messages import get_message
from telegram_bot.settings.group_settings import GroupSettings


@dataclass
class FakeChat:
    id: int
    type: str


@dataclass
class FakeUser:
    id: int
    language_code: str
    username: str = "tester"
    full_name: str = "Test User"


@dataclass
class FakeChatMember:
    user: FakeUser
    status: str


class FakeMessage:
    def __init__(self, text: str = "/settings") -> None:
        self.text = text
        self.caption = None
        self.message_id = 100
        self.reply_text = AsyncMock()


class FakeUpdate:
    def __init__(self, chat_type: str, user_id: int = 456) -> None:
        self.effective_message = FakeMessage()
        self.effective_chat = FakeChat(id=-100, type=chat_type)
        self.effective_user = FakeUser(id=user_id, language_code="en")
        self.callback_query = None


class FakeContext:
    def __init__(self) -> None:
        self.bot = AsyncMock()


def test_settings_command_in_private_chat_returns_unavailable_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    update = FakeUpdate("private")
    update.effective_chat.id = 456
    context = FakeContext()
    monkeypatch.setattr(
        settings_command_handler,
        "resolve_context_language",
        lambda *args: "en",
    )

    asyncio.run(
        settings_command_handler.handle_settings_command(update, context)
    )

    update.effective_message.reply_text.assert_awaited_once_with(
        text=get_message("settings_private_only_groups", language="en"),
        do_quote=True,
    )


def test_settings_command_denies_group_non_admin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    update = FakeUpdate("supergroup")
    context = FakeContext()
    context.bot.get_chat_administrators = AsyncMock(return_value=[])
    monkeypatch.setattr(
        settings_command_handler,
        "resolve_context_language",
        lambda *args: "en",
    )

    asyncio.run(
        settings_command_handler.handle_settings_command(update, context)
    )

    update.effective_message.reply_text.assert_awaited_once_with(
        text=get_message("settings_admin_only", language="en"),
        do_quote=True,
    )


def test_settings_command_allows_group_admin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    update = FakeUpdate("supergroup")
    context = FakeContext()
    context.bot.get_chat_administrators = AsyncMock(
        return_value=[
            FakeChatMember(
                user=FakeUser(id=456, language_code="en"),
                status=ChatMemberStatus.ADMINISTRATOR,
            )
        ]
    )
    monkeypatch.setattr(
        settings_command_handler,
        "resolve_context_language",
        lambda *args: "en",
    )
    monkeypatch.setattr(
        settings_command_handler,
        "get_group_settings",
        lambda chat_id: GroupSettings(),
    )

    asyncio.run(
        settings_command_handler.handle_settings_command(update, context)
    )

    reply_call = update.effective_message.reply_text.await_args

    assert reply_call is not None
    assert "Bot settings" in reply_call.kwargs["text"]
    assert reply_call.kwargs["do_quote"] is True
    assert reply_call.kwargs["reply_markup"] is not None
