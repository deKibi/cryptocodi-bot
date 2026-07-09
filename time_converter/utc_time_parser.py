# time_converter/utc_time_parser.py

# Standard Libraries
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Final, Optional

# Custom Modules
from time_converter.time_utils import TIMEZONES_BY_LABEL


# Time parsing
TIME_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?<![\w:.])(?P<hour>(?:[01]?\d|2[0-3]))"
    r"(?::(?P<minute>[0-5]\d))? ?(?P<timezone>UTC|CEST|CET|KYIV)\b",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True)
class ParsedTime:
    """Represent a parsed time with its source timezone."""

    source_datetime: datetime
    timezone_label: str


def _parse_time_match(match: re.Match[str]) -> ParsedTime:
    hour = int(match.group("hour"))
    minute_group = match.group("minute")
    minute = int(minute_group) if minute_group is not None else 0
    timezone_label = match.group("timezone").upper()
    timezone = TIMEZONES_BY_LABEL[timezone_label]

    return ParsedTime(
        source_datetime=datetime.now(tz=timezone).replace(
            hour=hour,
            minute=minute,
            second=0,
            microsecond=0,
        ),
        timezone_label=timezone_label,
    )


def parse_time_from_text(text: str) -> Optional[ParsedTime]:
    """Return the first supported timezone time found in text."""
    parsed_times = parse_times_from_text(text, limit=1)

    if not parsed_times:
        return None

    return parsed_times[0]


def parse_times_from_text(text: str, limit: int) -> list[ParsedTime]:
    """Return supported timezone times found in text in message order."""
    if limit <= 0:
        return []

    parsed_times: list[ParsedTime] = []

    for match in TIME_PATTERN.finditer(text):
        parsed_times.append(_parse_time_match(match))

        if len(parsed_times) == limit:
            break

    return parsed_times


def parse_utc_time_from_text(text: str) -> Optional[datetime]:
    """Return the first supported UTC time found in text using today's date."""
    for match in TIME_PATTERN.finditer(text):
        parsed_time = _parse_time_match(match)

        if parsed_time.timezone_label == "UTC":
            return parsed_time.source_datetime

    return None


if __name__ == "__main__":
    test_messages = (
        "10:00 utc",
        "10:00utc",
        "10:00 UTC",
        "Текст 10:00 UTC текст",
        "10:00UTC",
        "10:00 текст utc",
        "10 UTC",
        "10 CET",
        "10 CEST",
        "10:30 cet",
        "10:30 cest",
        "10 KYIV",
        "10:45kyiv",
        "Старт 10:00 UTC, фініш 12:00 CET",
        "Текст 10:00 Utc текст",
        "Перша подія 10:00 UTC, друга подія 12:30 UTC"
    )

    for test_message in test_messages:
        parsed_datetime = parse_times_from_text(test_message, limit=5)
        print(
            "Message:",
            repr(test_message),
            "Parsed datetime:",
            parsed_datetime,
            "Object type:",
            type(parsed_datetime),
        )
