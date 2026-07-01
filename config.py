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


def get_positive_int_env(variable_name: str, default: int) -> int:
    """Read a positive integer environment variable or use its default."""
    value = os.getenv(variable_name)

    if value is None or not value.strip():
        return default

    try:
        parsed_value = int(value)
    except ValueError as error:
        raise ValueError(
            f"Environment variable {variable_name} must be an integer"
        ) from error

    if parsed_value <= 0:
        raise ValueError(
            f"Environment variable {variable_name} must be greater than zero"
        )

    return parsed_value


TELEGRAM_BOT_TOKEN: Final[str] = get_required_env(
    variable_name="TELEGRAM_BOT_TOKEN",
)

COINGECKO_API_KEY: Final[str] = get_required_env(
    variable_name="COINGECKO_API_KEY",
)

CRYPTO_CONVERSIONS_PER_USER_PER_DAY: Final[int] = get_positive_int_env(
    variable_name="CRYPTO_CONVERSIONS_PER_USER_PER_DAY",
    default=10,
)

COINGECKO_REQUESTS_PER_DAY: Final[int] = get_positive_int_env(
    variable_name="COINGECKO_REQUESTS_PER_DAY",
    default=250,
)

MAX_CRYPTO_PAIRS_PER_MESSAGE: Final[int] = get_positive_int_env(
    variable_name="MAX_CRYPTO_PAIRS_PER_MESSAGE",
    default=5,
)


if __name__ == "__main__":
    print("Application configuration loaded successfully.")
