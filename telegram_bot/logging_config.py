# telegram_bot/logging_config.py

# Standard Libraries
import json
import logging
from datetime import datetime, timezone
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Final

# Third-party Libraries
from telegram import Update


# Logging
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent
LOG_DIRECTORY: Final[Path] = PROJECT_ROOT / "logs"
GENERAL_LOG_PATH: Final[Path] = LOG_DIRECTORY / "bot.log"
DETECTED_MESSAGES_LOG_PATH: Final[Path] = (
    LOG_DIRECTORY / "detected_messages.jsonl"
)
DETECTED_CRYPTO_MESSAGES_LOG_PATH: Final[Path] = (
    LOG_DIRECTORY / "detected_crypto_messages.jsonl"
)
LOG_RETENTION_DAYS: Final[int] = 30
DETECTED_MESSAGES_LOGGER_NAME: Final[str] = "detected_messages"
DETECTED_CRYPTO_MESSAGES_LOGGER_NAME: Final[str] = (
    "detected_crypto_messages"
)
_LOGGING_CONFIGURED = False


def configure_logging() -> None:
    """Configure console, general file, and detected-message logging."""
    global _LOGGING_CONFIGURED

    if _LOGGING_CONFIGURED:
        return

    LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)

    general_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(general_formatter)

    general_file_handler = TimedRotatingFileHandler(
        filename=GENERAL_LOG_PATH,
        when="midnight",
        backupCount=LOG_RETENTION_DAYS,
        encoding="utf-8",
        delay=True,
    )
    general_file_handler.setFormatter(general_formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(general_file_handler)

    detected_messages_handler = TimedRotatingFileHandler(
        filename=DETECTED_MESSAGES_LOG_PATH,
        when="midnight",
        backupCount=LOG_RETENTION_DAYS,
        encoding="utf-8",
        delay=True,
    )
    detected_messages_handler.setFormatter(logging.Formatter("%(message)s"))

    detected_messages_logger = logging.getLogger(
        DETECTED_MESSAGES_LOGGER_NAME
    )
    detected_messages_logger.setLevel(logging.INFO)
    detected_messages_logger.propagate = False
    detected_messages_logger.addHandler(detected_messages_handler)

    detected_crypto_messages_handler = TimedRotatingFileHandler(
        filename=DETECTED_CRYPTO_MESSAGES_LOG_PATH,
        when="midnight",
        backupCount=LOG_RETENTION_DAYS,
        encoding="utf-8",
        delay=True,
    )
    detected_crypto_messages_handler.setFormatter(
        logging.Formatter("%(message)s")
    )

    detected_crypto_messages_logger = logging.getLogger(
        DETECTED_CRYPTO_MESSAGES_LOGGER_NAME
    )
    detected_crypto_messages_logger.setLevel(logging.INFO)
    detected_crypto_messages_logger.propagate = False
    detected_crypto_messages_logger.addHandler(
        detected_crypto_messages_handler
    )

    logging.getLogger("httpx").setLevel(logging.WARNING)
    _LOGGING_CONFIGURED = True


def get_update_metadata(update: Update) -> dict[str, object]:
    """Return user and chat metadata suitable for structured logging."""
    user = update.effective_user
    chat = update.effective_chat

    return {
        "user_id": user.id if user is not None else None,
        "username": user.username if user is not None else None,
        "display_name": user.full_name if user is not None else None,
        "chat_id": chat.id if chat is not None else None,
        "chat_type": chat.type if chat is not None else None,
    }


def format_log_metadata(metadata: dict[str, object]) -> str:
    """Format user and chat metadata as a compact single log line."""
    return " | ".join(
        (
            f"user_id={metadata['user_id']!r}",
            f"username={metadata['username']!r}",
            f"display_name={metadata['display_name']!r}",
            f"chat_id={metadata['chat_id']!r}",
            f"chat_type={metadata['chat_type']!r}",
        )
    )


def log_detected_message(message_data: dict[str, object]) -> None:
    """Write one detected UTC message as a JSON Lines record."""
    record = {
        "logged_at": datetime.now(tz=timezone.utc).isoformat(),
        **message_data,
    }
    logger = logging.getLogger(DETECTED_MESSAGES_LOGGER_NAME)
    logger.info(json.dumps(record, ensure_ascii=False))


def log_detected_crypto_message(message_data: dict[str, object]) -> None:
    """Write one detected crypto message as a JSON Lines record."""
    record = {
        "logged_at": datetime.now(tz=timezone.utc).isoformat(),
        **message_data,
    }
    logger = logging.getLogger(DETECTED_CRYPTO_MESSAGES_LOGGER_NAME)
    logger.info(json.dumps(record, ensure_ascii=False))
