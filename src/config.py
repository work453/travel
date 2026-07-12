"""Loads config.yaml plus secrets from the environment (.env for local runs)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")


@dataclass(frozen=True)
class Place:
    code: str
    name: str


@dataclass(frozen=True)
class SearchConfig:
    window_start_days: int
    window_end_days: int
    sample_dates: int
    trip_length_days: int
    currency: str


@dataclass(frozen=True)
class AlertConfig:
    discount_threshold_pct: float
    rolling_window_days: int
    min_history_points: int


@dataclass(frozen=True)
class Secrets:
    amadeus_api_key: str
    amadeus_api_secret: str
    gmail_address: str
    gmail_app_password: str
    alert_email_to: str


@dataclass(frozen=True)
class Config:
    origins: list[Place]
    destinations: list[Place]
    search: SearchConfig
    alert: AlertConfig
    email_enabled: bool
    telegram_enabled: bool
    amadeus_enabled: bool
    google_flights_enabled: bool
    secrets: Secrets


def _require_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise RuntimeError(
            f"Missing required environment variable {name}. "
            "Copy .env.example to .env (or set repo secrets in CI) and fill it in."
        )
    return value


def load_config(path: Path | None = None) -> Config:
    path = path or REPO_ROOT / "config.yaml"
    raw = yaml.safe_load(path.read_text())

    sources = raw.get("sources", {})
    amadeus_enabled = bool(sources.get("amadeus", {}).get("enabled", True))
    google_flights_enabled = bool(sources.get("google_flights", {}).get("enabled", False))

    secrets = Secrets(
        amadeus_api_key=_require_env("AMADEUS_API_KEY") if amadeus_enabled else "",
        amadeus_api_secret=_require_env("AMADEUS_API_SECRET") if amadeus_enabled else "",
        gmail_address=_require_env("GMAIL_ADDRESS"),
        gmail_app_password=_require_env("GMAIL_APP_PASSWORD"),
        alert_email_to=os.environ.get("ALERT_EMAIL_TO") or _require_env("GMAIL_ADDRESS"),
    )

    return Config(
        origins=[Place(**o) for o in raw["origins"]],
        destinations=[Place(**d) for d in raw["destinations"]],
        search=SearchConfig(**raw["search"]),
        alert=AlertConfig(**raw["alert"]),
        email_enabled=bool(raw["notifications"]["email"]["enabled"]),
        telegram_enabled=bool(raw["notifications"]["telegram"]["enabled"]),
        amadeus_enabled=amadeus_enabled,
        google_flights_enabled=google_flights_enabled,
        secrets=secrets,
    )
