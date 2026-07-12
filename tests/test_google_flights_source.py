from unittest.mock import Mock, patch

from src.flight_sources.google_flights_source import GoogleFlightsSource


def _response(json_body, status_ok=True):
    response = Mock()
    response.json.return_value = json_body
    response.raise_for_status = Mock()
    return response


def test_picks_cheapest_across_best_and_other_flights():
    source = GoogleFlightsSource(api_key="test-key")
    body = {
        "best_flights": [{"price": 32000}],
        "other_flights": [{"price": 28000}, {"price": 41000}],
    }

    with patch("src.flight_sources.google_flights_source.requests.get", return_value=_response(body)):
        quote = source.get_cheapest_price("BOM", "DXB", "2026-08-11", "2026-08-18", "INR")

    assert quote is not None
    assert quote.price == 28000
    assert quote.source == "Google Flights"


def test_returns_none_on_api_error():
    source = GoogleFlightsSource(api_key="test-key")
    body = {"error": "Invalid API key"}

    with patch("src.flight_sources.google_flights_source.requests.get", return_value=_response(body)):
        quote = source.get_cheapest_price("BOM", "DXB", "2026-08-11", "2026-08-18", "INR")

    assert quote is None


def test_returns_none_when_no_priced_flights():
    source = GoogleFlightsSource(api_key="test-key")
    body = {"best_flights": [], "other_flights": []}

    with patch("src.flight_sources.google_flights_source.requests.get", return_value=_response(body)):
        quote = source.get_cheapest_price("BOM", "DXB", "2026-08-11", "2026-08-18", "INR")

    assert quote is None
