"""Placeholder Telegram channel.

Not wired up yet — send() just logs. To enable later: create a bot via
@BotFather, grab its token + your chat id, then implement send() as a POST
to https://api.telegram.org/bot<token>/sendMessage, and flip
notifications.telegram.enabled to true in config.yaml.
"""

from __future__ import annotations

import logging

from .base import Notifier

logger = logging.getLogger(__name__)


class TelegramNotifier(Notifier):
    def __init__(self, bot_token: str | None = None, chat_id: str | None = None) -> None:
        self._bot_token = bot_token
        self._chat_id = chat_id

    def send(self, subject: str, body: str) -> None:
        logger.info(
            "Telegram notifier not implemented yet; skipping alert: %s", subject
        )
