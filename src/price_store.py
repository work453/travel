"""SQLite-backed price history so we can compute a rolling average per route.

One row per (origin, destination, check run) — the cheapest price found
across that run's sampled dates for the route.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "price_history.sqlite3"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    price REAL NOT NULL,
    currency TEXT NOT NULL,
    checked_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_price_history_route
    ON price_history (origin, destination, checked_at);
"""


@contextmanager
def _connect(db_path: Path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(_SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


@dataclass(frozen=True)
class RouteStats:
    rolling_average: float | None
    sample_count: int


def record_price(
    db_path: Path,
    origin: str,
    destination: str,
    price: float,
    currency: str,
    checked_at: datetime | None = None,
) -> None:
    checked_at = checked_at or datetime.now(timezone.utc)
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT INTO price_history (origin, destination, price, currency, checked_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (origin, destination, price, currency, checked_at.isoformat()),
        )


def get_route_stats(
    db_path: Path,
    origin: str,
    destination: str,
    rolling_window_days: int,
    before: datetime | None = None,
) -> RouteStats:
    """Rolling average + sample count over the last `rolling_window_days`,
    excluding anything at/after `before` (defaults to now) so a price just
    recorded in this run doesn't skew its own baseline."""
    before = before or datetime.now(timezone.utc)
    cutoff = before.timestamp() - rolling_window_days * 86400

    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT price, checked_at FROM price_history "
            "WHERE origin = ? AND destination = ? AND checked_at < ?",
            (origin, destination, before.isoformat()),
        ).fetchall()

    recent_prices = [
        price
        for price, checked_at in rows
        if datetime.fromisoformat(checked_at).timestamp() >= cutoff
    ]

    if not recent_prices:
        return RouteStats(rolling_average=None, sample_count=0)

    return RouteStats(
        rolling_average=sum(recent_prices) / len(recent_prices),
        sample_count=len(recent_prices),
    )
