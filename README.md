# cryptocodi bot

Telegram utility-бот для криптоспільноти [@cryptocodi](https://t.me/cryptocodi).
Працює в особистих повідомленнях і Telegram-групах.

## Можливості

- знаходить UTC-час у тексті та переводить його в Kyiv і CET;
- знаходить суми криптовалют і приблизно переводить їх у USD та UAH;
- підтримує декілька crypto-пар в одному повідомленні;
- отримує актуальні курси через CoinGecko Demo API;
- веде загальні логи та окремі логи знайдених повідомлень;
- обмежує денну кількість конвертацій і CoinGecko-запитів.

Приклади повідомлень:

```text
10:00 UTC
Старт події о 10:00utc
0.3 BNB
25k USDT
Ціна: 0,34 ETH
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
- `telegram_bot/` — Telegram handlers, форматування відповідей і логування;
- `main.py` — точка запуску бота.
