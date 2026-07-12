from datetime import datetime, timedelta, timezone

from src.price_store import get_route_stats, record_price


def test_rolling_average_within_window(tmp_path):
    db_path = tmp_path / "prices.sqlite3"
    now = datetime(2026, 7, 12, tzinfo=timezone.utc)

    for days_ago, price in [(5, 20000), (10, 21000), (15, 19000)]:
        record_price(
            db_path, "BOM", "DXB", price, "INR", checked_at=now - timedelta(days=days_ago)
        )

    stats = get_route_stats(db_path, "BOM", "DXB", rolling_window_days=30, before=now)

    assert stats.sample_count == 3
    assert stats.rolling_average == (20000 + 21000 + 19000) / 3


def test_rolling_average_excludes_old_and_future_points(tmp_path):
    db_path = tmp_path / "prices.sqlite3"
    now = datetime(2026, 7, 12, tzinfo=timezone.utc)

    record_price(db_path, "BOM", "DXB", 15000, "INR", checked_at=now - timedelta(days=40))
    record_price(db_path, "BOM", "DXB", 20000, "INR", checked_at=now - timedelta(days=5))
    record_price(db_path, "BOM", "DXB", 99999, "INR", checked_at=now)  # "today's" own reading

    stats = get_route_stats(db_path, "BOM", "DXB", rolling_window_days=30, before=now)

    assert stats.sample_count == 1
    assert stats.rolling_average == 20000


def test_no_history_returns_none_average(tmp_path):
    db_path = tmp_path / "prices.sqlite3"

    stats = get_route_stats(db_path, "BOM", "SIN", rolling_window_days=30)

    assert stats.sample_count == 0
    assert stats.rolling_average is None
