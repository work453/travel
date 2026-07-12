from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from .base import Notifier

logger = logging.getLogger(__name__)

GMAIL_SMTP_HOST = "smtp.gmail.com"
GMAIL_SMTP_PORT = 465


class EmailNotifier(Notifier):
    def __init__(self, gmail_address: str, gmail_app_password: str, to_address: str) -> None:
        self._gmail_address = gmail_address
        self._gmail_app_password = gmail_app_password
        self._to_address = to_address

    def send(self, subject: str, body: str) -> None:
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = f"Flight Deal Alerts <{self._gmail_address}>"
        message["To"] = self._to_address
        message.set_content(body)

        try:
            with smtplib.SMTP_SSL(GMAIL_SMTP_HOST, GMAIL_SMTP_PORT) as smtp:
                smtp.login(self._gmail_address, self._gmail_app_password)
                smtp.send_message(message)
            logger.info("Sent alert email to %s", self._to_address)
        except smtplib.SMTPException:
            logger.exception("Failed to send alert email to %s", self._to_address)
