# tests/crypto_converter/test_coin_ticker_resolver.py

# Custom Modules
from crypto_converter.coin_ticker_resolver import resolve_coin


def test_resolve_known_crypto_ticker_without_api() -> None:
    resolved_coin = resolve_coin("btc")

    assert resolved_coin is not None
    assert resolved_coin.coin_id == "bitcoin"
    assert resolved_coin.ticker == "BTC"
    assert resolved_coin.name == "Bitcoin"


def test_resolve_zloty_alias_without_api() -> None:
    resolved_coin = resolve_coin("zl")

    assert resolved_coin is not None
    assert resolved_coin.coin_id == "tether"
    assert resolved_coin.ticker == "PLN"
    assert resolved_coin.name == "Zloty"


def test_resolve_ruble_without_api() -> None:
    resolved_coin = resolve_coin("rub")

    assert resolved_coin is not None
    assert resolved_coin.coin_id == "tether"
    assert resolved_coin.ticker == "RUB"
    assert resolved_coin.name == "Russian Ruble"


def test_block_utc_ticker_without_api() -> None:
    assert resolve_coin("utc") is None
