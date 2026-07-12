# Flight Deal Alerts

Watches round-trip flight prices departing **Mumbai (BOM)** and **Delhi (DEL)**
to a configurable list of destinations, and emails you when a price drops at
least X% below that route's 30-day rolling average. Runs on a daily GitHub
Actions schedule — no server to maintain.

Telegram delivery is stubbed out (`src/notifiers/telegram_notifier.py`) behind
the same `Notifier` interface as email, ready to wire up later.

## How it works

1. `config.yaml` defines origins, destinations, the date window to search,
   and the alert rule (default: alert when a route's price is ≥50% cheaper
   than its 30-day average, once at least 5 historical prices exist for it).
2. Each run samples a few departure dates spread across a rolling window
   (default 30–90 days out, 7-day trips), queries the
   [Amadeus Flight Offers Search API](https://developers.amadeus.com/) for
   each origin→destination pair, and takes the cheapest offer found.
3. That price is recorded in `data/price_history.sqlite3` and compared
   against the rolling average for that route.
4. Any route that clears the discount threshold goes into a single summary
   email.

## One-time setup

### 1. Amadeus API credentials (free)

1. Sign up at https://developers.amadeus.com/
2. Create an app under "My Apps" — this gives you an API Key and API Secret
   for the **test environment** (free, generous quota, but only a subset of
   real-world fares/routes — good enough to get this running; you can
   request production access later for full coverage).

### 2. Gmail app password (free)

1. Enable 2-Step Verification on the Google account you want to send from.
2. Go to Google Account → Security → App passwords, generate one for "Mail".

### 3. Configure secrets

**Local run:**
```bash
cp .env.example .env
# fill in AMADEUS_API_KEY, AMADEUS_API_SECRET, GMAIL_ADDRESS, GMAIL_APP_PASSWORD, ALERT_EMAIL_TO
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m src.main
```

**GitHub Actions:** add these as repository secrets (Settings → Secrets and
variables → Actions):
- `AMADEUS_API_KEY`
- `AMADEUS_API_SECRET`
- `GMAIL_ADDRESS`
- `GMAIL_APP_PASSWORD`
- `ALERT_EMAIL_TO` (where alerts should land — e.g. your gmail address)

The workflow in `.github/workflows/flight_price_check.yml` runs daily at
03:00 UTC and can also be triggered manually from the Actions tab
("Run workflow"). Price history persists between runs via `actions/cache`
(no data is committed to the repo).

## Customizing

Edit `config.yaml`:
- `destinations`: add/remove cities (use IATA airport codes)
- `search.window_start_days` / `window_end_days`: how far out to look
- `search.trip_length_days`: round-trip length searched
- `alert.discount_threshold_pct`: how big a drop triggers an alert
- `alert.rolling_window_days` / `min_history_points`: how the baseline is computed

## Adding Telegram later

`src/notifiers/telegram_notifier.py` already implements the `Notifier`
interface but only logs today. To enable it:
1. Create a bot via [@BotFather](https://t.me/BotFather), get its token.
2. Message the bot, then fetch your chat id from
   `https://api.telegram.org/bot<token>/getUpdates`.
3. Implement `TelegramNotifier.send()` as a POST to
   `https://api.telegram.org/bot<token>/sendMessage`.
4. Set `notifications.telegram.enabled: true` in `config.yaml` and add the
   bot token/chat id as secrets.

## Tests

```bash
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest
```
