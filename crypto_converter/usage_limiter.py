# crypto_converter/usage_limiter.py

# Standard Libraries
from datetime import date, datetime, timezone
from threading import Lock
from typing import Optional

# Custom Modules
from config import (
    COINGECKO_REQUESTS_PER_DAY,
    CRYPTO_CONVERSIONS_PER_USER_PER_DAY,
)


class CoinGeckoDailyRequestLimitExceeded(RuntimeError):
    """Indicate that the daily CoinGecko request limit was reached."""


class CryptoUsageLimiter:
    """Track per-user conversions and global API requests for one UTC day."""

    def __init__(
        self,
        user_conversion_limit: int,
        coingecko_request_limit: int,
    ) -> None:
        self._user_conversion_limit = user_conversion_limit
        self._coingecko_request_limit = coingecko_request_limit
        self._usage_date = self._get_utc_date()
        self._user_conversions: dict[int, int] = {}
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
        self._user_conversions.clear()
        self._coingecko_requests = 0

    def try_acquire_user_conversion(self, user_id: Optional[int]) -> bool:
        """Reserve one daily conversion for a user when capacity remains."""
        if user_id is None:
            return True

        with self._lock:
            self._reset_if_new_day()
            conversion_count = self._user_conversions.get(user_id, 0)

            if conversion_count >= self._user_conversion_limit:
                return False

            self._user_conversions[user_id] = conversion_count + 1
            return True

    def release_user_conversion(self, user_id: Optional[int]) -> None:
        """Release a reserved conversion that did not produce a result."""
        if user_id is None:
            return

        with self._lock:
            self._reset_if_new_day()
            conversion_count = self._user_conversions.get(user_id, 0)

            if conversion_count <= 1:
                self._user_conversions.pop(user_id, None)
                return

            self._user_conversions[user_id] = conversion_count - 1

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
)
