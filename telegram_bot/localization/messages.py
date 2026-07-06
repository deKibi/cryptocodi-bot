# telegram_bot/localization/messages.py

# Standard Libraries
from typing import Final


# Languages
DEFAULT_LANGUAGE: Final[str] = "uk"
SUPPORTED_LANGUAGES: Final[frozenset[str]] = frozenset({"uk", "en"})


# User-facing messages
MESSAGES: Final[dict[str, dict[str, str]]] = {
    "uk": {
        "bot_info": "\n".join(
            (
                "Привіт! Це @cryptocodi bot.",
                "",
                "<b>Що бот вміє зараз:</b>",
                "• знаходити UTC-час у повідомленнях і переводити його "
                "в Kyiv та CET (центральноєвропейський час, Відень)",
                "• знаходити суми криптовалют і приблизно переводити їх "
                "в USD та UAH",
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
                "<code>1 bitcoin</code>",
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
        "command_start": "Показати інформацію про бота і формати",
        "command_help": "Показати довідку та приклади",
        "command_id": "Показати ID або приблизну дату створення",
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
            "<code>{first_line_prefix}┬─> {kyiv_time} КИЇВ\n"
            "{continuation_indent}├─> {central_europe_time} CET\n"
            "{continuation_indent}└─> {utc_time} UTC\n\n"
            "UTC — UTC (UTC+00:00)</code>"
        ),
        "invalid_user_id": (
            "Вкажіть один додатний цілий ID користувача Telegram."
        ),
        "positive_user_ids_only": (
            "Підтримуються лише додатні ID користувачів Telegram. "
            "ID чатів чи груп не підтримуються."
        ),
        "current_id_response": (
            "<b>ЧАТ:</b>\n"
            "  <b>назва:</b> {chat_title}\n"
            "  <b>тип:</b> {chat_type}\n"
            "  <b>ім’я користувача:</b> {chat_username}\n"
            "  <b>ID:</b> {chat_id}\n\n"
            "<b>ВИ:</b>\n"
            "  <b>ім’я:</b> {first_name}\n"
            "  <b>прізвище:</b> {last_name}\n"
            "  <b>ім’я користувача:</b> {user_username}\n"
            "  <b>мова:</b> {language_code}\n"
            "  <b>ID:</b> {user_id}\n"
            "⭐<b>Дата створення</b>⭐ <b>(приблизно):</b> "
            "{creation_month}"
        ),
        "user_id_response": (
            "<b>КОРИСТУВАЧ:</b>\n"
            "  <b>ID:</b> <code>{user_id}</code>\n"
            "  ⭐<b>Дата створення</b>⭐ <b>(приблизно):</b> "
            "<code>{creation_month}</code>"
        ),
        "chat_id_response": (
            "<b>ЧАТ:</b>\n"
            "  <b>ID:</b> <code>{chat_id}</code>"
        ),
        "chat_type_private": "приватний",
        "chat_type_group": "група",
        "chat_type_supergroup": "супергрупа",
        "chat_type_channel": "канал",
        "entity_selection_prompt": (
            "{user_mention}, виберіть сутність (чат, канал, користувача "
            "або бота), щоб отримати її ID"
        ),
        "missing_value": "-",
        "monospace_value": "<code>{value}</code>",
        "user_mention": "<a href=\"tg://user?id={user_id}\">{name}</a>",
        "find_different_id_button": "Знайти інший ID",
        "select_chat_button": "Чат",
        "select_channel_button": "Канал",
        "select_user_button": "Користувач",
        "select_bot_button": "Бот",
        "select_entity_placeholder": "Виберіть сутність",
        "delete_button": "Видалити",
        "coin_chart_button": "📈 {coin_name}",
        "date_before": "до {month_year}",
        "date_after": "після {month_year}",
        "month_1": "січень",
        "month_2": "лютий",
        "month_3": "березень",
        "month_4": "квітень",
        "month_5": "травень",
        "month_6": "червень",
        "month_7": "липень",
        "month_8": "серпень",
        "month_9": "вересень",
        "month_10": "жовтень",
        "month_11": "листопад",
        "month_12": "грудень",
        "month_genitive_1": "січня",
        "month_genitive_2": "лютого",
        "month_genitive_3": "березня",
        "month_genitive_4": "квітня",
        "month_genitive_5": "травня",
        "month_genitive_6": "червня",
        "month_genitive_7": "липня",
        "month_genitive_8": "серпня",
        "month_genitive_9": "вересня",
        "month_genitive_10": "жовтня",
        "month_genitive_11": "листопада",
        "month_genitive_12": "грудня",
    },
    "en": {
        "bot_info": "\n".join(
            (
                "Hi! This is @cryptocodi bot.",
                "",
                "<b>What the bot can do:</b>",
                "• find UTC times in messages and convert them to Kyiv and "
                "CET (Central European Time, Vienna)",
                "• find cryptocurrency amounts and approximately convert "
                "them to USD and UAH",
                "• show 24-hour price changes and open coin charts",
                "• calculate simple mathematical and cryptocurrency "
                "expressions",
                "• show the current chat and user IDs and an approximate "
                "Telegram account creation date",
                "• open a menu for selecting another user, bot, group, or "
                "channel in a private chat",
                "",
                "<b>Examples:</b>",
                "",
                "<code>10:00 UTC</code>",
                "<code>0.3 BNB</code>",
                "<code>25k USDT</code>",
                "<code>1 bitcoin</code>",
                "<code>(10 + 5) / 3</code>",
                "<code>3*2 BNB</code>",
                "<code>/id</code>",
                "<code>/id 603206097</code>",
                "",
                "<b>Commands:</b>",
                "<code>/start</code> or <code>/help</code> — view this "
                "message",
                "<code>/id</code> — view chat and user IDs or estimate an "
                "account creation date by ID",
                "",
                "Author: @deKibi",
                "Channel: @cryptocodi",
                "",
                "Source code: "
                "<a href=\"https://github.com/deKibi/cryptocodi-bot\">"
                "GitHub</a>",
            )
        ),
        "command_start": "Show bot information and supported formats",
        "command_help": "Show help and usage examples",
        "command_id": "Show IDs or estimate an account creation date",
        "calculation_error": "Could not calculate the expression.",
        "personal_crypto_limit": (
            "Your daily cryptocurrency conversion limit has been reached. "
            "Try again tomorrow."
        ),
        "global_crypto_limit": (
            "The bot's cryptocurrency conversion limit has been reached. "
            "Try again later."
        ),
        "calculation_response": (
            "<b>{expression}</b> = <code>{result}</code>"
        ),
        "crypto_24h_change": "{change}% in 24h",
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
        "invalid_user_id": "Enter one positive integer Telegram user ID.",
        "positive_user_ids_only": (
            "Only positive Telegram user IDs are supported. "
            "Chat and group IDs are not supported."
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
        "chat_type_private": "private",
        "chat_type_group": "group",
        "chat_type_supergroup": "supergroup",
        "chat_type_channel": "channel",
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
        "month_genitive_1": "January",
        "month_genitive_2": "February",
        "month_genitive_3": "March",
        "month_genitive_4": "April",
        "month_genitive_5": "May",
        "month_genitive_6": "June",
        "month_genitive_7": "July",
        "month_genitive_8": "August",
        "month_genitive_9": "September",
        "month_genitive_10": "October",
        "month_genitive_11": "November",
        "month_genitive_12": "December",
    },
}


def get_message(
    key: str,
    language: str = DEFAULT_LANGUAGE,
    **values: object,
) -> str:
    """Return a localized message and format its dynamic values."""
    localized_messages = MESSAGES.get(language, MESSAGES[DEFAULT_LANGUAGE])
    message = localized_messages[key]

    if not values:
        return message

    return message.format(**values)
