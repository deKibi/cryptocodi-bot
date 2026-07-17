# telegram_bot/localization/messages.py

# Standard Libraries
from typing import Final

# Custom Modules
from telegram_bot.localization.language_preferences import DEFAULT_LANGUAGE


# User-facing messages
MESSAGES: Final[dict[str, dict[str, str]]] = {
    "bot_info": {
        "uk": "\n".join(
            (
                "Привіт! Це @cryptocodi bot.",
                "",
                "<b>Що бот вміє зараз:</b>",
                "• знаходити UTC, UTC/GMT-зміщення, CET та KYIV часи в "
                "повідомленнях і переводити їх між підтримуваними часовими "
                "поясами",
                "• знаходити суми криптовалют і базових фіатних валют "
                "(USD, EUR, CAD, PLN, RUB, UAH) та приблизно переводити їх у "
                "USD та UAH",
                "• переводити суми в доларах у криптовалюту",
                "• показувати зміну курсу за 24 години та відкривати "
                "графіки монет",
                "• обчислювати прості математичні й криптовалютні вирази",
                "• показувати ID поточного чату й користувача та приблизну "
                "дату створення Telegram-акаунта",
                "• у приватному чаті відкривати меню вибору іншого "
                "користувача, бота, групи або каналу",
                "• підтримувати English, українську та російську мови "
                "повідомлень",
                "",
                "<b>Приклади:</b>",
                "",
                "<code>10:00 UTC</code>",
                "<code>10:00 GMT+3</code>",
                "<code>10:00 CET</code>",
                "<code>10:00 KYIV</code>",
                "<code>старт 10:00 UTC, фініш 12:00 CET</code>",
                "<code>0.3 BNB</code>",
                "<code>10$ BNB</code>",
                "<code>25k USDT</code>",
                "<code>1m BNB</code>",
                "<code>1 bitcoin</code>",
                "<code>100 EUR</code>",
                "<code>100 CAD</code>",
                "<code>100 PLN</code>",
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
                "<code>/language</code> — змінити мову бота",
                "",
                "Автор: @deKibi",
                "Канал: @cryptocodi",
                "",
                "Вихідний код: "
                "<a href=\"https://github.com/deKibi/cryptocodi-bot\">"
                "GitHub</a>",
            )
        ),
        "en": "\n".join(
            (
                "Hi! This is @cryptocodi bot.",
                "",
                "<b>What the bot can do:</b>",
                "• find UTC, GMT offsets, CET and KYIV times in messages "
                "and convert them between supported timezones",
                "• find cryptocurrency and basic fiat amounts "
                "(USD, EUR, CAD, PLN, RUB, UAH) and approximately convert them "
                "to USD and UAH",
                "• convert USD amounts to cryptocurrency amounts",
                "• show 24-hour price changes and open coin charts",
                "• calculate simple mathematical and cryptocurrency "
                "expressions",
                "• show the current chat and user IDs and estimate a "
                "Telegram account creation date",
                "• open a menu in private chats to select another user, "
                "bot, group or channel",
                "• support English, Ukrainian and Russian messages",
                "",
                "<b>Examples:</b>",
                "",
                "<code>10:00 UTC</code>",
                "<code>10:00 GMT+3</code>",
                "<code>10:00 CET</code>",
                "<code>10:00 KYIV</code>",
                "<code>start 10:00 UTC, finish 12:00 CET</code>",
                "<code>0.3 BNB</code>",
                "<code>10$ BNB</code>",
                "<code>25k USDT</code>",
                "<code>1m BNB</code>",
                "<code>1 bitcoin</code>",
                "<code>100 EUR</code>",
                "<code>100 CAD</code>",
                "<code>100 PLN</code>",
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
                "<code>/language</code> — change the bot language",
                "",
                "Author: @deKibi",
                "Channel: @cryptocodi",
                "",
                "Source code: "
                "<a href=\"https://github.com/deKibi/cryptocodi-bot\">"
                "GitHub</a>",
            )
        ),
        "ru": "\n".join(
            (
                "Привет! Это @cryptocodi bot.",
                "",
                "<b>Что бот умеет сейчас:</b>",
                "• находить UTC, UTC/GMT-смещения, CET и KYIV время в "
                "сообщениях и переводить его между поддерживаемыми часовыми "
                "поясами",
                "• находить суммы криптовалют и базовых фиатных валют "
                "(USD, EUR, CAD, PLN, RUB, UAH) и приблизительно переводить их "
                "в USD и UAH",
                "• переводить суммы в долларах в криптовалюту",
                "• показывать изменение курса за 24 часа и открывать "
                "графики монет",
                "• вычислять простые математические и криптовалютные "
                "выражения",
                "• показывать ID текущего чата и пользователя, а также "
                "примерную дату создания Telegram-аккаунта",
                "• в личном чате открывать меню выбора другого "
                "пользователя, бота, группы или канала",
                "• поддерживать English, украинский и русский языки "
                "сообщений",
                "",
                "<b>Примеры:</b>",
                "",
                "<code>10:00 UTC</code>",
                "<code>10:00 GMT+3</code>",
                "<code>10:00 CET</code>",
                "<code>10:00 KYIV</code>",
                "<code>старт 10:00 UTC, финиш 12:00 CET</code>",
                "<code>0.3 BNB</code>",
                "<code>10$ BNB</code>",
                "<code>25k USDT</code>",
                "<code>1m BNB</code>",
                "<code>1 bitcoin</code>",
                "<code>100 EUR</code>",
                "<code>100 CAD</code>",
                "<code>100 PLN</code>",
                "<code>(10 + 5) / 3</code>",
                "<code>3*2 BNB</code>",
                "<code>/id</code>",
                "<code>/id 603206097</code>",
                "",
                "<b>Команды:</b>",
                "<code>/start</code> или <code>/help</code> — посмотреть "
                "это сообщение",
                "<code>/id</code> — посмотреть ID чата и пользователя или "
                "примерную дату создания по ID",
                "<code>/language</code> — изменить язык бота",
                "",
                "Автор: @deKibi",
                "Канал: @cryptocodi",
                "",
                "Исходный код: "
                "<a href=\"https://github.com/deKibi/cryptocodi-bot\">"
                "GitHub</a>",
            )
        ),
    },
    "command_start": {"en": "Show bot info and supported formats"},
    "command_help": {"en": "Show bot help and usage examples"},
    "command_id": {"en": "Show IDs or estimate account creation date"},
    "command_language": {"en": "Change bot language"},
    "calculation_error": {
        "uk": "Не вдалося обчислити вираз.",
        "en": "Could not calculate the expression.",
        "ru": "Не удалось вычислить выражение.",
    },
    "personal_crypto_limit": {
        "uk": (
            "Ліміт криптоконвертацій на сьогодні вичерпано. "
            "Спробуйте завтра."
        ),
        "en": (
            "Your crypto conversion limit for today has been reached. "
            "Try again tomorrow."
        ),
        "ru": (
            "Ваш лимит криптоконвертаций на сегодня исчерпан. "
            "Попробуйте завтра."
        ),
    },
    "global_crypto_limit": {
        "uk": (
            "Загальний ліміт криптоконвертацій вичерпано. "
            "Спробуйте пізніше."
        ),
        "en": (
            "The bot's global crypto conversion limit has been reached. "
            "Try again later."
        ),
        "ru": (
            "Общий лимит криптоконвертаций бота исчерпан. "
            "Попробуйте позже."
        ),
    },
    "calculation_response": {
        "en": "<b>{expression}</b> = <code>{result}</code>",
    },
    "crypto_24h_change": {
        "uk": "{change}% за 24г",
        "en": "{change}% in 24h",
        "ru": "{change}% за 24ч",
    },
    "crypto_change_text": {"en": " | {change}"},
    "coin_label": {"en": "{coin_name} ({ticker})"},
    "crypto_conversion": {
        "en": (
            "{amount_prefix}{coin_label}{change_text}:\n"
            "{total_usd} usd\n"
            "{total_uah} uah"
        ),
    },
    "crypto_responses": {"en": "<code>{conversions}</code>"},
    "crypto_calculation_response": {
        "en": (
            "<b>{expression} = </b><code>{amount}</code>\n"
            "<code>{amount_prefix}{coin_label}</code>:\n"
            "<code>{total_usd} usd</code>\n"
            "<code>{total_uah} uah</code>"
        ),
    },
    "fiat_to_crypto_response": {
        "en": (
            "<code>{usd_amount}$ {ticker}:</code>\n"
            "<code>{crypto_amount} {ticker}</code>"
        ),
    },
    "fiat_to_crypto_minimum_amount": {
        "uk": (
            "Мінімальна сума для конвертації доларів у криптовалюту — $0.10."
        ),
        "en": "Minimum USD amount for crypto conversion is $0.10.",
        "ru": (
            "Минимальная сумма для конвертации долларов в криптовалюту — "
            "$0.10."
        ),
    },
    "time_response": {
        "uk": (
            "<code>{conversion_blocks}</code>\n\n"
            "{timezone_descriptions}"
        ),
        "en": (
            "<code>{conversion_blocks}</code>\n\n"
            "{timezone_descriptions}"
        ),
        "ru": (
            "<code>{conversion_blocks}</code>\n\n"
            "{timezone_descriptions}"
        ),
    },
    "timezone_description_line": {
        "en": "<b>{timezone}</b> — <i>{description}</i> ({utc_offset})",
    },
    "timezone_description_utc": {
        "uk": "UTC",
        "en": "UTC",
        "ru": "UTC",
    },
    "timezone_description_kyiv": {
        "uk": "KYIV",
        "en": "KYIV",
        "ru": "KYIV",
    },
    "timezone_description_cet": {
        "uk": "CET",
        "en": "CET",
        "ru": "CET",
    },
    "timezone_description_cest": {
        "uk": "Europe/Monaco • Monaco Time",
        "en": "Europe/Monaco • Monaco Time",
        "ru": "Europe/Monaco • Monaco Time",
    },
    "invalid_user_id": {
        "uk": "Вкажіть один додатний цілий ID користувача Telegram.",
        "en": "Enter one positive integer Telegram user ID.",
        "ru": "Укажите один положительный целочисленный ID пользователя Telegram.",
    },
    "positive_user_ids_only": {
        "uk": (
            "Підтримуються лише додатні ID користувачів Telegram. "
            "ID чатів чи груп не підтримуються."
        ),
        "en": (
            "Only positive Telegram user IDs are supported. "
            "Chat and group IDs are not supported."
        ),
        "ru": (
            "Поддерживаются только положительные ID пользователей Telegram. "
            "ID чатов и групп не поддерживаются."
        ),
    },
    "current_id_response": {
        "uk": (
            "<b>ЧАТ:</b>\n"
            "  <b>назва:</b> {chat_title}\n"
            "  <b>тип:</b> {chat_type}\n"
            "  <b>username:</b> {chat_username}\n"
            "  <b>ID:</b> {chat_id}\n\n"
            "<b>ВИ:</b>\n"
            "  <b>імʼя:</b> {first_name}\n"
            "  <b>прізвище:</b> {last_name}\n"
            "  <b>username:</b> {user_username}\n"
            "  <b>мова:</b> {language_code}\n"
            "  <b>ID:</b> {user_id}\n"
            "⭐<b>Дата створення</b>⭐ <b>(приблизно):</b> "
            "{creation_month}"
        ),
        "en": (
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
        "ru": (
            "<b>ЧАТ:</b>\n"
            "  <b>название:</b> {chat_title}\n"
            "  <b>тип:</b> {chat_type}\n"
            "  <b>username:</b> {chat_username}\n"
            "  <b>ID:</b> {chat_id}\n\n"
            "<b>ВЫ:</b>\n"
            "  <b>имя:</b> {first_name}\n"
            "  <b>фамилия:</b> {last_name}\n"
            "  <b>username:</b> {user_username}\n"
            "  <b>язык:</b> {language_code}\n"
            "  <b>ID:</b> {user_id}\n"
            "⭐<b>Дата создания</b>⭐ <b>(приблизительно):</b> "
            "{creation_month}"
        ),
    },
    "user_id_response": {
        "uk": (
            "<b>КОРИСТУВАЧ:</b>\n"
            "  <b>ID:</b> <code>{user_id}</code>\n"
            "  ⭐<b>Дата створення</b>⭐ <b>(приблизно):</b> "
            "<code>{creation_month}</code>"
        ),
        "en": (
            "<b>USER:</b>\n"
            "  <b>ID:</b> <code>{user_id}</code>\n"
            "  ⭐<b>Creation date</b>⭐ <b>(approximately):</b> "
            "<code>{creation_month}</code>"
        ),
        "ru": (
            "<b>ПОЛЬЗОВАТЕЛЬ:</b>\n"
            "  <b>ID:</b> <code>{user_id}</code>\n"
            "  ⭐<b>Дата создания</b>⭐ <b>(приблизительно):</b> "
            "<code>{creation_month}</code>"
        ),
    },
    "chat_id_response": {
        "uk": "<b>ЧАТ:</b>\n  <b>ID:</b> <code>{chat_id}</code>",
        "en": "<b>CHAT:</b>\n  <b>ID:</b> <code>{chat_id}</code>",
        "ru": "<b>ЧАТ:</b>\n  <b>ID:</b> <code>{chat_id}</code>",
    },
    "entity_selection_prompt": {
        "uk": (
            "{user_mention}, виберіть сутність (Chat, Channel, User або "
            "Bot), щоб отримати її ID"
        ),
        "en": (
            "{user_mention}, select an entity (Chat, Channel, User or Bot) "
            "to retrieve its ID"
        ),
        "ru": (
            "{user_mention}, выберите сущность (Chat, Channel, User или "
            "Bot), чтобы получить её ID"
        ),
    },
    "missing_value": {"en": "-"},
    "monospace_value": {"en": "<code>{value}</code>"},
    "user_mention": {
        "en": "<a href=\"tg://user?id={user_id}\">{name}</a>",
    },
    "find_different_id_button": {"en": "Find a different ID"},
    "select_chat_button": {"en": "Chat"},
    "select_channel_button": {"en": "Channel"},
    "select_user_button": {"en": "User"},
    "select_bot_button": {"en": "Bot"},
    "select_entity_placeholder": {"en": "Select an entity"},
    "delete_button": {"en": "Delete"},
    "delete_denied": {
        "uk": "Ця кнопка не для вас.",
        "en": "This button is not for you.",
        "ru": "Эта кнопка не для вас.",
    },
    "coin_chart_button": {"en": "📈 {coin_name}"},
    "change_language_button": {"en": "Change Language"},
    "invite_bot_button": {"en": "➕ Add bot to your chat"},
    "language_back_button": {"en": "Back"},
    "choose_language": {
        "uk": "Оберіть мову:",
        "en": "Choose language:",
        "ru": "Выберите язык:",
    },
    "language_changed": {
        "uk": "Мову змінено.",
        "en": "Language changed.",
        "ru": "Язык изменён.",
    },
    "group_language_admin_only": {
        "uk": (
            "Лише адміністратори групи можуть змінювати мову бота "
            "в цьому чаті."
        ),
        "en": (
            "Only group admins can change the bot language in this chat."
        ),
        "ru": (
            "Только администраторы группы могут изменять язык бота "
            "в этом чате."
        ),
    },
    "language_english_button": {"en": "English"},
    "language_ukrainian_button": {"en": "Ukrainian"},
    "language_russian_button": {"en": "Russian"},
    "date_before": {
        "uk": "до {month_year}",
        "en": "before {month_year}",
        "ru": "до {month_year}",
    },
    "date_after": {
        "uk": "після {month_year}",
        "en": "after {month_year}",
        "ru": "после {month_year}",
    },
    "month_1": {"uk": "Січень", "en": "January", "ru": "Январь"},
    "month_2": {"uk": "Лютий", "en": "February", "ru": "Февраль"},
    "month_3": {"uk": "Березень", "en": "March", "ru": "Март"},
    "month_4": {"uk": "Квітень", "en": "April", "ru": "Апрель"},
    "month_5": {"uk": "Травень", "en": "May", "ru": "Май"},
    "month_6": {"uk": "Червень", "en": "June", "ru": "Июнь"},
    "month_7": {"uk": "Липень", "en": "July", "ru": "Июль"},
    "month_8": {"uk": "Серпень", "en": "August", "ru": "Август"},
    "month_9": {"uk": "Вересень", "en": "September", "ru": "Сентябрь"},
    "month_10": {"uk": "Жовтень", "en": "October", "ru": "Октябрь"},
    "month_11": {"uk": "Листопад", "en": "November", "ru": "Ноябрь"},
    "month_12": {"uk": "Грудень", "en": "December", "ru": "Декабрь"},
}


def get_message(
    key: str,
    language: str = DEFAULT_LANGUAGE,
    **values: object,
) -> str:
    """Return a localized user-facing message with English fallback."""
    translations = MESSAGES[key]
    message = translations.get(language, translations[DEFAULT_LANGUAGE])

    if not values:
        return message

    return message.format(**values)
