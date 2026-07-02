# crypto_converter/usage_limiter.py

# Standard Libraries
from datetime import date, datetime, timezone
from typing import Final, Optional

# Custom Modules
from config import (
    COINGECKO_REQUESTS_PER_DAY,
    CRYPTO_CONVERSIONS_PER_USER_PER_DAY,
    PRIORITY_GROUP_CONVERT_LIMIT,
    PRIORITY_GROUPS_ID,
    PRIORITY_USER_CONVERT_LIMIT,
    PRIORITY_USERS_ID,
)
from crypto_converter.usage_limit_storage import UsageLimitStorage


# Conversion quota units
FULL_CONVERSION_UNITS: Final[int] = 2
CONVERSION_ATTEMPT_UNITS: Final[int] = 1
GLOBAL_REQUEST_SCOPE_TYPE: Final[str] = "coingecko_requests"
GLOBAL_REQUEST_SCOPE_ID: Final[int] = 0


class CoinGeckoDailyRequestLimitExceeded(RuntimeError):
    """Indicate that the daily CoinGecko request limit was reached."""


class CryptoUsageLimiter:
    """Track conversion scopes and global API requests for one UTC day."""

    def __init__(
        self,
        user_conversion_limit: int,
        coingecko_request_limit: int,
        priority_group_ids: frozenset[int] = frozenset(),
        priority_user_ids: frozenset[int] = frozenset(),
        priority_group_conversion_limit: Optional[int] = None,
        priority_user_conversion_limit: Optional[int] = None,
        storage: Optional[UsageLimitStorage] = None,
    ) -> None:
        self._user_conversion_limit = user_conversion_limit
        self._coingecko_request_limit = coingecko_request_limit
        self._priority_group_ids = priority_group_ids
        self._priority_user_ids = priority_user_ids
        self._priority_group_conversion_limit = (
            priority_group_conversion_limit
        )
        self._priority_user_conversion_limit = (
            priority_user_conversion_limit
        )
        self._storage = storage if storage is not None else UsageLimitStorage()

    @staticmethod
    def _get_utc_date() -> date:
        return datetime.now(tz=timezone.utc).date()

    def _get_conversion_scope(
        self,
        user_id: Optional[int],
        chat_id: Optional[int],
    ) -> tuple[Optional[tuple[str, int]], Optional[int]]:
        if (
            chat_id is not None
            and chat_id in self._priority_group_ids
        ):
            priority_group_limit = (
                self._priority_group_conversion_limit
                or self._user_conversion_limit
            )

            return (
                ("group", chat_id),
                max(
                    self._user_conversion_limit,
                    priority_group_limit,
                ),
            )

        if (
            user_id is not None
            and user_id in self._priority_user_ids
        ):
            priority_user_limit = (
                self._priority_user_conversion_limit
                or self._user_conversion_limit
            )

            return (
                ("user", user_id),
                max(
                    self._user_conversion_limit,
                    priority_user_limit,
                ),
            )

        if user_id is None:
            return None, None

        return ("user", user_id), self._user_conversion_limit

    def try_acquire_user_conversion(
        self,
        user_id: Optional[int],
        chat_id: Optional[int] = None,
    ) -> bool:
        """Reserve one daily conversion for the applicable usage scope."""
        return self._try_acquire_conversion_units(
            user_id=user_id,
            chat_id=chat_id,
            units=FULL_CONVERSION_UNITS,
        )

    def try_acquire_conversion_attempt(
        self,
        user_id: Optional[int],
        chat_id: Optional[int] = None,
    ) -> bool:
        """Reserve half a conversion before resolving a ticker."""
        return self._try_acquire_conversion_units(
            user_id=user_id,
            chat_id=chat_id,
            units=CONVERSION_ATTEMPT_UNITS,
        )

    def try_complete_conversion(
        self,
        user_id: Optional[int],
        chat_id: Optional[int] = None,
    ) -> bool:
        """Reserve the second half after a successful ticker resolution."""
        return self._try_acquire_conversion_units(
            user_id=user_id,
            chat_id=chat_id,
            units=CONVERSION_ATTEMPT_UNITS,
        )

    def _try_acquire_conversion_units(
        self,
        user_id: Optional[int],
        chat_id: Optional[int],
        units: int,
    ) -> bool:
        conversion_scope, conversion_limit = self._get_conversion_scope(
            user_id=user_id,
            chat_id=chat_id,
        )

        if conversion_scope is None or conversion_limit is None:
            return True

        conversion_limit_units = conversion_limit * FULL_CONVERSION_UNITS

        return self._storage.try_acquire(
            usage_date=self._get_utc_date(),
            scope_type=conversion_scope[0],
            scope_id=conversion_scope[1],
            units=units,
            limit=conversion_limit_units,
        )

    def release_user_conversion(
        self,
        user_id: Optional[int],
        chat_id: Optional[int] = None,
    ) -> None:
        """Release a reserved conversion that did not produce a result."""
        self._release_conversion_units(
            user_id=user_id,
            chat_id=chat_id,
            units=FULL_CONVERSION_UNITS,
        )

    def release_conversion_attempt(
        self,
        user_id: Optional[int],
        chat_id: Optional[int] = None,
    ) -> None:
        """Release a half-conversion reservation after an API failure."""
        self._release_conversion_units(
            user_id=user_id,
            chat_id=chat_id,
            units=CONVERSION_ATTEMPT_UNITS,
        )

    def _release_conversion_units(
        self,
        user_id: Optional[int],
        chat_id: Optional[int],
        units: int,
    ) -> None:
        conversion_scope, conversion_limit = self._get_conversion_scope(
            user_id=user_id,
            chat_id=chat_id,
        )

        if conversion_scope is None or conversion_limit is None:
            return

        self._storage.release(
            usage_date=self._get_utc_date(),
            scope_type=conversion_scope[0],
            scope_id=conversion_scope[1],
            units=units,
        )

    def acquire_coingecko_request(self) -> None:
        """Reserve one global CoinGecko request or raise at the daily limit."""
        request_acquired = self._storage.try_acquire(
            usage_date=self._get_utc_date(),
            scope_type=GLOBAL_REQUEST_SCOPE_TYPE,
            scope_id=GLOBAL_REQUEST_SCOPE_ID,
            units=1,
            limit=self._coingecko_request_limit,
        )

        if not request_acquired:
            raise CoinGeckoDailyRequestLimitExceeded(
                "Daily CoinGecko request limit reached"
            )


crypto_usage_limiter = CryptoUsageLimiter(
    user_conversion_limit=CRYPTO_CONVERSIONS_PER_USER_PER_DAY,
    coingecko_request_limit=COINGECKO_REQUESTS_PER_DAY,
    priority_group_ids=PRIORITY_GROUPS_ID,
    priority_user_ids=PRIORITY_USERS_ID,
    priority_group_conversion_limit=PRIORITY_GROUP_CONVERT_LIMIT,
    priority_user_conversion_limit=PRIORITY_USER_CONVERT_LIMIT,
)
