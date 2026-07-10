# tests/time_converter/test_time_formatter.py

# Custom Modules
from telegram_bot.handlers.time_message_handler import format_time_response
from time_converter.utc_time_parser import parse_times_from_text


def test_format_timezone_offset_response() -> None:
    parsed_times = parse_times_from_text("10:00 GMT+3", limit=5)

    response_text = format_time_response(parsed_times, language="en")

    assert response_text.startswith("<code>")
    assert "10:00 GMT+3 (10:00) UTC+3" in response_text
    assert "KYIV" in response_text
    assert "CET" in response_text
    assert "UTC" in response_text
    assert "07:00 UTC" in response_text
    assert (
        "<b>GMT+3</b> — <i>UTC+3</i> (UTC+03:00)"
        in response_text
    )


def test_format_multiple_time_conversions() -> None:
    parsed_times = parse_times_from_text(
        "start 10:00 UTC, finish 12:00 GMT+3",
        limit=5,
    )

    response_text = format_time_response(parsed_times, language="en")

    assert response_text.count("┬─>") == 2
    assert "10:00 UTC" in response_text
    assert "12:00 GMT+3 (12:00) UTC+3" in response_text
    assert "<b>UTC</b> — <i>UTC</i> (UTC+00:00)" in response_text
    assert (
        "<b>GMT+3</b> — <i>UTC+3</i> (UTC+03:00)"
        in response_text
    )
