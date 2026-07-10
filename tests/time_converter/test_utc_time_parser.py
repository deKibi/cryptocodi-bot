# tests/time_converter/test_utc_time_parser.py

# Third-party Libraries
import pytest

# Custom Modules
from time_converter.utc_time_parser import (
    parse_time_from_text,
    parse_times_from_text,
    parse_utc_time_from_text,
)


@pytest.mark.parametrize(
    ("text", "timezone_label", "hour", "minute"),
    [
        ("10:00 UTC", "UTC", 10, 0),
        ("10:00UTC", "UTC", 10, 0),
        ("10 UTC", "UTC", 10, 0),
        ("10:30 cet", "CET", 10, 30),
        ("10 CEST", "CEST", 10, 0),
        ("10:45kyiv", "KYIV", 10, 45),
    ],
)
def test_parse_named_timezones(
    text: str,
    timezone_label: str,
    hour: int,
    minute: int,
) -> None:
    parsed_time = parse_time_from_text(text)

    assert parsed_time is not None
    assert parsed_time.timezone_label == timezone_label
    assert parsed_time.source_datetime.hour == hour
    assert parsed_time.source_datetime.minute == minute


def test_parse_multiple_times_in_message_order() -> None:
    parsed_times = parse_times_from_text(
        "start 10:00 UTC, finish 12:00 GMT+3",
        limit=5,
    )

    assert [parsed_time.timezone_label for parsed_time in parsed_times] == [
        "UTC",
        "UTC+3",
    ]
    assert [parsed_time.source_datetime.hour for parsed_time in parsed_times] == [
        10,
        12,
    ]


def test_parse_times_respects_limit() -> None:
    parsed_times = parse_times_from_text(
        "10:00 UTC, 11:00 CET, 12:00 GMT+3",
        limit=2,
    )

    assert [parsed_time.timezone_label for parsed_time in parsed_times] == [
        "UTC",
        "CET",
    ]


def test_parse_utc_time_from_text_skips_non_utc_matches() -> None:
    parsed_datetime = parse_utc_time_from_text(
        "start 10:00 GMT+3, finish 12:00 UTC",
    )

    assert parsed_datetime is not None
    assert parsed_datetime.hour == 12
    assert parsed_datetime.minute == 0


@pytest.mark.parametrize(
    "text",
    [
        "abc10:00UTC",
        "10:00UTCabc",
        "-10:00 UTC",
        "10: 00 UTC",
    ],
)
def test_reject_partial_named_timezone_matches(text: str) -> None:
    assert parse_time_from_text(text) is None
