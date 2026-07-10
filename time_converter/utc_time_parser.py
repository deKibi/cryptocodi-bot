# time_converter/utc_time_parser.py

# Standard Libraries
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Final, Optional

# Custom Modules
from time_converter.time_utils import TIMEZONES_BY_LABEL


# Time parsing
NAMED_TIME_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?<![\w:.\-+])(?P<hour>(?:[01]?\d|2[0-3]))"
    r"(?::(?P<minute>[0-5]\d))? ?(?P<timezone>UTC|CEST|CET|KYIV)\b"
    r"(?![+-])",
    flags=re.IGNORECASE,
)
OFFSET_TIME_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?<![\w:.\-+])(?P<hour>(?:[01]?\d|2[0-3]))"
    r"(?::(?P<minute>[0-5]\d))? ?"
    r"(?P<timezone>(?:UTC|GMT)(?P<sign>[+-])(?P<offset>0?\d|1[0-4]))"
    r"(?![\w:])",
    flags=re.IGNORECASE,
)
MIN_UTC_OFFSET_HOURS: Final[int] = -12
MAX_UTC_OFFSET_HOURS: Final[int] = 14


@dataclass(frozen=True)
class ParsedTime:
    """Represent a parsed time with its source timezone."""

    source_datetime: datetime
    timezone_label: str
    display_timezone_label: Optional[str] = None


def _parse_named_time_match(match: re.Match[str]) -> Optional[ParsedTime]:
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


def _parse_offset_time_match(match: re.Match[str]) -> Optional[ParsedTime]:
    hour = int(match.group("hour"))
    minute_group = match.group("minute")
    minute = int(minute_group) if minute_group is not None else 0
    sign = match.group("sign")
    offset_hours = int(match.group("offset"))

    if sign == "-":
        offset_hours = -offset_hours

    if not MIN_UTC_OFFSET_HOURS <= offset_hours <= MAX_UTC_OFFSET_HOURS:
        return None

    offset_timezone = timezone(timedelta(hours=offset_hours))
    label_sign = "+" if offset_hours >= 0 else "-"
    timezone_label = f"UTC{label_sign}{abs(offset_hours)}"
    input_timezone_prefix = match.group("timezone")[:3].upper()
    display_timezone_label = (
        f"{input_timezone_prefix}{label_sign}{abs(offset_hours)}"
    )

    return ParsedTime(
        source_datetime=datetime.now(tz=offset_timezone).replace(
            hour=hour,
            minute=minute,
            second=0,
            microsecond=0,
        ),
        timezone_label=timezone_label,
        display_timezone_label=display_timezone_label,
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
    matches = sorted(
        (
            *(
                (
                    named_time_match.start(),
                    _parse_named_time_match(named_time_match),
                )
                for named_time_match in NAMED_TIME_PATTERN.finditer(text)
            ),
            *(
                (
                    offset_time_match.start(),
                    _parse_offset_time_match(offset_time_match),
                )
                for offset_time_match in OFFSET_TIME_PATTERN.finditer(text)
            ),
        ),
        key=lambda match_data: match_data[0],
    )

    for _match_start, parsed_time in matches:
        if parsed_time is None:
            continue

        parsed_times.append(parsed_time)

        if len(parsed_times) == limit:
            break

    return parsed_times


def parse_utc_time_from_text(text: str) -> Optional[datetime]:
    """Return the first supported UTC time found in text using today's date."""
    for parsed_time in parse_times_from_text(text, limit=len(text)):
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
        "10:00 GMT+3",
        "10:00GMT+3",
        "10:00 GMT-5",
        "10:00GMT-5",
        "01:00 GMT+03",
        "23:59 GMT+14",
        "00:00 GMT-12",
        "10:00 UTC+3",
        "10:00UTC+3",
        "10:00 GMT+5:30",
        "10:00   GMT+3",
        "10:00 GMT + 3",
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
