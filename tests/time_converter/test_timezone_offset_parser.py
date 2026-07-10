# tests/time_converter/test_timezone_offset_parser.py

# Third-party Libraries
import pytest

# Custom Modules
from time_converter.utc_time_parser import (
    parse_time_from_text,
    parse_times_from_text,
)


@pytest.mark.parametrize(
    ("text", "hour", "minute", "offset"),
    [
        ("10 GMT+3", 10, 0, 3),
        ("10GMT+3", 10, 0, 3),
        ("10:00 GMT+3", 10, 0, 3),
        ("10:00GMT+3", 10, 0, 3),
        ("10 UTC+3", 10, 0, 3),
        ("10UTC+3", 10, 0, 3),
        ("10:00 UTC+3", 10, 0, 3),
        ("10:00UTC+3", 10, 0, 3),
        ("1:05 utc-5", 1, 5, -5),
        ("00:00 GMT+14", 0, 0, 14),
        ("23:59 GMT-12", 23, 59, -12),
    ],
)
def test_parse_valid_timezone_offsets(
    text: str,
    hour: int,
    minute: int,
    offset: int,
) -> None:
    parsed_time = parse_time_from_text(text)

    assert parsed_time is not None
    assert parsed_time.source_datetime.hour == hour
    assert parsed_time.source_datetime.minute == minute
    assert parsed_time.timezone_label == f"UTC{offset:+d}"
    assert parsed_time.source_datetime.utcoffset() is not None
    assert (
        int(parsed_time.source_datetime.utcoffset().total_seconds() // 3600)
        == offset
    )


@pytest.mark.parametrize(
    "text",
    [
        "24:00 GMT+3",
        "10:60 GMT+3",
        "10:00 GMT+15",
        "10:00 GMT-13",
        "10:00GMT+5:45",
        "abc10:00GMT+3",
        "10:00GMT+3abc",
        "10:00   GMT+3",
        "10:00 GMT3",
        "10:00 GMT 3",
        "10:00 +3",
        "10:00+3",
        "-1:00 GMT+3",
        "1:5 GMT+3",
        "100:00 GMT+3",
        "10:00 GMT",
    ],
)
def test_reject_invalid_timezone_offsets(text: str) -> None:
    assert parse_time_from_text(text) is None


def test_parse_multiple_offset_and_named_times_in_message_order() -> None:
    parsed_times = parse_times_from_text(
        "10:00 UTC+3, 12:00 CET",
        limit=5,
    )

    assert [parsed_time.timezone_label for parsed_time in parsed_times] == [
        "UTC+3",
        "CET",
    ]
    assert [parsed_time.source_datetime.hour for parsed_time in parsed_times] == [
        10,
        12,
    ]


def test_parse_gmt_offset_preserves_display_timezone_label() -> None:
    parsed_time = parse_time_from_text("10:00 gmt+3")

    assert parsed_time is not None
    assert parsed_time.timezone_label == "UTC+3"
    assert parsed_time.display_timezone_label == "GMT+3"


def test_parse_utc_offset_preserves_display_timezone_label() -> None:
    parsed_time = parse_time_from_text("10:00 utc+3")

    assert parsed_time is not None
    assert parsed_time.timezone_label == "UTC+3"
    assert parsed_time.display_timezone_label == "UTC+3"


@pytest.mark.parametrize(
    "text",
    [
        "2+2",
        "2*2 BNB",
        "1 BTC",
        "BTC + ETH",
    ],
)
def test_time_parser_ignores_calculator_and_crypto_text(text: str) -> None:
    assert parse_time_from_text(text) is None
