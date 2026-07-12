from types import SimpleNamespace
from unittest.mock import patch

from src.flight_sources.google_flights_source import GoogleFlightsSource


def _flight(price):
    return SimpleNamespace(price=price)


def test_picks_cheapest_across_results():
    source = GoogleFlightsSource()
    results = [_flight(32000), _flight(28000), _flight(41000)]

    with patch("src.flight_sources.google_flights_source.get_flights", return_value=results), \
         patch("src.flight_sources.google_flights_source.time.sleep"):
        quote = source.get_cheapest_price("BOM", "DXB", "2026-08-11", "2026-08-18", "INR")

    assert quote is not None
    assert quote.price == 28000
    assert quote.source == "Google Flights"


def test_returns_none_when_no_results():
    source = GoogleFlightsSource()

    with patch("src.flight_sources.google_flights_source.get_flights", return_value=[]), \
         patch("src.flight_sources.google_flights_source.time.sleep"):
        quote = source.get_cheapest_price("BOM", "DXB", "2026-08-11", "2026-08-18", "INR")

    assert quote is None


def test_returns_none_on_scrape_failure():
    source = GoogleFlightsSource()

    def raise_error(*args, **kwargs):
        raise RuntimeError("scrape blocked")

    with patch("src.flight_sources.google_flights_source.get_flights", side_effect=raise_error), \
         patch("src.flight_sources.google_flights_source.time.sleep"):
        quote = source.get_cheapest_price("BOM", "DXB", "2026-08-11", "2026-08-18", "INR")

    assert quote is None
