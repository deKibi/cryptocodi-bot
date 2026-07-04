# telegram_bot/state/message_reply_tracker.py

# Standard Libraries
from collections import OrderedDict
from typing import Final, Optional


# Related bot replies
MAX_TRACKED_REPLY_MESSAGE_IDS: Final[int] = 10_000
REPLY_MESSAGE_IDS_BOT_DATA_KEY: Final[str] = "reply_message_ids"

ReplyMessageKey = tuple[str, int, int]
ReplyMessageCache = OrderedDict[ReplyMessageKey, int]


def _get_reply_message_cache(
    bot_data: dict[str, object],
) -> ReplyMessageCache:
    existing_cache = bot_data.get(REPLY_MESSAGE_IDS_BOT_DATA_KEY)

    if isinstance(existing_cache, OrderedDict):
        return existing_cache

    reply_message_cache: ReplyMessageCache = OrderedDict()
    bot_data[REPLY_MESSAGE_IDS_BOT_DATA_KEY] = reply_message_cache
    return reply_message_cache


def get_related_reply_message_id(
    bot_data: dict[str, object],
    feature: str,
    chat_id: int,
    source_message_id: int,
) -> Optional[int]:
    """Return the bot reply associated with a source message."""
    reply_message_cache = _get_reply_message_cache(bot_data)
    key = (feature, chat_id, source_message_id)
    reply_message_id = reply_message_cache.get(key)

    if reply_message_id is not None:
        reply_message_cache.move_to_end(key)

    return reply_message_id


def remember_related_reply_message_id(
    bot_data: dict[str, object],
    feature: str,
    chat_id: int,
    source_message_id: int,
    reply_message_id: int,
) -> None:
    """Associate a bot reply with a source message and bound the cache."""
    reply_message_cache = _get_reply_message_cache(bot_data)
    key = (feature, chat_id, source_message_id)
    reply_message_cache[key] = reply_message_id
    reply_message_cache.move_to_end(key)

    while len(reply_message_cache) > MAX_TRACKED_REPLY_MESSAGE_IDS:
        reply_message_cache.popitem(last=False)
