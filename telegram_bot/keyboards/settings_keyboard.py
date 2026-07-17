# telegram_bot/keyboards/settings_keyboard.py

# Standard Libraries
from typing import Final

# Third-party Libraries
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Custom Modules
from telegram_bot.localization.messages import get_message
from telegram_bot.settings.group_settings import (
    ALLOWED_MESSAGE_LIMITS,
    GroupSettings,
)


# Settings callbacks
SETTINGS_HOME_CALLBACK_PREFIX: Final[str] = "settings_home"
SETTINGS_TOGGLE_CALLBACK_PREFIX: Final[str] = "settings_toggle"
SETTINGS_LIMIT_MENU_CALLBACK_PREFIX: Final[str] = "settings_limit"
SETTINGS_SET_LIMIT_CALLBACK_PREFIX: Final[str] = "settings_set_limit"
DELETE_SETTINGS_CALLBACK_PREFIX: Final[str] = "delete_settings"


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


def build_settings_home_keyboard(
    chat_id: int,
    settings: GroupSettings,
) -> InlineKeyboardMarkup:
    """Build the settings home menu keyboard."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=(
                        f"{get_message('settings_crypto_button')}: "
                        f"{_format_enabled_label(settings.crypto_converter_enabled)}"
                    ),
                    callback_data=(
                        f"{SETTINGS_TOGGLE_CALLBACK_PREFIX}:"
                        f"{chat_id}:crypto"
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
                        f"{chat_id}:calculator"
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
                        f"{chat_id}:time"
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
                        f"{chat_id}:crypto"
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
                        f"{chat_id}:time"
                    ),
                )
            ],
            _build_delete_row(chat_id),
        ]
    )


def build_settings_limit_keyboard(
    chat_id: int,
    limit_type: str,
    active_limit: int,
) -> InlineKeyboardMarkup:
    """Build a strict 1/3/5 limit selection keyboard."""
    buttons = []

    for limit in ALLOWED_MESSAGE_LIMITS:
        label = str(limit)

        if limit == active_limit:
            label = f"✅ {label}"

        buttons.append(
            InlineKeyboardButton(
                text=label,
                callback_data=(
                    f"{SETTINGS_SET_LIMIT_CALLBACK_PREFIX}:"
                    f"{chat_id}:{limit_type}:{limit}"
                ),
            )
        )

    return InlineKeyboardMarkup(
        [
            buttons,
            [
                InlineKeyboardButton(
                    text=get_message("language_back_button"),
                    callback_data=(
                        f"{SETTINGS_HOME_CALLBACK_PREFIX}:{chat_id}"
                    ),
                )
            ],
            _build_delete_row(chat_id),
        ]
    )
