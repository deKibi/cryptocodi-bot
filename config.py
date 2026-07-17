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


def is_env_configured(variable_name: str) -> bool:
    """Return whether an environment variable is set to a non-empty value."""
    return bool(os.getenv(variable_name, "").strip())


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


def get_positive_int_env_or_default(variable_name: str, default: int) -> int:
    """Read a positive integer or fall back to its default when invalid."""
    value = os.getenv(variable_name)

    if value is None or not value.strip():
        return default

    try:
        parsed_value = int(value)
    except ValueError:
        LOGGER.warning(
            "Environment variable %s must be an integer; using %s default",
            variable_name,
            default,
        )
        return default

    if parsed_value <= 0:
        LOGGER.warning(
            "Environment variable %s must be greater than zero; "
            "using %s default",
            variable_name,
            default,
        )
        return default

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


def _warn_if_priority_limit_below_standard(
    priority_name: str,
    priority_limit: Optional[int],
    standard_limit: int,
) -> None:
    if priority_limit is None or priority_limit >= standard_limit:
        return

    LOGGER.warning(
        "%s priority conversion limit (%d) is lower than the standard "
        "user conversion limit (%d); the standard limit will be used.",
        priority_name,
        priority_limit,
        standard_limit,
    )


def _warn_if_default_env_missing(
    variable_name: str,
    default: int,
) -> None:
    if is_env_configured(variable_name):
        return

    LOGGER.warning(
        "%s is not configured; using %d default.",
        variable_name,
        default,
    )


TELEGRAM_BOT_TOKEN: Final[str] = get_required_env(
    variable_name="TELEGRAM_BOT_TOKEN",
)

COINGECKO_API_KEY: Final[str] = get_required_env(
    variable_name="COINGECKO_API_KEY",
)

DEFAULT_CRYPTO_CONVERSIONS_PER_USER_PER_DAY: Final[int] = 10
CRYPTO_CONVERSIONS_PER_USER_PER_DAY_IS_CONFIGURED: Final[bool] = (
    is_env_configured("CRYPTO_CONVERSIONS_PER_USER_PER_DAY")
)
CRYPTO_CONVERSIONS_PER_USER_PER_DAY: Final[int] = get_positive_int_env(
    variable_name="CRYPTO_CONVERSIONS_PER_USER_PER_DAY",
    default=DEFAULT_CRYPTO_CONVERSIONS_PER_USER_PER_DAY,
)

DEFAULT_COINGECKO_REQUESTS_PER_DAY: Final[int] = 250
COINGECKO_REQUESTS_PER_DAY_IS_CONFIGURED: Final[bool] = is_env_configured(
    "COINGECKO_REQUESTS_PER_DAY"
)
COINGECKO_REQUESTS_PER_DAY: Final[int] = get_positive_int_env(
    variable_name="COINGECKO_REQUESTS_PER_DAY",
    default=DEFAULT_COINGECKO_REQUESTS_PER_DAY,
)

DEFAULT_MAX_CRYPTO_PAIRS_PER_MESSAGE: Final[int] = 5
MAX_CRYPTO_PAIRS_PER_MESSAGE_IS_CONFIGURED: Final[bool] = (
    is_env_configured("MAX_CRYPTO_PAIRS_PER_MESSAGE")
)
MAX_CRYPTO_PAIRS_PER_MESSAGE: Final[int] = get_positive_int_env_or_default(
    variable_name="MAX_CRYPTO_PAIRS_PER_MESSAGE",
    default=DEFAULT_MAX_CRYPTO_PAIRS_PER_MESSAGE,
)

DEFAULT_MAX_TIME_MATCHES_PER_MESSAGE: Final[int] = 5
MAX_TIME_MATCHES_PER_MESSAGE_IS_CONFIGURED: Final[bool] = (
    is_env_configured("MAX_TIME_MATCHES_PER_MESSAGE")
)
MAX_TIME_MATCHES_PER_MESSAGE: Final[int] = get_positive_int_env_or_default(
    variable_name="MAX_TIME_MATCHES_PER_MESSAGE",
    default=DEFAULT_MAX_TIME_MATCHES_PER_MESSAGE,
)

DEFAULT_CRYPTO_MAX_MARKET_CAP_RANK: Final[int] = 1000
CRYPTO_MAX_MARKET_CAP_RANK_IS_CONFIGURED: Final[bool] = (
    is_env_configured("CRYPTO_MAX_MARKET_CAP_RANK")
)
CRYPTO_MAX_MARKET_CAP_RANK: Final[int] = get_positive_int_env(
    variable_name="CRYPTO_MAX_MARKET_CAP_RANK",
    default=DEFAULT_CRYPTO_MAX_MARKET_CAP_RANK,
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


def log_configuration_warnings() -> None:
    """Log warnings for default and invalid optional configuration."""
    _warn_if_default_env_missing(
        variable_name="CRYPTO_CONVERSIONS_PER_USER_PER_DAY",
        default=DEFAULT_CRYPTO_CONVERSIONS_PER_USER_PER_DAY,
    )
    _warn_if_default_env_missing(
        variable_name="COINGECKO_REQUESTS_PER_DAY",
        default=DEFAULT_COINGECKO_REQUESTS_PER_DAY,
    )
    _warn_if_default_env_missing(
        variable_name="MAX_CRYPTO_PAIRS_PER_MESSAGE",
        default=DEFAULT_MAX_CRYPTO_PAIRS_PER_MESSAGE,
    )
    _warn_if_default_env_missing(
        variable_name="MAX_TIME_MATCHES_PER_MESSAGE",
        default=DEFAULT_MAX_TIME_MATCHES_PER_MESSAGE,
    )
    _warn_if_default_env_missing(
        variable_name="CRYPTO_MAX_MARKET_CAP_RANK",
        default=DEFAULT_CRYPTO_MAX_MARKET_CAP_RANK,
    )
    _warn_if_priority_config_incomplete(
        priority_name="Group",
        priority_configured=bool(PRIORITY_GROUPS_ID),
        priority_limit=PRIORITY_GROUP_CONVERT_LIMIT,
    )
    _warn_if_priority_limit_below_standard(
        priority_name="Group",
        priority_limit=PRIORITY_GROUP_CONVERT_LIMIT,
        standard_limit=CRYPTO_CONVERSIONS_PER_USER_PER_DAY,
    )
    _warn_if_priority_config_incomplete(
        priority_name="User",
        priority_configured=bool(PRIORITY_USERS_ID),
        priority_limit=PRIORITY_USER_CONVERT_LIMIT,
    )
    _warn_if_priority_limit_below_standard(
        priority_name="User",
        priority_limit=PRIORITY_USER_CONVERT_LIMIT,
        standard_limit=CRYPTO_CONVERSIONS_PER_USER_PER_DAY,
    )


if __name__ == "__main__":
    print("Application configuration loaded successfully.")
