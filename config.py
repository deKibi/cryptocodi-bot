# config.py

# Standard Libraries
import logging
import os
from typing import Final, Optional

# Third-Party Libraries
from dotenv import load_dotenv


load_dotenv()

LOGGER = logging.getLogger(__name__)


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


def get_optional_int_env(variable_name: str) -> Optional[int]:
    """Read an optional integer environment variable."""
    value = os.getenv(variable_name)

    if value is None or not value.strip():
        return None

    normalized_value = value.strip()

    try:
        return int(normalized_value)
    except ValueError as error:
        raise ValueError(
            f"Environment variable {variable_name} must be an integer"
        ) from error


def get_int_set_env(variable_name: str) -> frozenset[int]:
    """Read comma-separated integers or return an empty set."""
    value = os.getenv(variable_name)

    if value is None or not value.strip():
        return frozenset()

    parsed_values: set[int] = set()

    for raw_value in value.split(","):
        normalized_value = raw_value.strip()

        if not normalized_value:
            raise ValueError(
                f"Environment variable {variable_name} must contain "
                "comma-separated integers"
            )

        try:
            parsed_values.add(int(normalized_value))
        except ValueError as error:
            raise ValueError(
                f"Environment variable {variable_name} must contain "
                "comma-separated integers"
            ) from error

    return frozenset(parsed_values)


def get_optional_positive_int_env(variable_name: str) -> Optional[int]:
    """Read an optional positive integer environment variable."""
    parsed_value = get_optional_int_env(variable_name)

    if parsed_value is None:
        return None

    if parsed_value <= 0:
        raise ValueError(
            f"Environment variable {variable_name} must be greater than zero"
        )

    return parsed_value


def _warn_if_priority_config_incomplete(
    priority_name: str,
    priority_configured: bool,
    priority_limit: Optional[int],
) -> None:
    if not priority_configured and priority_limit is not None:
        LOGGER.warning(
            "%s priority conversion limit is configured without an ID; "
            "the priority limit is disabled.",
            priority_name,
        )
    elif priority_configured and priority_limit is None:
        LOGGER.warning(
            "%s priority ID is configured without a conversion limit; "
            "the standard conversion limit will be used.",
            priority_name,
        )


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

PRIORITY_GROUPS_ID: Final[frozenset[int]] = get_int_set_env(
    variable_name="PRIORITY_GROUPS_ID",
)

PRIORITY_USERS_ID: Final[frozenset[int]] = get_int_set_env(
    variable_name="PRIORITY_USERS_ID",
)

PRIORITY_GROUP_CONVERT_LIMIT: Final[Optional[int]] = (
    get_optional_positive_int_env(
        variable_name="PRIORITY_GROUP_CONVERT_LIMIT",
    )
)

PRIORITY_USER_CONVERT_LIMIT: Final[Optional[int]] = (
    get_optional_positive_int_env(
        variable_name="PRIORITY_USER_CONVERT_LIMIT",
    )
)

_warn_if_priority_config_incomplete(
    priority_name="Group",
    priority_configured=bool(PRIORITY_GROUPS_ID),
    priority_limit=PRIORITY_GROUP_CONVERT_LIMIT,
)
_warn_if_priority_config_incomplete(
    priority_name="User",
    priority_configured=bool(PRIORITY_USERS_ID),
    priority_limit=PRIORITY_USER_CONVERT_LIMIT,
)


if __name__ == "__main__":
    print("Application configuration loaded successfully.")
