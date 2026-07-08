# telegram_bot/services/bot_invitation.py

# Standard Libraries
import re
from typing import Final, Optional, Sequence

# Third-party Libraries
from telegram.helpers import create_deep_linked_url


# Bot invitation deep links
BOT_INVITATION_PAYLOAD_PREFIX: Final[str] = "invite"
BOT_INVITATION_PAYLOAD_PATTERN: Final[re.Pattern[str]] = re.compile(
    rf"{BOT_INVITATION_PAYLOAD_PREFIX}_(?P<inviter_user_id>[1-9][0-9]*)"
)


def build_bot_invitation_url(
    bot_username: str,
    inviter_user_id: int,
) -> str:
    """Build a Telegram group-selection link for one inviter."""
    payload = f"{BOT_INVITATION_PAYLOAD_PREFIX}_{inviter_user_id}"
    return create_deep_linked_url(
        bot_username,
        payload=payload,
        group=True,
    )


def parse_bot_inviter_user_id(arguments: Sequence[str]) -> Optional[int]:
    """Return a valid inviter ID from one start-command argument."""
    if len(arguments) != 1:
        return None

    match = BOT_INVITATION_PAYLOAD_PATTERN.fullmatch(arguments[0])

    if match is None:
        return None

    return int(match.group("inviter_user_id"))
