# telegram_bot/keyboards/settings_keyboard.py

# Standard Libraries
from typing import Final

# Third-party Libraries
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Custom Modules
from config import MAX_CRYPTO_PAIRS_PER_MESSAGE, MAX_TIME_MATCHES_PER_MESSAGE
from telegram_bot.localization.messages import get_message
from telegram_bot.settings.group_settings import (
    ALLOWED_MESSAGE_LIMITS,
    GroupSettings,
)


# Settings callbacks
SETTINGS_HOME_CALLBACK_PREFIX: Final[str] = "settings_home"
SETTINGS_BACK_CALLBACK_PREFIX: Final[str] = "settings_back"
SETTINGS_TOGGLE_CALLBACK_PREFIX: Final[str] = "settings_toggle"
SETTINGS_LIMIT_MENU_CALLBACK_PREFIX: Final[str] = "settings_limit"
SETTINGS_SET_LIMIT_CALLBACK_PREFIX: Final[str] = "settings_set_limit"
SETTINGS_DEFAULT_LIMIT_CALLBACK_PREFIX: Final[str] = "settings_default_limit"
DELETE_SETTINGS_CALLBACK_PREFIX: Final[str] = "delete_settings"
BOT_INFO_SETTINGS_CONTEXT: Final[str] = "bot_info"


def _format_enabled_label(is_enabled: bool) -> str:
    return (
        get_message("settings_enabled_button")
        if is_enabled
        else get_message("settings_disabled_button")
    )


def _build_delete_row(chat_id: int) -> list[InlineKeyboardButton]:
    return [
        InlineKeyboardButton(
            text=get_message("delete_button"),
            callback_data=f"{DELETE_SETTINGS_CALLBACK_PREFIX}:{chat_id}",
        )
    ]


def _format_bot_info_context(requester_user_id: int | None) -> str:
    if requester_user_id is None:
        return ""

    return f":{BOT_INFO_SETTINGS_CONTEXT}:{requester_user_id}"


def _build_bot_info_back_row(
    chat_id: int,
    requester_user_id: int,
) -> list[InlineKeyboardButton]:
    return [
        InlineKeyboardButton(
            text=get_message("language_back_button"),
            callback_data=(
                f"{SETTINGS_BACK_CALLBACK_PREFIX}:"
                f"{chat_id}:{requester_user_id}"
            ),
        )
    ]


def build_settings_home_keyboard(
    chat_id: int,
    settings: GroupSettings,
    requester_user_id: int | None = None,
) -> InlineKeyboardMarkup:
    """Build the settings home menu keyboard."""
    context = _format_bot_info_context(requester_user_id)
    keyboard = [
        [
            InlineKeyboardButton(
                text=(
                    f"{get_message('settings_crypto_button')}: "
                    f"{_format_enabled_label(settings.crypto_converter_enabled)}"
                ),
                callback_data=(
                    f"{SETTINGS_TOGGLE_CALLBACK_PREFIX}:"
                    f"{chat_id}:crypto{context}"
                ),
            )
        ],
        [
            InlineKeyboardButton(
                text=(
                    f"{get_message('settings_calculator_button')}: "
                    f"{_format_enabled_label(settings.calculator_enabled)}"
                ),
                callback_data=(
                    f"{SETTINGS_TOGGLE_CALLBACK_PREFIX}:"
                    f"{chat_id}:calculator{context}"
                ),
            )
        ],
        [
            InlineKeyboardButton(
                text=(
                    f"{get_message('settings_time_button')}: "
                    f"{_format_enabled_label(settings.time_converter_enabled)}"
                ),
                callback_data=(
                    f"{SETTINGS_TOGGLE_CALLBACK_PREFIX}:"
                    f"{chat_id}:time{context}"
                ),
            )
        ],
        [
            InlineKeyboardButton(
                text=(
                    f"{get_message('settings_max_crypto_button')}: "
                    f"{settings.max_crypto_pairs_per_message}"
                ),
                callback_data=(
                    f"{SETTINGS_LIMIT_MENU_CALLBACK_PREFIX}:"
                    f"{chat_id}:crypto{context}"
                ),
            )
        ],
        [
            InlineKeyboardButton(
                text=(
                    f"{get_message('settings_max_time_button')}: "
                    f"{settings.max_time_matches_per_message}"
                ),
                callback_data=(
                    f"{SETTINGS_LIMIT_MENU_CALLBACK_PREFIX}:"
                    f"{chat_id}:time{context}"
                ),
            )
        ],
    ]

    if requester_user_id is not None:
        keyboard.append(_build_bot_info_back_row(chat_id, requester_user_id))

    keyboard.append(_build_delete_row(chat_id))

    return InlineKeyboardMarkup(keyboard)


def build_settings_limit_keyboard(
    chat_id: int,
    limit_type: str,
    active_limit: int,
    requester_user_id: int | None = None,
) -> InlineKeyboardMarkup:
    """Build a strict 1/3/5 limit selection keyboard."""
    buttons = []
    context = _format_bot_info_context(requester_user_id)
    default_limit = (
        MAX_CRYPTO_PAIRS_PER_MESSAGE
        if limit_type == "crypto"
        else MAX_TIME_MATCHES_PER_MESSAGE
    )

    for limit in ALLOWED_MESSAGE_LIMITS:
        label = str(limit)

        if limit == active_limit:
            label = f"✅ {label}"

        buttons.append(
            InlineKeyboardButton(
                text=label,
                callback_data=(
                    f"{SETTINGS_SET_LIMIT_CALLBACK_PREFIX}:"
                    f"{chat_id}:{limit_type}:{limit}{context}"
                ),
            )
        )

    return InlineKeyboardMarkup(
        [
            buttons,
            [
                InlineKeyboardButton(
                    text=f"Default ({default_limit})",
                    callback_data=(
                        f"{SETTINGS_DEFAULT_LIMIT_CALLBACK_PREFIX}:"
                        f"{chat_id}:{limit_type}{context}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text=get_message("language_back_button"),
                    callback_data=(
                        f"{SETTINGS_HOME_CALLBACK_PREFIX}:"
                        f"{chat_id}{context}"
                    ),
                )
            ],
            _build_delete_row(chat_id),
        ]
    )
