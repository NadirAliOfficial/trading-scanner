import threading
import requests
from datetime import datetime, timezone, timedelta
import config

FF_CALENDAR_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"

SYMBOL_CURRENCIES = {
    "XAUUSD": ["USD"],        # XAU not on FF; USD events move gold
    "EURUSD": ["EUR", "USD"],
    "GBPUSD": ["GBP", "USD"],
    "USDJPY": ["USD", "JPY"],
    "GBPJPY": ["GBP", "JPY"],
    "EURJPY": ["EUR", "JPY"],
}

_cache: dict = {"events": [], "fetched_at": None}
_lock = threading.Lock()


def _parse_dt(date_str: str):
    """Parse ISO-8601 datetime string to UTC-aware datetime."""
    if not date_str:
        return None
    try:
        # Python 3.11+ handles offset natively; fallback for 3.9/3.10
        try:
            dt = datetime.fromisoformat(date_str)
        except ValueError:
            # Try replacing trailing Z
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def fetch_calendar(force=False):
    """Fetch ForexFactory calendar JSON. Cached for 1 hour."""
    with _lock:
        now = datetime.now(timezone.utc)
        age = (now - _cache["fetched_at"]).total_seconds() if _cache["fetched_at"] else 9999
        if not force and age < 3600 and _cache["events"]:
            return _cache["events"]
        try:
            r = requests.get(
                FF_CALENDAR_URL,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10,
            )
            r.raise_for_status()
            _cache["events"] = r.json()
            _cache["fetched_at"] = now
        except Exception as e:
            print(f"[NewsFilter] Calendar fetch failed: {e}")
        return _cache["events"]


def get_upcoming_events(hours=24, impacts=("High", "Medium", "Low")):
    """Return events within the next N hours, sorted by time."""
    events = fetch_calendar()
    now = datetime.now(timezone.utc)
    cutoff = now + timedelta(hours=hours)
    result = []
    for ev in events:
        dt = _parse_dt(ev.get("date", ""))
        if dt is None or not (now - timedelta(hours=1) <= dt <= cutoff):
            continue
        impact = ev.get("impact", "")
        if impact not in impacts:
            continue
        delta_min = (dt - now).total_seconds() / 60
        result.append({
            "title": ev.get("title", ""),
            "currency": ev.get("country", ""),
            "impact": impact,
            "datetime_utc": dt,
            "forecast": ev.get("forecast") or "—",
            "previous": ev.get("previous") or "—",
            "actual": ev.get("actual") or "—",
            "minutes_away": round(delta_min),
        })
    return sorted(result, key=lambda x: x["datetime_utc"])


def is_news_blackout(symbol: str):
    """
    Returns (blackout: bool, reason: str | None).
    Blocks if a HIGH-impact event for the symbol's currencies is within
    the pre/post window defined in config.
    """
    currencies = SYMBOL_CURRENCIES.get(symbol.upper(), [])
    if not currencies:
        return False, None

    events = fetch_calendar()
    now = datetime.now(timezone.utc)
    pre = config.NEWS_BLOCK_MINUTES_BEFORE
    post = config.NEWS_BLOCK_MINUTES_AFTER

    for ev in events:
        if ev.get("impact", "") != "High":
            continue
        if ev.get("country", "").upper() not in currencies:
            continue
        dt = _parse_dt(ev.get("date", ""))
        if dt is None:
            continue
        delta_min = (dt - now).total_seconds() / 60
        if -post <= delta_min <= pre:
            direction = f"in {int(delta_min)}m" if delta_min > 0 else f"{abs(int(delta_min))}m ago"
            reason = f"⚠️ {ev.get('country')} high-impact event {direction}: {ev.get('title', '')}"
            return True, reason

    return False, None


def get_next_high_impact(currencies=("USD", "EUR", "GBP", "JPY")):
    """Return the next HIGH-impact event for tracked currencies."""
    events = get_upcoming_events(hours=48, impacts=("High",))
    for ev in events:
        if ev["currency"].upper() in currencies and ev["minutes_away"] > 0:
            return ev
    return None
