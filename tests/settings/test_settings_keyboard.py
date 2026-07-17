# tests/settings/test_settings_keyboard.py

# Standard Libraries
import re

# Custom Modules
from telegram_bot.handlers.settings_command_handler import (
    SETTINGS_DEFAULT_LIMIT_CALLBACK_PATTERN,
    SETTINGS_HOME_CALLBACK_PATTERN,
    SETTINGS_LIMIT_MENU_CALLBACK_PATTERN,
    SETTINGS_SET_LIMIT_CALLBACK_PATTERN,
    SETTINGS_TOGGLE_CALLBACK_PATTERN,
    format_settings_home,
)
from telegram_bot.keyboards.language_keyboard import build_change_language_keyboard
from telegram_bot.keyboards.settings_keyboard import (
    build_settings_home_keyboard,
    build_settings_limit_keyboard,
)
from telegram_bot.localization.language_preferences import CHAT_LANGUAGE_SCOPE
from telegram_bot.settings.group_settings import GroupSettings


def test_settings_home_uses_localized_ukrainian_labels() -> None:
    settings = GroupSettings(
        crypto_converter_enabled=True,
        calculator_enabled=False,
        time_converter_enabled=True,
        max_crypto_pairs_per_message=5,
        max_time_matches_per_message=3,
    )

    assert format_settings_home(settings, "uk") == (
        "<b>Налаштування бота</b>\n\n"
        "Криптоконвертер: ✅\n"
        "Калькулятор: ❌\n"
        "Конвертер часу: ✅\n\n"
        "Максимум криптоконвертацій у повідомленні: 5\n"
        "Максимум часових конвертацій у повідомленні: 3"
    )


def test_settings_command_keyboard_does_not_show_bot_info_back() -> None:
    keyboard = build_settings_home_keyboard(
        -100,
        GroupSettings(calculator_enabled=False),
    )

    rows = keyboard.inline_keyboard

    assert rows[0][0].text == "Crypto converter: ✅"
    assert rows[1][0].text == "Calculator: ❌"
    assert rows[2][0].text == "Time converter: ✅"
    assert rows[-1][0].text == "Delete"
    assert all(row[0].text != "Back" for row in rows)


def test_bot_info_settings_keyboard_shows_back_before_delete() -> None:
    keyboard = build_settings_home_keyboard(
        -100,
        GroupSettings(),
        requester_user_id=456,
    )

    rows = keyboard.inline_keyboard

    assert rows[-2][0].text == "Back"
    assert rows[-2][0].callback_data == "settings_back:-100:456"
    assert rows[-1][0].text == "Delete"
    assert rows[0][0].callback_data == "settings_toggle:-100:crypto:bot_info:456"


def test_bot_info_root_keyboard_uses_action_emojis() -> None:
    keyboard = build_change_language_keyboard(
        CHAT_LANGUAGE_SCOPE,
        -100,
        456,
    )

    rows = keyboard.inline_keyboard

    assert rows[0][0].text == "🌐 Change Language"
    assert rows[1][0].text == "⚙️ Settings"
    assert rows[1][0].callback_data == "settings_home:-100:bot_info:456"
    assert rows[2][0].text == "Delete"


def test_settings_patterns_accept_bot_info_context() -> None:
    assert re.fullmatch(
        SETTINGS_HOME_CALLBACK_PATTERN,
        "settings_home:-100:bot_info:456",
    )
    assert re.fullmatch(
        SETTINGS_TOGGLE_CALLBACK_PATTERN,
        "settings_toggle:-100:crypto:bot_info:456",
    )
    assert re.fullmatch(
        SETTINGS_LIMIT_MENU_CALLBACK_PATTERN,
        "settings_limit:-100:time:bot_info:456",
    )
    assert re.fullmatch(
        SETTINGS_SET_LIMIT_CALLBACK_PATTERN,
        "settings_set_limit:-100:crypto:3:bot_info:456",
    )
    assert re.fullmatch(
        SETTINGS_DEFAULT_LIMIT_CALLBACK_PATTERN,
        "settings_default_limit:-100:crypto:bot_info:456",
    )


def test_settings_limit_keyboard_shows_default_limit_button() -> None:
    keyboard = build_settings_limit_keyboard(
        -100,
        "crypto",
        1,
        requester_user_id=456,
    )

    rows = keyboard.inline_keyboard

    assert rows[0][0].text == "✅ 1"
    assert rows[1][0].text.startswith("Default (")
    assert rows[1][0].callback_data == (
        "settings_default_limit:-100:crypto:bot_info:456"
    )
    assert rows[2][0].text == "Back"
