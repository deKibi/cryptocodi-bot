# time_converter/time_utils.py

# Standard Libraries
from datetime import datetime, timedelta
from typing import Final
from zoneinfo import ZoneInfo


# Timezones
UTC_TIMEZONE: Final[ZoneInfo] = ZoneInfo("UTC")
KYIV_TIMEZONE: Final[ZoneInfo] = ZoneInfo("Europe/Kyiv")
CENTRAL_EUROPE_TIMEZONE: Final[ZoneInfo] = ZoneInfo("Europe/Vienna")
SUPPORTED_TIMEZONES: Final[tuple[ZoneInfo, ...]] = (
    UTC_TIMEZONE,
    KYIV_TIMEZONE,
    CENTRAL_EUROPE_TIMEZONE,
)


def get_current_kyiv_datetime() -> datetime:
    """Return the current timezone-aware datetime in Kyiv."""
    return datetime.now(tz=KYIV_TIMEZONE)


def get_current_utc_datetime() -> datetime:
    """Return the current timezone-aware datetime in UTC."""
    return datetime.now(tz=UTC_TIMEZONE)


def convert_to_utc(
    source_datetime: datetime,
    source_timezone: ZoneInfo,
) -> datetime:
    """Convert a datetime from a supported source timezone to UTC.

    A naive datetime is interpreted as local time in ``source_timezone``.
    A timezone-aware datetime must already use ``source_timezone``.
    """
    if source_timezone not in SUPPORTED_TIMEZONES:
        raise ValueError("source_timezone must be UTC, Europe/Kyiv, or Europe/Vienna")

    if source_datetime.tzinfo is None:
        source_datetime = source_datetime.replace(tzinfo=source_timezone)
    elif source_datetime.tzinfo != source_timezone:
        raise ValueError("source_datetime must use source_timezone")

    return source_datetime.astimezone(UTC_TIMEZONE)


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


def convert_central_europe_to_utc(
    central_europe_datetime: datetime,
) -> datetime:
    """Convert a timezone-aware Vienna datetime to the UTC timezone."""
    return convert_to_utc(
        source_datetime=central_europe_datetime,
        source_timezone=CENTRAL_EUROPE_TIMEZONE,
    )


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
    example_datetime = datetime.now().replace(
        hour=10,
        minute=0,
        second=0,
        microsecond=0,
        tzinfo=None,
    )
    print("Example date:", example_datetime.date())

    utc_datetime = convert_to_utc(example_datetime, UTC_TIMEZONE)
    print("10:00 UTC -> Kyiv:", convert_utc_to_kyiv(utc_datetime))
    print(
        "10:00 UTC -> Central Europe:",
        convert_utc_to_central_europe(utc_datetime),
    )

    central_europe_utc_datetime = convert_to_utc(
        example_datetime,
        CENTRAL_EUROPE_TIMEZONE,
    )
    print(
        "10:00 Central Europe -> Kyiv:",
        convert_utc_to_kyiv(central_europe_utc_datetime),
    )
    print("10:00 Central Europe -> UTC:", central_europe_utc_datetime)

    kyiv_utc_datetime = convert_to_utc(example_datetime, KYIV_TIMEZONE)
    print(
        "10:00 Kyiv -> Central Europe:",
        convert_utc_to_central_europe(kyiv_utc_datetime),
    )
    print("10:00 Kyiv -> UTC:", kyiv_utc_datetime)
