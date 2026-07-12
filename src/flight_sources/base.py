"""Common interface so alert_engine doesn't care which flight-data provider
found a given price."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class PriceQuote:
    origin: str
    destination: str
    departure_date: str
    return_date: str
    price: float
    currency: str
    source: str


class FlightSource(ABC):
    name: str

    @abstractmethod
    def get_cheapest_price(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: str,
        currency: str,
    ) -> PriceQuote | None:
        """Returns the cheapest offer found for a route+dates, or None if
        none was found (or the request failed)."""
