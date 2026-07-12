from datetime import date, datetime, timedelta, timezone

import src.alert_engine as alert_engine
from src.amadeus_client import PriceQuote
from src.config import AlertConfig, Place, SearchConfig
from src.price_store import record_price

ORIGIN = Place(code="BOM", name="Mumbai")
DESTINATION = Place(code="DXB", name="Dubai")


def test_sample_departure_dates_spans_window():
    search = SearchConfig(
        window_start_days=30, window_end_days=90, sample_dates=3, trip_length_days=7, currency="INR"
    )
    today = date(2026, 7, 12)

    dates = alert_engine.sample_departure_dates(search, today=today)

    assert len(dates) == 3
    assert dates[0] == today + timedelta(days=30)
    assert dates[-1] == today + timedelta(days=90)


def _seed_history(db_path, price=20000, count=3):
    now = datetime.now(timezone.utc)
    for i in range(count):
        record_price(db_path, ORIGIN.code, DESTINATION.code, price, "INR", checked_at=now - timedelta(days=(i + 1) * 5))


def _search_config():
    return SearchConfig(window_start_days=30, window_end_days=90, sample_dates=1, trip_length_days=7, currency="INR")


def _fake_quote(price):
    def fake_get_cheapest_price(client, origin, destination, departure_date, return_date, currency):
        return PriceQuote(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            price=price,
            currency=currency,
        )

    return fake_get_cheapest_price


def test_check_route_triggers_deal_when_price_drops_enough(tmp_path, monkeypatch):
    db_path = tmp_path / "prices.sqlite3"
    _seed_history(db_path, price=20000, count=3)
    monkeypatch.setattr(alert_engine, "get_cheapest_price", _fake_quote(9000))

    alert = AlertConfig(discount_threshold_pct=50, rolling_window_days=30, min_history_points=3)
    deal = alert_engine.check_route(None, db_path, ORIGIN, DESTINATION, _search_config(), alert)

    assert deal is not None
    assert deal.discount_pct >= 50


def test_check_route_skips_when_discount_too_small(tmp_path, monkeypatch):
    db_path = tmp_path / "prices.sqlite3"
    _seed_history(db_path, price=20000, count=3)
    monkeypatch.setattr(alert_engine, "get_cheapest_price", _fake_quote(15000))

    alert = AlertConfig(discount_threshold_pct=50, rolling_window_days=30, min_history_points=3)
    deal = alert_engine.check_route(None, db_path, ORIGIN, DESTINATION, _search_config(), alert)

    assert deal is None


def test_check_route_skips_when_not_enough_history(tmp_path, monkeypatch):
    db_path = tmp_path / "prices.sqlite3"
    monkeypatch.setattr(alert_engine, "get_cheapest_price", _fake_quote(1000))

    alert = AlertConfig(discount_threshold_pct=50, rolling_window_days=30, min_history_points=3)
    deal = alert_engine.check_route(None, db_path, ORIGIN, DESTINATION, _search_config(), alert)

    assert deal is None


def test_format_alert_email_lists_all_deals(tmp_path, monkeypatch):
    db_path = tmp_path / "prices.sqlite3"
    _seed_history(db_path, price=20000, count=3)
    monkeypatch.setattr(alert_engine, "get_cheapest_price", _fake_quote(5000))

    alert = AlertConfig(discount_threshold_pct=50, rolling_window_days=30, min_history_points=3)
    deal = alert_engine.check_route(None, db_path, ORIGIN, DESTINATION, _search_config(), alert)

    subject, body = alert_engine.format_alert_email([deal])

    assert "1 flight deal" in subject
    assert "Mumbai" in body and "Dubai" in body
