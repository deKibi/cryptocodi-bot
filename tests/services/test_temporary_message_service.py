# tests/services/test_temporary_message_service.py

# Standard Libraries
import asyncio
from unittest.mock import AsyncMock

# Third-party Libraries
import pytest
from telegram.error import TelegramError

# Custom Modules
from telegram_bot.services import temporary_message_service
from telegram_bot.services.temporary_message_service import (
    delete_temporary_message,
    send_temporary_message,
)


class FakeApplication:
    def __init__(self) -> None:
        self.create_task_calls: list[dict[str, object]] = []

    def create_task(self, coroutine: object, **kwargs: object) -> None:
        self.create_task_calls.append(
            {
                "coroutine": coroutine,
                "kwargs": kwargs,
            }
        )
        coroutine.close()


class FakeContext:
    def __init__(self) -> None:
        self.application = FakeApplication()


class FakeMessage:
    def __init__(self) -> None:
        self.chat_id = -100
        self.message_id = 10
        self.reply_text = AsyncMock()
        self.delete = AsyncMock()


async def _skip_sleep(delay_seconds: int) -> None:
    return None


def test_send_temporary_message_replies_and_schedules_deletion() -> None:
    source_message = FakeMessage()
    notice_message = FakeMessage()
    source_message.reply_text = AsyncMock(return_value=notice_message)
    context = FakeContext()

    result = asyncio.run(
        send_temporary_message(
            source_message,
            context,
            text="warning",
            delay_seconds=15,
            task_name="delete-warning",
            log_label="Warning notice",
        )
    )

    assert result is notice_message
    source_message.reply_text.assert_awaited_once_with(
        text="warning",
        do_quote=True,
    )
    assert len(context.application.create_task_calls) == 1
    assert context.application.create_task_calls[0]["kwargs"] == {
        "name": "delete-warning",
    }


def test_delete_temporary_message_deletes_after_delay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    message = FakeMessage()
    monkeypatch.setattr(
        temporary_message_service.asyncio,
        "sleep",
        _skip_sleep,
    )

    asyncio.run(delete_temporary_message(message, delay_seconds=15))

    message.delete.assert_awaited_once_with()


def test_delete_temporary_message_ignores_telegram_delete_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    message = FakeMessage()
    message.delete = AsyncMock(side_effect=TelegramError("delete failed"))
    monkeypatch.setattr(
        temporary_message_service.asyncio,
        "sleep",
        _skip_sleep,
    )

    asyncio.run(delete_temporary_message(message, delay_seconds=15))

    message.delete.assert_awaited_once_with()
