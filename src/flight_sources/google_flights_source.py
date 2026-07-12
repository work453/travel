"""Google Flights source, via SerpApi's google_flights search engine
(https://serpapi.com/google-flights-api). SerpApi does the scraping; we
just call their JSON API with an API key, which keeps this ToS-safe and
reasonably stable compared to scraping Google directly.
"""

from __future__ import annotations

import logging

import requests

from .base import FlightSource, PriceQuote

logger = logging.getLogger(__name__)

SERPAPI_URL = "https://serpapi.com/search.json"
REQUEST_TIMEOUT_SECONDS = 20


class GoogleFlightsSource(FlightSource):
    name = "Google Flights"

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def get_cheapest_price(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: str,
        currency: str,
    ) -> PriceQuote | None:
        params = {
            "engine": "google_flights",
            "type": "1",  # round trip
            "departure_id": origin,
            "arrival_id": destination,
            "outbound_date": departure_date,
            "return_date": return_date,
            "currency": currency,
            "hl": "en",
            "api_key": self._api_key,
        }

        try:
            response = requests.get(SERPAPI_URL, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException:
            logger.warning(
                "SerpApi Google Flights request failed for %s->%s on %s",
                origin,
                destination,
                departure_date,
                exc_info=True,
            )
            return None

        if data.get("error"):
            logger.warning(
                "SerpApi Google Flights error for %s->%s: %s", origin, destination, data["error"]
            )
            return None

        candidates = (data.get("best_flights") or []) + (data.get("other_flights") or [])
        priced = [c for c in candidates if isinstance(c.get("price"), (int, float))]
        if not priced:
            return None

        cheapest = min(priced, key=lambda c: c["price"])
        return PriceQuote(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            price=float(cheapest["price"]),
            currency=currency,
            source=self.name,
        )
