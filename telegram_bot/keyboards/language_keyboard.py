# telegram_bot/keyboards/language_keyboard.py

# Standard Libraries
from typing import Final

# Third-party Libraries
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Custom Modules
from telegram_bot.localization.messages import get_message


# Language selection callbacks
CHANGE_LANGUAGE_CALLBACK_PREFIX: Final[str] = "change_language"
BACK_TO_LANGUAGE_SETTINGS_CALLBACK_PREFIX: Final[str] = (
    "back_to_language_settings"
)
SET_LANGUAGE_CALLBACK_PREFIX: Final[str] = "set_language"
BOT_INFO_LANGUAGE_RESPONSE: Final[str] = "bot_info"
COMMAND_LANGUAGE_RESPONSE: Final[str] = "command"
LANGUAGE_BUTTON_KEYS: Final[dict[str, str]] = {
    "en": "language_english_button",
    "uk": "language_ukrainian_button",
    "ru": "language_russian_button",
}


def build_change_language_keyboard(
    scope_type: str,
    scope_id: int,
) -> InlineKeyboardMarkup:
    """Build the action that opens selection for one language scope."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=get_message("change_language_button"),
                    callback_data=(
                        f"{CHANGE_LANGUAGE_CALLBACK_PREFIX}:"
                        f"{scope_type}:{scope_id}"
                    ),
                )
            ]
        ]
    )


def build_language_selection_keyboard(
    scope_type: str,
    scope_id: int,
    active_language: str,
    response_mode: str = BOT_INFO_LANGUAGE_RESPONSE,
) -> InlineKeyboardMarkup:
    """Build English language choices and mark the active preference."""
    buttons: list[InlineKeyboardButton] = []

    for language, message_key in LANGUAGE_BUTTON_KEYS.items():
        label = get_message(message_key)

        if language == active_language:
            label = f"✅ {label}"

        callback_data = (
            f"{SET_LANGUAGE_CALLBACK_PREFIX}:{language}:"
            f"{scope_type}:{scope_id}"
        )

        if response_mode == COMMAND_LANGUAGE_RESPONSE:
            callback_data = f"{callback_data}:{COMMAND_LANGUAGE_RESPONSE}"

        buttons.append(
            InlineKeyboardButton(
                text=label,
                callback_data=callback_data,
            )
        )

    keyboard = [buttons]

    if response_mode == BOT_INFO_LANGUAGE_RESPONSE:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=get_message("language_back_button"),
                    callback_data=(
                        f"{BACK_TO_LANGUAGE_SETTINGS_CALLBACK_PREFIX}:"
                        f"{scope_type}:{scope_id}"
                    ),
                )
            ]
        )

    return InlineKeyboardMarkup(keyboard)
