# time_converter/utc_time_parser.py

# Standard Libraries
import re
from datetime import datetime
from typing import Final, Optional
from zoneinfo import ZoneInfo


# UTC time parsing
UTC_TIMEZONE: Final[ZoneInfo] = ZoneInfo("UTC")
UTC_TIME_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?<![\w:.])(?P<hour>(?:[01]?\d|2[0-3]))"
    r"(?::(?P<minute>[0-5]\d))? ?UTC\b",
    flags=re.IGNORECASE,
)


def parse_utc_time_from_text(text: str) -> Optional[datetime]:
    """Return the first supported UTC time found in text using today's date."""
    match = UTC_TIME_PATTERN.search(text)

    if match is None:
        return None

    hour = int(match.group("hour"))
    minute_group = match.group("minute")
    minute = int(minute_group) if minute_group is not None else 0

    return datetime.now(tz=UTC_TIMEZONE).replace(
        hour=hour,
        minute=minute,
        second=0,
        microsecond=0,
    )


if __name__ == "__main__":
    test_messages = (
        "10:00 utc",
        "10:00utc",
        "10:00 UTC",
        "Текст 10:00 UTC текст",
        "10:00UTC",
        "10:00 текст utc",
        "10 UTC",
        "Текст 10:00 Utc текст",
        "Перша подія 10:00 UTC, друга подія 12:30 UTC"
    )

    for test_message in test_messages:
        parsed_datetime = parse_utc_time_from_text(test_message)
        print(
            "Message:",
            repr(test_message),
            "Parsed datetime:",
            parsed_datetime,
            "Object type:",
            type(parsed_datetime),
        )
