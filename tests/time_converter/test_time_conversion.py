# tests/time_converter/test_time_conversion.py

# Third-party Libraries
import pytest

# Custom Modules
from time_converter.time_utils import convert_to_timezone
from time_converter.utc_time_parser import parse_time_from_text


@pytest.mark.parametrize(
    ("text", "expected_utc"),
    [
        ("00:30 GMT+5", "19:30"),
        ("23:30 GMT-5", "04:30"),
        ("00:00 GMT+14", "10:00"),
        ("23:59 GMT-12", "11:59"),
    ],
)
def test_conversion_across_day_boundary(
    text: str,
    expected_utc: str,
) -> None:
    parsed_time = parse_time_from_text(text)

    assert parsed_time is not None

    utc_datetime = convert_to_timezone(parsed_time.source_datetime, "UTC")

    assert f"{utc_datetime:%H:%M}" == expected_utc


@pytest.mark.parametrize(
    ("text", "expected_utc"),
    [
        ("10:00 GMT+3", "07:00"),
        ("10:00 UTC+3", "07:00"),
        ("10:00 GMT-5", "15:00"),
        ("10:00 UTC-5", "15:00"),
    ],
)
def test_offset_conversion_to_utc(
    text: str,
    expected_utc: str,
) -> None:
    parsed_time = parse_time_from_text(text)

    assert parsed_time is not None

    utc_datetime = convert_to_timezone(parsed_time.source_datetime, "UTC")

    assert f"{utc_datetime:%H:%M}" == expected_utc
