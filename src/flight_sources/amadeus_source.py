"""Amadeus Flight Offers Search source.

Uses the official `amadeus` SDK, which defaults to Amadeus's free "test"
environment. Test environment data covers a limited (but broad enough for
major routes) subset of real fares — see README for notes on moving to
the production environment later.
"""

from __future__ import annotations

import logging

from amadeus import Client, ResponseError

from .base import FlightSource, PriceQuote

logger = logging.getLogger(__name__)


class AmadeusSource(FlightSource):
    name = "Amadeus"

    def __init__(self, api_key: str, api_secret: str) -> None:
        self._client = Client(client_id=api_key, client_secret=api_secret)

    def get_cheapest_price(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: str,
        currency: str,
    ) -> PriceQuote | None:
        try:
            response = self._client.shopping.flight_offers_search.get(
                originLocationCode=origin,
                destinationLocationCode=destination,
                departureDate=departure_date,
                returnDate=return_date,
                adults=1,
                currencyCode=currency,
                max=5,
            )
        except ResponseError as exc:
            logger.warning(
                "Amadeus search failed for %s->%s on %s: %s",
                origin,
                destination,
                departure_date,
                exc,
            )
            return None

        offers = response.data
        if not offers:
            return None

        cheapest = min(offers, key=lambda offer: float(offer["price"]["grandTotal"]))
        return PriceQuote(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            price=float(cheapest["price"]["grandTotal"]),
            currency=cheapest["price"]["currency"],
            source=self.name,
        )
