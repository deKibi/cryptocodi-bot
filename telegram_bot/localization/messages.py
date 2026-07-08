# telegram_bot/localization/messages.py

# Standard Libraries
from typing import Final


# User-facing messages
MESSAGES: Final[dict[str, str]] = {
    "bot_info": "\n".join(
        (
            "Привіт! Це @cryptocodi bot.",
            "",
            "<b>Що бот вміє зараз:</b>",
            "• знаходити UTC-час у повідомленнях і переводити його "
            "в Kyiv та CET (центральноєвропейський час, Відень)",
            "• знаходити суми криптовалют і базових фіатних валют "
            "(USD, EUR, CAD, UAH) та приблизно переводити їх у USD та UAH",
            "• показувати зміну курсу за 24 години та відкривати "
            "графіки монет",
            "• обчислювати прості математичні й криптовалютні вирази",
            "• показувати ID поточного чату й користувача та приблизну "
            "дату створення Telegram-акаунта",
            "• у приватному чаті відкривати меню вибору іншого "
            "користувача, бота, групи або каналу",
            "",
            "<b>Приклади:</b>",
            "",
            "<code>10:00 UTC</code>",
            "<code>0.3 BNB</code>",
            "<code>25k USDT</code>",
            "<code>1m BNB</code>",
            "<code>1 bitcoin</code>",
            "<code>100 EUR</code>",
            "<code>100 CAD</code>",
            "<code>(10 + 5) / 3</code>",
            "<code>3*2 BNB</code>",
            "<code>/id</code>",
            "<code>/id 603206097</code>",
            "",
            "<b>Команди:</b>",
            "<code>/start</code> або <code>/help</code> — переглянути "
            "це повідомлення",
            "<code>/id</code> — переглянути ID чату й користувача або "
            "приблизну дату створення за ID",
            "",
            "Автор: @deKibi",
            "Канал: @cryptocodi",
            "",
            "Вихідний код: "
            "<a href=\"https://github.com/deKibi/cryptocodi-bot\">"
            "GitHub</a>",
        )
    ),
    "command_start": "Show bot info and supported formats",
    "command_help": "Show bot help and usage examples",
    "command_id": "Show IDs or estimate account creation date",
    "calculation_error": "Не вдалося обчислити вираз.",
    "personal_crypto_limit": (
        "Ліміт криптоконвертацій на сьогодні вичерпано. "
        "Спробуйте завтра."
    ),
    "global_crypto_limit": (
        "Загальний ліміт криптоконвертацій вичерпано. "
        "Спробуйте пізніше."
    ),
    "calculation_response": (
        "<b>{expression}</b> = <code>{result}</code>"
    ),
    "crypto_24h_change": "{change}% за 24г",
    "crypto_change_text": " | {change}",
    "coin_label": "{coin_name} ({ticker})",
    "crypto_conversion": (
        "{amount_prefix}{coin_label}{change_text}:\n"
        "{total_usd} usd\n"
        "{total_uah} uah"
    ),
    "crypto_responses": "<code>{conversions}</code>",
    "crypto_calculation_response": (
        "<b>{expression} = </b><code>{amount}</code>\n"
        "<code>{amount_prefix}{coin_label}</code>:\n"
        "<code>{total_usd} usd</code>\n"
        "<code>{total_uah} uah</code>"
    ),
    "time_response": (
        "<code>{first_line_prefix}┬─> {kyiv_time} KYIV\n"
        "{continuation_indent}├─> {central_europe_time} CET\n"
        "{continuation_indent}└─> {utc_time} UTC\n\n"
        "UTC — Coordinated Universal Time (UTC+00:00)</code>"
    ),
    "invalid_user_id": (
        "Вкажіть один додатний цілий ID користувача Telegram."
    ),
    "positive_user_ids_only": (
        "Підтримуються лише додатні ID користувачів Telegram. "
        "ID чатів чи груп не підтримуються."
    ),
    "current_id_response": (
        "<b>CHAT:</b>\n"
        "  <b>title:</b> {chat_title}\n"
        "  <b>type:</b> {chat_type}\n"
        "  <b>username:</b> {chat_username}\n"
        "  <b>ID:</b> {chat_id}\n\n"
        "<b>YOU:</b>\n"
        "  <b>first name:</b> {first_name}\n"
        "  <b>last name:</b> {last_name}\n"
        "  <b>username:</b> {user_username}\n"
        "  <b>language:</b> {language_code}\n"
        "  <b>ID:</b> {user_id}\n"
        "⭐<b>Creation date</b>⭐ <b>(approximately):</b> "
        "{creation_month}"
    ),
    "user_id_response": (
        "<b>USER:</b>\n"
        "  <b>ID:</b> <code>{user_id}</code>\n"
        "  ⭐<b>Creation date</b>⭐ <b>(approximately):</b> "
        "<code>{creation_month}</code>"
    ),
    "chat_id_response": (
        "<b>CHAT:</b>\n"
        "  <b>ID:</b> <code>{chat_id}</code>"
    ),
    "entity_selection_prompt": (
        "{user_mention}, select an entity (Chat, Channel, User or Bot) "
        "to retrieve its ID"
    ),
    "missing_value": "-",
    "monospace_value": "<code>{value}</code>",
    "user_mention": "<a href=\"tg://user?id={user_id}\">{name}</a>",
    "find_different_id_button": "Find a different ID",
    "select_chat_button": "Chat",
    "select_channel_button": "Channel",
    "select_user_button": "User",
    "select_bot_button": "Bot",
    "select_entity_placeholder": "Select an entity",
    "delete_button": "Delete",
    "coin_chart_button": "📈 {coin_name}",
    "date_before": "before {month_year}",
    "date_after": "after {month_year}",
    "month_1": "January",
    "month_2": "February",
    "month_3": "March",
    "month_4": "April",
    "month_5": "May",
    "month_6": "June",
    "month_7": "July",
    "month_8": "August",
    "month_9": "September",
    "month_10": "October",
    "month_11": "November",
    "month_12": "December",
}


def get_message(key: str, **values: object) -> str:
    """Return a user-facing message and format its dynamic values."""
    message = MESSAGES[key]

    if not values:
        return message

    return message.format(**values)
