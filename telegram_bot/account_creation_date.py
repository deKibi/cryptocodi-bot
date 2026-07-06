# telegram_bot/account_creation_date.py

# Standard Libraries
from bisect import bisect_left
from datetime import date
from typing import Final


# Approximation data
# Historical samples are adapted from the MIT-licensed GetIDs dataset:
# https://github.com/AmanoTeam/python-getids
_ACCOUNT_AGE_ANCHORS: Final[tuple[tuple[int, date], ...]] = (
    (2_768_409, date(2013, 10, 31)),
    (54_845_238, date(2014, 9, 21)),
    (101_323_197, date(2015, 3, 13)),
    (157_242_073, date(2015, 11, 6)),
    (225_034_354, date(2016, 6, 18)),
    (352_940_995, date(2017, 2, 24)),
    (400_169_472, date(2017, 7, 31)),
    (603_206_097, date(2018, 6, 15)),
    (805_158_066, date(2019, 7, 15)),
    (1_974_255_900, date(2021, 10, 12)),
)
_ANCHOR_IDS: Final[tuple[int, ...]] = tuple(
    user_id for user_id, _creation_date in _ACCOUNT_AGE_ANCHORS
)
_MONTH_NAMES: Final[tuple[str, ...]] = (
    "",
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)


def _format_month_year(creation_date: date) -> str:
    return f"{_MONTH_NAMES[creation_date.month]} {creation_date.year}"


def estimate_account_creation_month(user_id: int) -> str:
    """Estimate a Telegram account creation month from its numeric ID."""
    first_id, first_date = _ACCOUNT_AGE_ANCHORS[0]
    last_id, last_date = _ACCOUNT_AGE_ANCHORS[-1]

    if user_id < first_id:
        return f"before {_format_month_year(first_date)}"

    if user_id > last_id:
        return f"after {_format_month_year(last_date)}"

    upper_index = bisect_left(_ANCHOR_IDS, user_id)
    upper_id, upper_date = _ACCOUNT_AGE_ANCHORS[upper_index]

    if user_id == upper_id:
        return _format_month_year(upper_date)

    lower_id, lower_date = _ACCOUNT_AGE_ANCHORS[upper_index - 1]
    id_position = (user_id - lower_id) / (upper_id - lower_id)
    date_range_days = upper_date.toordinal() - lower_date.toordinal()
    estimated_ordinal = lower_date.toordinal() + round(
        id_position * date_range_days
    )

    return _format_month_year(date.fromordinal(estimated_ordinal))
