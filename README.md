# cryptocodi bot

Telegram utility-бот для криптоспільноти [@cryptocodi](https://t.me/cryptocodi).
Працює в особистих повідомленнях і Telegram-групах.

## Можливості

- знаходить UTC-час у тексті та переводить його в Kyiv і CET;
- знаходить суми криптовалют і базових фіатних валют
  (USD, EUR, CAD, UAH) та приблизно переводить їх у USD та UAH;
- підтримує тікери, повні назви монет, compact amounts і декілька
  crypto-пар в одному повідомленні;
- показує зміну курсу за 24 години для одиниці криптовалюти або
  підтримуваної фіатної валюти;
- додає посилання на графіки CoinGecko та кнопку видалення crypto-відповіді;
- обчислює прості математичні вирази з `+`, `-`, `*`, `/`, `**` і дужками;
- обчислює crypto-вирази на кшталт `3*2 BNB` і конвертує результат;
- розпізнає `×`, латинську `x` і кириличну `х` як множення;
- команда `/id` показує дані поточного чату й користувача, приймає
  `/id <user_id>` та підтримує вибір іншої сутності у приватному чаті;
- отримує актуальні курси через CoinGecko Demo API;
- веде загальні логи та окремі логи знайдених повідомлень;
- обмежує денну кількість конвертацій і CoinGecko-запитів;
- оновлює пов'язану відповідь після редагування повідомлення та не відповідає
  повторно, якщо crypto-значення, UTC-час або математичний вираз не змінилися.

## Команди

- `/start` або `/help` — показати інформацію про можливості та приклади;
- `/id` — показати ID поточного чату й користувача;
- `/id <user_id>` — приблизно визначити місяць створення Telegram-акаунта.

Приклади повідомлень:

```text
10:00 UTC
Старт події о 10:00utc
0.3 BNB
25k USDT
Ціна: 0,34 ETH
1 bitcoin
100 EUR
100 CAD
3*2
(10 + 5) / 3
3*2 BNB
/id
/id 603206097
```

## Локальний запуск

Потрібен Python 3.10 або новіший.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Заповніть `.env` власними значеннями:

- `TELEGRAM_BOT_TOKEN` — токен від BotFather;
- `COINGECKO_API_KEY` — CoinGecko Demo API key;
- решта змінних керує лімітами та priority user/group.

Реальний `.env` не можна додавати в Git.

Запуск бота:

```bash
python main.py
```

## Простий запуск на Linux через screen

Встановіть системні пакети:

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip screen
```

Склонуйте проєкт і підготуйте середовище:

```bash
git clone <repository-url>
cd cryptocodi-bot
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
nano .env
```

Створіть `screen`-сесію та запустіть бота:

```bash
screen -S cryptocodi-bot
source .venv/bin/activate
python main.py
```

Щоб залишити бота працювати у фоні, натисніть `Ctrl+A`, потім `D`.

Повернутися до сесії:

```bash
screen -r cryptocodi-bot
```

Зупинити бота можна через `Ctrl+C` всередині screen-сесії.

## Структура

- `time_converter/` — парсинг і конвертація UTC-часу;
- `crypto_converter/` — парсинг сум, пошук монет і отримання цін;
- `calculator/` — парсинг і безпечне обчислення математичних виразів;
- `telegram_bot/` — Telegram handlers, форматування відповідей і логування;
- `telegram_bot/state/` — обмежений in-memory стан оброблених повідомлень;
- `main.py` — точка запуску бота.
