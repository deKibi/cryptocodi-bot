# tests/crypto_converter/test_usage_limiter.py

# Standard Libraries
from datetime import date

# Third-party Libraries
import pytest

# Custom Modules
from crypto_converter.usage_limiter import (
    CoinGeckoDailyRequestLimitExceeded,
    CryptoUsageLimiter,
)


class InMemoryUsageLimitStorage:
    def __init__(self) -> None:
        self.used_units: dict[tuple[date, str, int], int] = {}

    def try_acquire(
        self,
        usage_date: date,
        counter_type: str,
        subject_id: int,
        units: int,
        limit: int,
    ) -> bool:
        key = (usage_date, counter_type, subject_id)
        next_used_units = self.used_units.get(key, 0) + units

        if next_used_units > limit:
            return False

        self.used_units[key] = next_used_units
        return True

    def release(
        self,
        usage_date: date,
        counter_type: str,
        subject_id: int,
        units: int,
    ) -> None:
        key = (usage_date, counter_type, subject_id)
        self.used_units[key] = max(self.used_units.get(key, 0) - units, 0)


def test_conversion_attempt_and_completion_use_one_full_limit() -> None:
    limiter = CryptoUsageLimiter(
        user_conversion_limit=1,
        coingecko_request_limit=10,
        storage=InMemoryUsageLimitStorage(),
    )

    assert limiter.try_acquire_conversion_attempt(user_id=1) is True
    assert limiter.try_complete_conversion(user_id=1) is True
    assert limiter.try_acquire_conversion_attempt(user_id=1) is False


def test_release_conversion_attempt_restores_half_limit() -> None:
    limiter = CryptoUsageLimiter(
        user_conversion_limit=1,
        coingecko_request_limit=10,
        storage=InMemoryUsageLimitStorage(),
    )

    assert limiter.try_acquire_conversion_attempt(user_id=1) is True
    limiter.release_conversion_attempt(user_id=1)
    assert limiter.try_acquire_user_conversion(user_id=1) is True


def test_priority_user_limit_cannot_lower_base_limit() -> None:
    limiter = CryptoUsageLimiter(
        user_conversion_limit=2,
        coingecko_request_limit=10,
        priority_user_ids=frozenset({42}),
        priority_user_conversion_limit=1,
        storage=InMemoryUsageLimitStorage(),
    )

    assert limiter.try_acquire_user_conversion(user_id=42) is True
    assert limiter.try_acquire_user_conversion(user_id=42) is True
    assert limiter.try_acquire_user_conversion(user_id=42) is False


def test_priority_group_limit_cannot_lower_base_limit() -> None:
    limiter = CryptoUsageLimiter(
        user_conversion_limit=2,
        coingecko_request_limit=10,
        priority_group_ids=frozenset({100}),
        priority_group_conversion_limit=1,
        storage=InMemoryUsageLimitStorage(),
    )

    assert limiter.try_acquire_user_conversion(user_id=1, chat_id=100) is True
    assert limiter.try_acquire_user_conversion(user_id=2, chat_id=100) is True
    assert limiter.try_acquire_user_conversion(user_id=3, chat_id=100) is False


def test_coingecko_daily_request_limit_raises_after_limit() -> None:
    limiter = CryptoUsageLimiter(
        user_conversion_limit=10,
        coingecko_request_limit=1,
        storage=InMemoryUsageLimitStorage(),
    )

    limiter.acquire_coingecko_request()

    with pytest.raises(CoinGeckoDailyRequestLimitExceeded):
        limiter.acquire_coingecko_request()
