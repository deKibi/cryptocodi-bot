# crypto_converter/usage_limiter.py

# Standard Libraries
from datetime import date, datetime, timezone
from threading import Lock
from typing import Optional

# Custom Modules
from config import (
    COINGECKO_REQUESTS_PER_DAY,
    CRYPTO_CONVERSIONS_PER_USER_PER_DAY,
    PRIORITY_GROUP_CONVERT_LIMIT,
    PRIORITY_GROUP_ID,
    PRIORITY_USER_CONVERT_LIMIT,
    PRIORITY_USER_ID,
)


class CoinGeckoDailyRequestLimitExceeded(RuntimeError):
    """Indicate that the daily CoinGecko request limit was reached."""


class CryptoUsageLimiter:
    """Track conversion scopes and global API requests for one UTC day."""

    def __init__(
        self,
        user_conversion_limit: int,
        coingecko_request_limit: int,
        priority_group_id: Optional[int] = None,
        priority_user_id: Optional[int] = None,
        priority_group_conversion_limit: Optional[int] = None,
        priority_user_conversion_limit: Optional[int] = None,
    ) -> None:
        self._user_conversion_limit = user_conversion_limit
        self._coingecko_request_limit = coingecko_request_limit
        self._priority_group_id = priority_group_id
        self._priority_user_id = priority_user_id
        self._priority_group_conversion_limit = (
            priority_group_conversion_limit
        )
        self._priority_user_conversion_limit = (
            priority_user_conversion_limit
        )
        self._usage_date = self._get_utc_date()
        self._conversion_counts: dict[tuple[str, int], int] = {}
        self._coingecko_requests = 0
        self._lock = Lock()

    @staticmethod
    def _get_utc_date() -> date:
        return datetime.now(tz=timezone.utc).date()

    def _reset_if_new_day(self) -> None:
        current_date = self._get_utc_date()

        if current_date == self._usage_date:
            return

        self._usage_date = current_date
        self._conversion_counts.clear()
        self._coingecko_requests = 0

    def _get_conversion_scope(
        self,
        user_id: Optional[int],
        chat_id: Optional[int],
    ) -> tuple[Optional[tuple[str, int]], Optional[int]]:
        if (
            chat_id is not None
            and chat_id == self._priority_group_id
            and self._priority_group_conversion_limit is not None
        ):
            return (
                ("group", chat_id),
                self._priority_group_conversion_limit,
            )

        if (
            user_id is not None
            and user_id == self._priority_user_id
            and self._priority_user_conversion_limit is not None
        ):
            return (
                ("user", user_id),
                self._priority_user_conversion_limit,
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
        conversion_scope, conversion_limit = self._get_conversion_scope(
            user_id=user_id,
            chat_id=chat_id,
        )

        if conversion_scope is None or conversion_limit is None:
            return True

        with self._lock:
            self._reset_if_new_day()
            conversion_count = self._conversion_counts.get(
                conversion_scope,
                0,
            )

            if conversion_count >= conversion_limit:
                return False

            self._conversion_counts[conversion_scope] = conversion_count + 1
            return True

    def release_user_conversion(
        self,
        user_id: Optional[int],
        chat_id: Optional[int] = None,
    ) -> None:
        """Release a reserved conversion that did not produce a result."""
        conversion_scope, conversion_limit = self._get_conversion_scope(
            user_id=user_id,
            chat_id=chat_id,
        )

        if conversion_scope is None or conversion_limit is None:
            return

        with self._lock:
            self._reset_if_new_day()
            conversion_count = self._conversion_counts.get(
                conversion_scope,
                0,
            )

            if conversion_count <= 1:
                self._conversion_counts.pop(conversion_scope, None)
                return

            self._conversion_counts[conversion_scope] = conversion_count - 1

    def acquire_coingecko_request(self) -> None:
        """Reserve one global CoinGecko request or raise at the daily limit."""
        with self._lock:
            self._reset_if_new_day()

            if self._coingecko_requests >= self._coingecko_request_limit:
                raise CoinGeckoDailyRequestLimitExceeded(
                    "Daily CoinGecko request limit reached"
                )

            self._coingecko_requests += 1


crypto_usage_limiter = CryptoUsageLimiter(
    user_conversion_limit=CRYPTO_CONVERSIONS_PER_USER_PER_DAY,
    coingecko_request_limit=COINGECKO_REQUESTS_PER_DAY,
    priority_group_id=PRIORITY_GROUP_ID,
    priority_user_id=PRIORITY_USER_ID,
    priority_group_conversion_limit=PRIORITY_GROUP_CONVERT_LIMIT,
    priority_user_conversion_limit=PRIORITY_USER_CONVERT_LIMIT,
)
