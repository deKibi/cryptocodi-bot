# config.py

# Standard Libraries
import os
from typing import Final

# Third-Party Libraries
from dotenv import load_dotenv


load_dotenv()


def get_required_env(variable_name: str) -> str:
    """
    Read a required environment variable.

    Raises an error if the variable is missing or empty.
    """
    value = os.getenv(variable_name)

    if value is None or not value.strip():
        raise ValueError(
            f"Required environment variable {variable_name} is not set"
        )

    return value.strip()


TELEGRAM_BOT_TOKEN: Final[str] = get_required_env(
    variable_name="TELEGRAM_BOT_TOKEN",
)


if __name__ == "__main__":
    print("Telegram bot configuration loaded successfully.")