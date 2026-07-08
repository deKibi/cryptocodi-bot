# telegram_bot/services/account_creation_date.py

# Standard Libraries
from bisect import bisect_left
from datetime import date
from typing import Final

# Custom Modules
from telegram_bot.localization.language_preferences import DEFAULT_LANGUAGE
from telegram_bot.localization.messages import get_message


# Approximation data
# Initial historical samples are adapted from the MIT-licensed GetIDs dataset:
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
    (1_624_349_999, date(2021, 1, 15)),
    (1_974_255_900, date(2021, 10, 12)),
    (5_240_968_131, date(2022, 5, 15)),
)
_ANCHOR_IDS: Final[tuple[int, ...]] = tuple(
    user_id for user_id, _creation_date in _ACCOUNT_AGE_ANCHORS
)


def _format_month_year(
    creation_date: date,
    language: str = DEFAULT_LANGUAGE,
) -> str:
    month_name = get_message(
        f"month_{creation_date.month}",
        language=language,
    )
    return f"{month_name} {creation_date.year}"


def estimate_account_creation_month(
    user_id: int,
    language: str = DEFAULT_LANGUAGE,
) -> str:
    """Estimate a Telegram account creation month from its numeric ID."""
    first_id, first_date = _ACCOUNT_AGE_ANCHORS[0]
    last_id, last_date = _ACCOUNT_AGE_ANCHORS[-1]

    if user_id < first_id:
        return get_message(
            "date_before",
            language=language,
            month_year=_format_month_year(first_date, language),
        )

    if user_id > last_id:
        return get_message(
            "date_after",
            language=language,
            month_year=_format_month_year(last_date, language),
        )

    upper_index = bisect_left(_ANCHOR_IDS, user_id)
    upper_id, upper_date = _ACCOUNT_AGE_ANCHORS[upper_index]

    if user_id == upper_id:
        return _format_month_year(upper_date, language)

    lower_id, lower_date = _ACCOUNT_AGE_ANCHORS[upper_index - 1]
    id_position = (user_id - lower_id) / (upper_id - lower_id)
    date_range_days = upper_date.toordinal() - lower_date.toordinal()
    estimated_ordinal = lower_date.toordinal() + round(
        id_position * date_range_days
    )

    return _format_month_year(
        date.fromordinal(estimated_ordinal),
        language,
    )
