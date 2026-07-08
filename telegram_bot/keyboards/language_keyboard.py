# telegram_bot/keyboards/language_keyboard.py

# Standard Libraries
from typing import Final

# Third-party Libraries
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Custom Modules
from telegram_bot.localization.messages import get_message


# Language selection callbacks
CHANGE_LANGUAGE_CALLBACK_PREFIX: Final[str] = "change_language"
SET_LANGUAGE_CALLBACK_PREFIX: Final[str] = "set_language"
LANGUAGE_BUTTON_KEYS: Final[dict[str, str]] = {
    "en": "language_english_button",
    "uk": "language_ukrainian_button",
    "ru": "language_russian_button",
}


def build_change_language_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Build the action that opens language selection for one user."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=get_message("change_language_button"),
                    callback_data=(
                        f"{CHANGE_LANGUAGE_CALLBACK_PREFIX}:{user_id}"
                    ),
                )
            ]
        ]
    )


def build_language_selection_keyboard(
    user_id: int,
    active_language: str,
) -> InlineKeyboardMarkup:
    """Build English language choices and mark the active preference."""
    buttons: list[InlineKeyboardButton] = []

    for language, message_key in LANGUAGE_BUTTON_KEYS.items():
        label = get_message(message_key)

        if language == active_language:
            label = f"✅ {label}"

        buttons.append(
            InlineKeyboardButton(
                text=label,
                callback_data=(
                    f"{SET_LANGUAGE_CALLBACK_PREFIX}:{language}:{user_id}"
                ),
            )
        )

    return InlineKeyboardMarkup([buttons])
