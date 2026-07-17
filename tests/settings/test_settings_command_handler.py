# tests/settings/test_settings_command_handler.py

# Standard Libraries
import asyncio
from dataclasses import dataclass
from unittest.mock import AsyncMock, Mock

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
        self.application = AsyncMock()


class FakeCallbackQuery:
    def __init__(self, data: str) -> None:
        self.data = data
        self.message = None
        self.answer = AsyncMock()


class FakeCallbackUpdate:
    def __init__(self, callback_data: str) -> None:
        self.callback_query = FakeCallbackQuery(callback_data)
        self.effective_message = None
        self.effective_chat = FakeChat(id=-100, type="supergroup")
        self.effective_user = FakeUser(id=456, language_code="en")


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
    send_temporary_message = AsyncMock()
    monkeypatch.setattr(
        settings_command_handler,
        "send_temporary_message",
        send_temporary_message,
    )

    asyncio.run(
        settings_command_handler.handle_settings_command(update, context)
    )

    update.effective_message.reply_text.assert_awaited_once_with(
        text=get_message("settings_private_only_groups", language="en"),
        do_quote=True,
    )
    send_temporary_message.assert_not_awaited()


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
    send_temporary_message = AsyncMock()
    monkeypatch.setattr(
        settings_command_handler,
        "send_temporary_message",
        send_temporary_message,
    )

    asyncio.run(
        settings_command_handler.handle_settings_command(update, context)
    )

    update.effective_message.reply_text.assert_not_called()
    send_temporary_message.assert_awaited_once_with(
        update.effective_message,
        context,
        text=get_message("settings_admin_only", language="en"),
        update=update,
        log_label="Temporary settings notice",
        task_name="delete-non-admin-settings-notice",
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


def test_settings_default_limit_callback_resets_crypto_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    update = FakeCallbackUpdate("settings_default_limit:-100:crypto")
    context = FakeContext()
    update_group_setting = Mock()
    monkeypatch.setattr(
        settings_command_handler,
        "_can_manage_settings",
        AsyncMock(return_value=True),
    )
    monkeypatch.setattr(
        settings_command_handler,
        "resolve_context_language",
        lambda *args: "en",
    )
    monkeypatch.setattr(
        settings_command_handler,
        "update_group_setting",
        update_group_setting,
    )

    asyncio.run(
        settings_command_handler.handle_settings_default_limit_callback(
            update,
            context,
        )
    )

    update_group_setting.assert_called_once_with(
        -100,
        "max_crypto_pairs_per_message",
        None,
    )
    update.callback_query.answer.assert_awaited_once_with()


def test_settings_toggle_callback_reports_save_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    update = FakeCallbackUpdate("settings_toggle:-100:calculator")
    context = FakeContext()
    monkeypatch.setattr(
        settings_command_handler,
        "_can_manage_settings",
        AsyncMock(return_value=True),
    )
    monkeypatch.setattr(
        settings_command_handler,
        "resolve_context_language",
        lambda *args: "en",
    )
    monkeypatch.setattr(
        settings_command_handler,
        "get_group_settings",
        lambda chat_id: GroupSettings(calculator_enabled=True),
    )
    monkeypatch.setattr(
        settings_command_handler,
        "update_group_setting",
        Mock(return_value=None),
    )

    asyncio.run(
        settings_command_handler.handle_settings_toggle_callback(
            update,
            context,
        )
    )

    update.callback_query.answer.assert_awaited_once_with(
        text=get_message("settings_save_failed", language="en"),
    )


def test_settings_set_limit_callback_reports_save_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    update = FakeCallbackUpdate("settings_set_limit:-100:crypto:3")
    context = FakeContext()
    monkeypatch.setattr(
        settings_command_handler,
        "_can_manage_settings",
        AsyncMock(return_value=True),
    )
    monkeypatch.setattr(
        settings_command_handler,
        "resolve_context_language",
        lambda *args: "en",
    )
    monkeypatch.setattr(
        settings_command_handler,
        "update_group_setting",
        Mock(return_value=None),
    )

    asyncio.run(
        settings_command_handler.handle_settings_set_limit_callback(
            update,
            context,
        )
    )

    update.callback_query.answer.assert_awaited_once_with(
        text=get_message("settings_save_failed", language="en"),
    )


def test_settings_default_limit_callback_reports_save_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    update = FakeCallbackUpdate("settings_default_limit:-100:time")
    context = FakeContext()
    monkeypatch.setattr(
        settings_command_handler,
        "_can_manage_settings",
        AsyncMock(return_value=True),
    )
    monkeypatch.setattr(
        settings_command_handler,
        "resolve_context_language",
        lambda *args: "en",
    )
    monkeypatch.setattr(
        settings_command_handler,
        "update_group_setting",
        Mock(return_value=None),
    )

    asyncio.run(
        settings_command_handler.handle_settings_default_limit_callback(
            update,
            context,
        )
    )

    update.callback_query.answer.assert_awaited_once_with(
        text=get_message("settings_save_failed", language="en"),
    )
