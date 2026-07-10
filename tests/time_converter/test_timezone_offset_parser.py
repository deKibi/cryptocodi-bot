# tests/time_converter/test_timezone_offset_parser.py

# Third-party Libraries
import pytest

# Custom Modules
from time_converter.utc_time_parser import parse_time_from_text, parse_times_from_text


@pytest.mark.parametrize(
    ("text", "hour", "minute", "offset"),
    [
        ("10:00 GMT+3", 10, 0, 3),
        ("10:00 GMT +3", 10, 0, 3),
        ("10:00 GMT+ 3", 10, 0, 3),
        ("10:00 GMT + 3", 10, 0, 3),
        ("10:00GMT+3", 10, 0, 3),
        ("10:00GMT +3", 10, 0, 3),
        ("10:00 UTC+3", 10, 0, 3),
        ("10:00 UTC +3", 10, 0, 3),
        ("10:00 UTC+ 3", 10, 0, 3),
        ("10:00 UTC + 3", 10, 0, 3),
        ("10:00UTC+3", 10, 0, 3),
        ("10:00UTC +3", 10, 0, 3),
        ("10:00 UTC+3.", 10, 0, 3),
        ("10:00 UTC+3, старт", 10, 0, 3),
        ("10:00 UTC+3: старт", 10, 0, 3),
        ("10:00 UTC+3 : старт", 10, 0, 3),
        ("10:00 GMT+5.", 10, 0, 5),
        ("10:00 GMT+5, start", 10, 0, 5),
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
        "10:00 GMT+5:30",
        "10:00 GMT+5 :30",
        "10:00 GMT+5 : 30",
        "10:00 GMT+5.5",
        "10:00 GMT+5,5",
        "10:00GMT+5:45",
        "10:00 GMT++3",
        "abc10:00GMT+3",
        "10:00GMT+3abc",
        "10:00   GMT+3",
        "10:00 GMT3",
        "10:00 GMT 3",
        "10:00 GMT plus 3",
        "10:00 UTC 3",
        "10:00 UTC+3:30",
        "10:00 UTC+3 :30",
        "10:00 UTC+3.5",
        "10:00 UTC+3 .5",
        "10:00 UTC+3,5",
        "10:00 UTC+3 ,5",
        "10:00 UTC + 3:30",
        "10:00 UTC + 3 :30",
        "10:00 UTC + 3.5",
        "10:00 UTC + 3 .5",
        "10:00 UTC-3.5",
        "10:00 +3",
        "10:00+3",
        "-1:00 GMT+3",
        "1:5 GMT+3",
        "100:00 GMT+3",
        "10:00 GMT--3",
        "10:00 GMT+-3",
        "10:00 GMT",
    ],
)
def test_reject_invalid_timezone_offsets(text: str) -> None:
    assert parse_time_from_text(text) is None


def test_fractional_offset_is_not_partially_parsed() -> None:
    assert parse_time_from_text("10:00 GMT+5:30") is None
    assert parse_time_from_text("10:00 GMT+5 :30") is None
    assert parse_time_from_text("10:00 GMT+5 : 30") is None
    assert parse_time_from_text("10:00 GMT+5.5") is None
    assert parse_time_from_text("10:00 GMT+5,5") is None
    assert parse_time_from_text("10:00 UTC+3:30") is None
    assert parse_time_from_text("10:00 UTC+3 :30") is None
    assert parse_time_from_text("10:00 UTC+3.5") is None
    assert parse_time_from_text("10:00 UTC+3 .5") is None
    assert parse_time_from_text("10:00 UTC+3,5") is None
    assert parse_time_from_text("10:00 UTC+3 ,5") is None
    assert parse_time_from_text("10:00 UTC + 3:30") is None
    assert parse_time_from_text("10:00 UTC + 3 :30") is None
    assert parse_time_from_text("10:00 UTC + 3.5") is None
    assert parse_time_from_text("10:00 UTC + 3 .5") is None
    assert parse_time_from_text("10:00 UTC-3.5") is None


def test_spaced_utc_offset_is_not_parsed_as_plain_utc() -> None:
    parsed_time = parse_time_from_text("10:00 UTC +3")

    assert parsed_time is not None
    assert parsed_time.timezone_label == "UTC+3"


@pytest.mark.parametrize(
    ("text", "expected_labels", "expected_hours"),
    [
        ("10:00 UTC+3, 12:00 CET", ["UTC+3", "CET"], [10, 12]),
        ("10:00 GMT+3. 12:00 UTC", ["UTC+3", "UTC"], [10, 12]),
    ],
)
def test_offset_punctuation_before_next_time_is_not_fractional_suffix(
    text: str,
    expected_labels: list[str],
    expected_hours: list[int],
) -> None:
    parsed_times = parse_times_from_text(text, limit=5)

    assert [parsed_time.timezone_label for parsed_time in parsed_times] == (
        expected_labels
    )
    assert [parsed_time.source_datetime.hour for parsed_time in parsed_times] == (
        expected_hours
    )
