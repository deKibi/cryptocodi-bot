# telegram_bot/keyboards/id_keyboard.py

# Standard Libraries
from typing import Final

# Third-party Libraries
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    KeyboardButtonRequestChat,
    KeyboardButtonRequestUsers,
    ReplyKeyboardMarkup,
)


# ID lookup keyboards
FIND_DIFFERENT_ID_CALLBACK: Final[str] = "find_different_id"
CHAT_REQUEST_ID: Final[int] = 1
CHANNEL_REQUEST_ID: Final[int] = 2
USER_REQUEST_ID: Final[int] = 3
BOT_REQUEST_ID: Final[int] = 4


def build_find_different_id_keyboard() -> InlineKeyboardMarkup:
    """Build the inline action for opening the entity selector."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="Find a different ID",
                    callback_data=FIND_DIFFERENT_ID_CALLBACK,
                )
            ]
        ]
    )


def build_entity_selection_keyboard() -> ReplyKeyboardMarkup:
    """Build buttons that request one Telegram entity of each type."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="Chat",
                    request_chat=KeyboardButtonRequestChat(
                        request_id=CHAT_REQUEST_ID,
                        chat_is_channel=False,
                    ),
                ),
                KeyboardButton(
                    text="Channel",
                    request_chat=KeyboardButtonRequestChat(
                        request_id=CHANNEL_REQUEST_ID,
                        chat_is_channel=True,
                    ),
                ),
                KeyboardButton(
                    text="User",
                    request_users=KeyboardButtonRequestUsers(
                        request_id=USER_REQUEST_ID,
                        user_is_bot=False,
                        max_quantity=1,
                    ),
                ),
                KeyboardButton(
                    text="Bot",
                    request_users=KeyboardButtonRequestUsers(
                        request_id=BOT_REQUEST_ID,
                        user_is_bot=True,
                        max_quantity=1,
                    ),
                ),
            ],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Select an entity",
    )
