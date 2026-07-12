"""Entry point: run one price-check pass and send alerts for any deals."""

from __future__ import annotations

import logging

from .alert_engine import find_all_deals, format_alert_email
from .amadeus_client import build_client
from .config import load_config
from .notifiers import EmailNotifier, Notifier, TelegramNotifier
from .price_store import DEFAULT_DB_PATH


def build_notifiers(config) -> list[Notifier]:
    notifiers: list[Notifier] = []
    if config.email_enabled:
        notifiers.append(
            EmailNotifier(
                gmail_address=config.secrets.gmail_address,
                gmail_app_password=config.secrets.gmail_app_password,
                to_address=config.secrets.alert_email_to,
            )
        )
    if config.telegram_enabled:
        notifiers.append(TelegramNotifier())
    return notifiers


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    config = load_config()

    client = build_client(config.secrets.amadeus_api_key, config.secrets.amadeus_api_secret)
    notifiers = build_notifiers(config)

    deals = find_all_deals(
        client,
        DEFAULT_DB_PATH,
        config.origins,
        config.destinations,
        config.search,
        config.alert,
    )

    if not deals:
        logging.info("No deals met the alert threshold this run.")
        return

    subject, body = format_alert_email(deals)
    for notifier in notifiers:
        notifier.send(subject, body)


if __name__ == "__main__":
    main()
