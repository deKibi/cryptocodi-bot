# time_converter/time_utils.py

# Standard Libraries
from datetime import datetime, timedelta
from typing import Final
from zoneinfo import ZoneInfo


# Timezones
UTC_TIMEZONE: Final[ZoneInfo] = ZoneInfo("UTC")
KYIV_TIMEZONE: Final[ZoneInfo] = ZoneInfo("Europe/Kyiv")
CENTRAL_EUROPE_TIMEZONE: Final[ZoneInfo] = ZoneInfo("Europe/Vienna")


def get_current_kyiv_datetime() -> datetime:
    """Return the current timezone-aware datetime in Kyiv."""
    return datetime.now(tz=KYIV_TIMEZONE)


def get_current_utc_datetime() -> datetime:
    """Return the current timezone-aware datetime in UTC."""
    return datetime.now(tz=UTC_TIMEZONE)


def convert_utc_to_kyiv(utc_datetime: datetime) -> datetime:
    """Convert a timezone-aware UTC datetime to the Kyiv timezone."""
    if (
        utc_datetime.tzinfo is None
        or utc_datetime.utcoffset() != timedelta(0)
        or utc_datetime.tzname() != "UTC"
    ):
        raise ValueError("utc_datetime must be a timezone-aware UTC datetime")

    return utc_datetime.astimezone(KYIV_TIMEZONE)


def convert_utc_to_central_europe(utc_datetime: datetime) -> datetime:
    """Convert a timezone-aware UTC datetime to the Vienna timezone."""
    if (
        utc_datetime.tzinfo is None
        or utc_datetime.utcoffset() != timedelta(0)
        or utc_datetime.tzname() != "UTC"
    ):
        raise ValueError("utc_datetime must be a timezone-aware UTC datetime")

    return utc_datetime.astimezone(CENTRAL_EUROPE_TIMEZONE)


def convert_utc_to_utc(utc_datetime: datetime) -> datetime:
    """Normalize a timezone-aware UTC datetime to the IANA UTC timezone."""
    if (
        utc_datetime.tzinfo is None
        or utc_datetime.utcoffset() != timedelta(0)
        or utc_datetime.tzname() != "UTC"
    ):
        raise ValueError("utc_datetime must be a timezone-aware UTC datetime")

    return utc_datetime.astimezone(UTC_TIMEZONE)


if __name__ == "__main__":
    current_utc_datetime = get_current_utc_datetime()
    print("Current UTC datetime:", current_utc_datetime)

    print("Kyiv datetime from UTC:", convert_utc_to_kyiv(current_utc_datetime))
    print(
        "Central Europe datetime (CET) from UTC:",
        convert_utc_to_central_europe(current_utc_datetime),
    )
    print("UTC datetime:", convert_utc_to_utc(current_utc_datetime))
