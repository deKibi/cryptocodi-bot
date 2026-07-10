# time_converter/time_utils.py

# Standard Libraries
from datetime import datetime, timedelta, timezone
from typing import Final
from zoneinfo import ZoneInfo


# Timezones
UTC_TIMEZONE: Final[ZoneInfo] = ZoneInfo("UTC")
KYIV_TIMEZONE: Final[ZoneInfo] = ZoneInfo("Europe/Kyiv")
CENTRAL_EUROPE_TIMEZONE: Final[ZoneInfo] = ZoneInfo("Europe/Vienna")
CEST_TIMEZONE: Final[timezone] = timezone(timedelta(hours=2))
TIMEZONES_BY_LABEL: Final[dict[str, ZoneInfo | timezone]] = {
    "UTC": UTC_TIMEZONE,
    "KYIV": KYIV_TIMEZONE,
    "CET": CENTRAL_EUROPE_TIMEZONE,
    "CEST": CEST_TIMEZONE,
}


def convert_utc_to_kyiv(utc_datetime: datetime) -> datetime:
    """Convert a timezone-aware UTC datetime to the Kyiv timezone."""
    return utc_datetime.astimezone(KYIV_TIMEZONE)


def convert_utc_to_cet(utc_datetime: datetime) -> datetime:
    """Convert a timezone-aware UTC datetime to Central Europe local time."""
    return utc_datetime.astimezone(CENTRAL_EUROPE_TIMEZONE)


def convert_utc_to_central_europe(utc_datetime: datetime) -> datetime:
    """Convert a timezone-aware UTC datetime to Central Europe local time."""
    return convert_utc_to_cet(utc_datetime)


def convert_to_timezone(
    source_datetime: datetime,
    timezone_label: str,
) -> datetime:
    """Convert a timezone-aware datetime to a supported timezone."""
    return source_datetime.astimezone(TIMEZONES_BY_LABEL[timezone_label])


if __name__ == "__main__":
    utc_datetime = datetime.now(tz=UTC_TIMEZONE).replace(
        hour=13,
        minute=0,
        second=0,
        microsecond=0,
    )
    kyiv_datetime = convert_utc_to_kyiv(utc_datetime)
    central_europe_datetime = convert_utc_to_central_europe(utc_datetime)

    print("UTC datetime:", utc_datetime)
    print("Kyiv datetime:", kyiv_datetime, "Object type:", type(kyiv_datetime))
    print(
        "Central Europe datetime:",
        central_europe_datetime,
        "Object type:",
        type(central_europe_datetime),
    )
