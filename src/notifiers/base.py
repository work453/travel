"""Common interface so alert_engine doesn't care which channels are wired up."""

from __future__ import annotations

from abc import ABC, abstractmethod


class Notifier(ABC):
    @abstractmethod
    def send(self, subject: str, body: str) -> None:
        """Deliver an alert. Implementations should log and return rather
        than raise, so one broken channel doesn't stop the others."""
