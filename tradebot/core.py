"""SQLite-backed market data, event studies, and saved research findings."""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "tradenerves-backend" / "backend"
DEFAULT_DAILY_DB = BACKEND_DIR / "db" / "stocks.db"
DEFAULT_INTRADAY_DB = BACKEND_DIR / "db" / "stocks_five.db"
DEFAULT_FINDINGS_DB = BACKEND_DIR / "db" / "tradebot_findings.db"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


@dataclass(frozen=True)
class Bar:
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int = 0


def _db_path(timeframe: str) -> Path:
    if timeframe == "1D":
        return Path(os.getenv("TRADENERVES_DAILY_DB_PATH", DEFAULT_DAILY_DB))
    if timeframe == "5m":
        return Path(os.getenv("TRADENERVES_INTRADAY_DB_PATH", DEFAULT_INTRADAY_DB))
    raise ValueError("timeframe must be '1D' or '5m'")


def _ensure_stock_prices(conn: sqlite3.Connection) -> None:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS stock_prices (
            id INTEGER PRIMARY KEY,
            symbol TEXT NOT NULL,
            date TEXT NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume INTEGER
        )"""
    )


class MarketData:
    """Reads the existing Tradenerves bar stores and fetches missing ranges."""

    def __init__(self, daily_db: Path | None = None, intraday_db: Path | None = None):
        self.daily_db = daily_db
        self.intraday_db = intraday_db

    def path_for(self, timeframe: str) -> Path:
        if timeframe == "1D" and self.daily_db:
            return self.daily_db
        if timeframe == "5m" and self.intraday_db:
            return self.intraday_db
        return _db_path(timeframe)

    def load_bars(self, symbol: str, start_date: str, end_date: str, timeframe: str = "1D") -> list[Bar]:
        path = self.path_for(timeframe)
        if not path.exists():
            return []
        with sqlite3.connect(path) as conn:
            rows = conn.execute(
                """SELECT date, open, high, low, close, COALESCE(volume, 0)
                   FROM stock_prices
                   WHERE symbol = ? AND date >= ? AND date <= ?
                   ORDER BY date ASC""",
                (symbol.upper(), start_date, end_date),
            ).fetchall()
        return [Bar(*row) for row in rows]

    def load_or_fetch(
        self, symbol: str, start_date: str, end_date: str, timeframe: str = "1D"
    ) -> dict[str, Any]:
        bars = self.load_bars(symbol, start_date, end_date, timeframe)
        if bars:
            return {"source": "sqlite", "symbol": symbol.upper(), "timeframe": timeframe, "bars": len(bars)}

        api_key = os.getenv("POLYGON_API_KEY") or os.getenv("MASSIVE_API_KEY")
        if not api_key:
            raise RuntimeError("No bars are stored and POLYGON_API_KEY or MASSIVE_API_KEY is not set.")
        fetched = self._fetch_and_store(symbol, start_date, end_date, timeframe, api_key)
        return {"source": "polygon", "symbol": symbol.upper(), "timeframe": timeframe, "bars": fetched}

    def _fetch_and_store(
        self, symbol: str, start_date: str, end_date: str, timeframe: str, api_key: str
    ) -> int:
        import requests

        multiplier, timespan = (1, "day") if timeframe == "1D" else (5, "minute")
        url = (
            f"https://api.polygon.io/v2/aggs/ticker/{symbol.upper()}/range/"
            f"{multiplier}/{timespan}/{start_date}/{end_date}"
        )
        response = requests.get(
            url,
            params={"adjusted": "true", "sort": "asc", "limit": 50000, "apiKey": api_key},
            timeout=30,
        )
        response.raise_for_status()
        results = response.json().get("results", [])

        path = self.path_for(timeframe)
        path.parent.mkdir(parents=True, exist_ok=True)
        date_format = "%Y-%m-%d" if timeframe == "1D" else "%Y-%m-%d-%H:%M"
        rows = [
            (
                symbol.upper(),
                datetime.fromtimestamp(entry["t"] / 1000, timezone.utc).strftime(date_format),
                float(entry.get("o", 0)),
                float(entry.get("h", 0)),
                float(entry.get("l", 0)),
                float(entry.get("c", 0)),
                int(entry.get("v") or 0),
            )
            for entry in results
            if entry.get("t") is not None
        ]
        with sqlite3.connect(path) as conn:
            _ensure_stock_prices(conn)
            existing = {
                row[0]
                for row in conn.execute(
                    "SELECT date FROM stock_prices WHERE symbol = ? AND date >= ? AND date <= ?",
                    (symbol.upper(), start_date, end_date),
                )
            }
            rows = [row for row in rows if row[1] not in existing]
            conn.executemany(
                """INSERT INTO stock_prices (symbol, date, open, high, low, close, volume)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                rows,
            )
        return len(rows)


class PatternBacktester:
    """Event study over existing Tradenerves single-candle pattern definitions."""

    def backtest(self, bars: Iterable[Bar], pattern: str, forward_bars: int) -> dict[str, Any]:
        if forward_bars < 1:
            raise ValueError("forward_bars must be at least 1")
        try:
            from data.optimized_pattern_detection import detect_patterns_for_candle
        except ModuleNotFoundError:
            # This fallback mirrors the existing detector and keeps offline math tests
            # free of its optional NumPy import.
            detect_patterns_for_candle = _detect_patterns_for_candle

        ordered = list(bars)
        events: list[dict[str, Any]] = []
        for index, bar in enumerate(ordered):
            if index + forward_bars >= len(ordered):
                continue
            patterns = detect_patterns_for_candle(bar.open, bar.high, bar.low, bar.close)
            if pattern not in patterns:
                continue
            future_close = ordered[index + forward_bars].close
            return_pct = ((future_close - bar.close) / bar.close) * 100 if bar.close else 0.0
            events.append({"date": bar.date, "return_pct": return_pct})

        returns = [event["return_pct"] for event in events]
        return {
            "pattern": pattern,
            "forward_bars": forward_bars,
            "count": len(events),
            "win_rate_pct": (sum(value > 0 for value in returns) / len(returns) * 100) if returns else 0.0,
            "mean_return_pct": (sum(returns) / len(returns)) if returns else 0.0,
            "events": events,
        }


class FindingsStore:
    """Separate SQLite store for chat findings; market databases remain untouched."""

    def __init__(self, path: Path | None = None):
        self.path = path or Path(os.getenv("TRADEBOT_FINDINGS_DB_PATH", DEFAULT_FINDINGS_DB))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS findings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    pattern TEXT NOT NULL,
                    window TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    result_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )"""
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_findings_lookup ON findings(symbol, pattern, window, created_at)"
            )

    def save(
        self, symbol: str, pattern: str, window: str, summary: str, result: dict[str, Any]
    ) -> dict[str, Any]:
        created_at = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.path) as conn:
            cursor = conn.execute(
                """INSERT INTO findings(symbol, pattern, window, summary, result_json, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (symbol.upper(), pattern, window, summary, json.dumps(result), created_at),
            )
        return {"id": cursor.lastrowid, "created_at": created_at}

    def lookup(self, symbol: str, pattern: str, window: str) -> list[dict[str, Any]]:
        with sqlite3.connect(self.path) as conn:
            rows = conn.execute(
                """SELECT id, symbol, pattern, window, summary, result_json, created_at
                   FROM findings WHERE symbol = ? AND pattern = ? AND window = ?
                   ORDER BY created_at DESC""",
                (symbol.upper(), pattern, window),
            ).fetchall()
        return [
            {
                "id": row[0],
                "symbol": row[1],
                "pattern": row[2],
                "window": row[3],
                "summary": row[4],
                "result": json.loads(row[5]),
                "created_at": row[6],
            }
            for row in rows
        ]


def bars_as_dicts(bars: Iterable[Bar]) -> list[dict[str, Any]]:
    return [asdict(bar) for bar in bars]


def _detect_patterns_for_candle(open_price: float, high_price: float, low_price: float, close_price: float) -> list[str]:
    """Dependency-free equivalent of data.optimized_pattern_detection's detector."""
    body = abs(close_price - open_price)
    upper_wick = high_price - max(open_price, close_price)
    lower_wick = min(open_price, close_price) - low_price
    full_range = max(high_price - low_price, 1e-12)
    patterns = []
    if (
        close_price > open_price
        and body > max(0.0, abs(open_price) * 0.0075)
        and body / full_range >= 0.6
        and upper_wick <= full_range * 0.1
        and lower_wick <= full_range * 0.2
    ):
        patterns.append("green")
    if (
        body > 0
        and body / full_range <= 0.35
        and lower_wick / body >= 2.0
        and upper_wick / body <= 0.5
        and max(open_price, close_price) >= low_price + 0.6 * full_range
    ):
        patterns.append("hammer")
    is_doji = body / full_range <= 0.1
    if is_doji:
        patterns.append("doji")
    if close_price < open_price and is_doji:
        patterns.append("red_doji")
    if close_price < open_price:
        patterns.append("red")
    if close_price > open_price:
        patterns.append("green_any")
    return patterns
