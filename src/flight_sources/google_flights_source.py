"""Google Flights source — scrapes Google Flights directly via the
`fast-flights` library, no API key required.

Google has no official public Flights API, so this parses the same data
Google Flights' web UI loads. That makes it free but unofficial: it can
break if Google changes their page internals, and cloud/datacenter IPs
(including GitHub Actions runners) are more likely than residential IPs
to get rate-limited or served a CAPTCHA. Every call is wrapped so a
failure here just means this source contributes no quote for that
route/date — Amadeus (or a future source) can still cover it.
"""

from __future__ import annotations

import logging
import time

from fast_flights import FlightQuery, Passengers, create_filter, get_flights

from .base import FlightSource, PriceQuote

logger = logging.getLogger(__name__)

# Small pause before each request so a run's ~50 lookups don't hammer
# Google in a tight loop, which is the fastest way to get rate-limited.
REQUEST_DELAY_SECONDS = 1.0


class GoogleFlightsSource(FlightSource):
    name = "Google Flights"

    def get_cheapest_price(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: str,
        currency: str,
    ) -> PriceQuote | None:
        time.sleep(REQUEST_DELAY_SECONDS)

        try:
            query = create_filter(
                flights=[
                    FlightQuery(date=departure_date, from_airport=origin, to_airport=destination),
                    FlightQuery(date=return_date, from_airport=destination, to_airport=origin),
                ],
                trip="round-trip",
                seat="economy",
                passengers=Passengers(adults=1),
                currency=currency,
            )
            results = get_flights(query)
        except Exception:
            logger.warning(
                "Google Flights scrape failed for %s->%s on %s",
                origin,
                destination,
                departure_date,
                exc_info=True,
            )
            return None

        if not results:
            return None

        cheapest = min(results, key=lambda flight: flight.price)
        return PriceQuote(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            price=float(cheapest.price),
            currency=currency,
            source=self.name,
        )
