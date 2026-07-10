# cryptocodi bot

Telegram utility bot for the [@cryptocodi](https://t.me/cryptocodi)
crypto community. Works in private messages and Telegram groups.

## Features

- detects up to the configured limit of UTC, GMT/UTC offset, CET, and KYIV
  times in one message and converts them between supported timezones;
- detects cryptocurrency and basic fiat currency amounts
  (USD, EUR, CAD, PLN, RUB, UAH) and approximately converts them to USD
  and UAH;
- supports tickers, full coin names, compact amounts with `k` (thousands)
  and `m` (millions) suffixes, and multiple crypto pairs in one message;
- shows 24-hour price changes for one unit of cryptocurrency or a supported
  fiat currency;
- adds CoinGecko chart links and a crypto-response delete button;
- calculates simple mathematical expressions with `+`, `-`, `*`, `/`, `**`
  and parentheses;
- calculates crypto expressions such as `3*2 BNB` and converts the result;
- recognizes `×`, Latin `x`, and Cyrillic `х` as multiplication;
- the `/id` command shows current chat and user data, accepts
  `/id <user_id>`, and supports selecting another entity in a private chat;
- supports English, Ukrainian, and Russian messages, stores separate language
  preferences for users and groups, and allows only group administrators to
  change the group language;
- fetches current rates through the CoinGecko Demo API;
- writes general logs and separate logs for detected messages;
- limits the daily number of conversions and CoinGecko requests;
- updates the related reply after a message is edited and does not reply again
  if crypto values, UTC time, or a mathematical expression did not change.

## Commands

- `/start` or `/help` — show information, examples, and change language;
- `/language` — change the bot message language; in groups, the command is
  available only to the owner and administrators;
- `/id` — show the current chat and user ID;
- `/id <user_id>` — approximately estimate the Telegram account creation month.

Message examples:

```text
10:00 UTC
10:00 GMT+3
10:00 CET
10:00 KYIV
start 10:00 UTC, finish 12:00 CET
Event starts at 10:00utc
0.3 BNB
25k USDT
1m BNB
Price: 0,34 ETH
1 bitcoin
100 EUR
100 CAD
100 PLN
3*2
(10 + 5) / 3
3*2 BNB
/id
/id 603206097
/language
```

## Local setup

Python 3.10 or newer is required.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Fill `.env` with your own values:

- `TELEGRAM_BOT_TOKEN` — token from BotFather;
- `COINGECKO_API_KEY` — CoinGecko Demo API key;
- `MAX_TIME_MATCHES_PER_MESSAGE` — maximum timezone matches processed from
  one message, `5` by default;
- the remaining variables control limits, parser caps, and priority
  users/groups.

The real `.env` must not be committed to Git.

Install development dependencies and run tests:

```bash
python -m pip install -r requirements-dev.txt
pytest
```

Run time conversion coverage:

```bash
pytest --cov=time_converter --cov=telegram_bot.handlers.time_message_handler
```

Run the bot:

```bash
python main.py
```

## Simple Linux launch with screen

Install system packages:

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip screen
```

Clone the project and prepare the environment:

```bash
git clone <repository-url>
cd cryptocodi-bot
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
nano .env
```

Create a `screen` session and start the bot:

```bash
screen -S cryptocodi-bot
source .venv/bin/activate
python main.py
```

To leave the bot running in the background, press `Ctrl+A`, then `D`.

Return to the session:

```bash
screen -r cryptocodi-bot
```

Stop the bot with `Ctrl+C` inside the screen session.

## Structure

- `time_converter/` — UTC time parsing and conversion;
- `crypto_converter/` — amount parsing, coin lookup, and price fetching;
- `calculator/` — parsing and safe calculation of mathematical expressions;
- `telegram_bot/` — Telegram handlers, response formatting, and logging;
- `telegram_bot/localization/` — translations and user language preferences;
- `telegram_bot/state/` — limited in-memory state for processed messages;
- `main.py` — bot entry point.
