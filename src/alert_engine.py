"""Core logic: sample dates for each route, fetch prices, decide alerts."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from .config import AlertConfig, Place, SearchConfig
from .flight_sources import FlightSource, PriceQuote
from .price_store import record_price, get_route_stats

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Deal:
    origin: Place
    destination: Place
    quote: PriceQuote
    rolling_average: float
    discount_pct: float


def sample_departure_dates(search: SearchConfig, today: date | None = None) -> list[date]:
    today = today or date.today()
    start = today + timedelta(days=search.window_start_days)
    end = today + timedelta(days=search.window_end_days)

    count = max(search.sample_dates, 1)
    if count == 1:
        return [start]

    span = (end - start).days
    step = span / (count - 1)
    return [start + timedelta(days=round(i * step)) for i in range(count)]


def find_cheapest_for_route(
    sources: list[FlightSource],
    origin: Place,
    destination: Place,
    search: SearchConfig,
) -> PriceQuote | None:
    quotes: list[PriceQuote] = []
    for departure in sample_departure_dates(search):
        return_date = departure + timedelta(days=search.trip_length_days)
        for source in sources:
            quote = source.get_cheapest_price(
                origin.code,
                destination.code,
                departure.isoformat(),
                return_date.isoformat(),
                search.currency,
            )
            if quote:
                quotes.append(quote)

    if not quotes:
        logger.info("No offers found for %s->%s", origin.code, destination.code)
        return None

    return min(quotes, key=lambda q: q.price)


def check_route(
    sources: list[FlightSource],
    db_path: Path,
    origin: Place,
    destination: Place,
    search: SearchConfig,
    alert: AlertConfig,
) -> Deal | None:
    best = find_cheapest_for_route(sources, origin, destination, search)
    if best is None:
        return None

    stats = get_route_stats(db_path, origin.code, destination.code, alert.rolling_window_days)

    # Record *after* computing stats so today's price never inflates its own baseline.
    record_price(db_path, origin.code, destination.code, best.price, best.currency)

    if stats.sample_count < alert.min_history_points or stats.rolling_average is None:
        logger.info(
            "%s->%s: %d/%d history points, not enough to judge yet",
            origin.code,
            destination.code,
            stats.sample_count,
            alert.min_history_points,
        )
        return None

    discount_pct = (1 - best.price / stats.rolling_average) * 100
    logger.info(
        "%s->%s: price %.0f %s vs avg %.0f (%.1f%% cheaper)",
        origin.code,
        destination.code,
        best.price,
        best.currency,
        stats.rolling_average,
        discount_pct,
    )

    if discount_pct >= alert.discount_threshold_pct:
        return Deal(
            origin=origin,
            destination=destination,
            quote=best,
            rolling_average=stats.rolling_average,
            discount_pct=discount_pct,
        )
    return None


def find_all_deals(
    sources: list[FlightSource],
    db_path: Path,
    origins: list[Place],
    destinations: list[Place],
    search: SearchConfig,
    alert: AlertConfig,
) -> list[Deal]:
    deals: list[Deal] = []
    for origin in origins:
        for destination in destinations:
            deal = check_route(sources, db_path, origin, destination, search, alert)
            if deal:
                deals.append(deal)
    return deals


def format_alert_email(deals: list[Deal]) -> tuple[str, str]:
    subject = f"✈️ {len(deals)} flight deal(s) found"
    lines = ["Found the following deals (at least the configured discount vs the 30-day average):", ""]
    for deal in sorted(deals, key=lambda d: -d.discount_pct):
        lines.append(
            f"- {deal.origin.name} ({deal.origin.code}) -> {deal.destination.name} ({deal.destination.code}): "
            f"{deal.quote.price:.0f} {deal.quote.currency} on {deal.quote.departure_date} "
            f"(return {deal.quote.return_date}), {deal.discount_pct:.0f}% below the "
            f"{deal.rolling_average:.0f} {deal.quote.currency} average [via {deal.quote.source}]"
        )
    return subject, "\n".join(lines)
