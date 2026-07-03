# telegram_bot/state/message_signature_tracker.py

# Standard Libraries
from collections import OrderedDict
from collections.abc import Hashable
from typing import Final


# Message signatures
MAX_TRACKED_MESSAGE_SIGNATURES: Final[int] = 10_000
MESSAGE_SIGNATURES_BOT_DATA_KEY: Final[str] = "message_signatures"

MessageSignatureKey = tuple[str, int, int]
MessageSignatureCache = OrderedDict[MessageSignatureKey, Hashable]


def _get_signature_cache(
    bot_data: dict[str, object],
) -> MessageSignatureCache:
    existing_cache = bot_data.get(MESSAGE_SIGNATURES_BOT_DATA_KEY)

    if isinstance(existing_cache, OrderedDict):
        return existing_cache

    signature_cache: MessageSignatureCache = OrderedDict()
    bot_data[MESSAGE_SIGNATURES_BOT_DATA_KEY] = signature_cache
    return signature_cache


def is_message_signature_unchanged(
    bot_data: dict[str, object],
    feature: str,
    chat_id: int,
    message_id: int,
    signature: Hashable,
) -> bool:
    """Return whether a message already has the same feature signature."""
    signature_cache = _get_signature_cache(bot_data)
    key = (feature, chat_id, message_id)

    if signature_cache.get(key) != signature:
        return False

    signature_cache.move_to_end(key)
    return True


def remember_message_signature(
    bot_data: dict[str, object],
    feature: str,
    chat_id: int,
    message_id: int,
    signature: Hashable,
) -> None:
    """Store a processed signature and evict the oldest entry if needed."""
    signature_cache = _get_signature_cache(bot_data)
    key = (feature, chat_id, message_id)
    signature_cache[key] = signature
    signature_cache.move_to_end(key)

    while len(signature_cache) > MAX_TRACKED_MESSAGE_SIGNATURES:
        signature_cache.popitem(last=False)


def forget_message_signature(
    bot_data: dict[str, object],
    feature: str,
    chat_id: int,
    message_id: int,
) -> None:
    """Forget a signature when an edit removes all matching values."""
    signature_cache = _get_signature_cache(bot_data)
    signature_cache.pop((feature, chat_id, message_id), None)
