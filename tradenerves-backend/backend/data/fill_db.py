import argparse
import logging
import os
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests
from paths import DAILY_DB_PATH, INTRADAY_DB_PATH

DEFAULT_SYMBOLS = [
    'SPY',
    'AAPL', 'NVDA', 'TSLA', 'MSFT', 'GOOGL', 'AMZN',
    'JPM', 'BAC', 'WFC', 'GS', 'AXP',
    'JNJ', 'UNH', 'PFE',
    'XOM', 'CVX', 'COP',
    'WMT', 'PG', 'KO',
    'META', 'NFLX', 'ADBE',
    'AAL', 'PLTR', 'FTNT', 'PANW', 'ZS'
]

INTRADAY_DB_FMT = '%Y-%m-%d-%H:%M'

logger = logging.getLogger(__name__)


def ensure_stock_prices_table(conn):
    conn.execute('''
        CREATE TABLE IF NOT EXISTS stock_prices (
            id INTEGER PRIMARY KEY,
            symbol TEXT,
            date TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER
        )
    ''')
    conn.commit()


def parse_date(value):
    return datetime.strptime(value, '%Y-%m-%d')


def get_last_date(conn, symbol, fmt):
    cur = conn.cursor()
    cur.execute('SELECT date FROM stock_prices WHERE symbol = ? ORDER BY date DESC LIMIT 1', (symbol,))
    row = cur.fetchone()
    if not row or not row[0]:
        return None
    try:
        return datetime.strptime(row[0], fmt)
    except ValueError:
        return None


def resolve_date_range(start_date, end_date, years_back, last_dt, step):
    end_dt = parse_date(end_date) if end_date else datetime.utcnow().date()
    if isinstance(end_dt, datetime):
        end_dt = end_dt.date()
    end_dt = datetime.combine(end_dt, datetime.min.time())

    if start_date:
        start_dt = parse_date(start_date)
    elif years_back:
        start_dt = end_dt - timedelta(days=int(years_back) * 365)
    elif last_dt:
        start_dt = last_dt + step
    else:
        start_dt = end_dt - timedelta(days=365)

    if start_dt > end_dt:
        return None, None
    return start_dt, end_dt


def polygon_aggs(symbol, start_date, end_date, multiplier, timespan, api_key, limit=50000, retries=3):
    url = (
        f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/{multiplier}/{timespan}/"
        f"{start_date}/{end_date}?adjusted=true&sort=asc&limit={limit}&apiKey={api_key}"
    )

    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get('results', [])
        except Exception as exc:
            wait = 1 + attempt * 2
            logger.warning("Polygon request failed (%s); retrying in %ss", exc, wait)
            time.sleep(wait)
    return []


def insert_rows(conn, rows):
    if not rows:
        return 0
    cur = conn.cursor()
    cur.executemany(
        '''
        INSERT INTO stock_prices (symbol, date, open, high, low, close, volume)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''',
        rows
    )
    conn.commit()
    return len(rows)


def fetch_daily(symbol, api_key, start_date=None, end_date=None, years_back=30, chunk_days=365):
    conn = sqlite3.connect(DAILY_DB_PATH)
    ensure_stock_prices_table(conn)

    last_dt = get_last_date(conn, symbol, '%Y-%m-%d')
    start_dt, end_dt = resolve_date_range(
        start_date,
        end_date,
        years_back,
        last_dt,
        step=timedelta(days=1)
    )
    if not start_dt:
        logger.info("Daily data for %s already up to date.", symbol)
        conn.close()
        return

    cursor_dt = start_dt
    total = 0
    while cursor_dt <= end_dt:
        chunk_end = min(cursor_dt + timedelta(days=chunk_days - 1), end_dt)
        data = polygon_aggs(
            symbol,
            cursor_dt.strftime('%Y-%m-%d'),
            chunk_end.strftime('%Y-%m-%d'),
            multiplier=1,
            timespan='day',
            api_key=api_key
        )

        rows = []
        for entry in data:
            ts = entry.get('t')
            if ts is None:
                continue
            date_str = datetime.fromtimestamp(ts / 1000, timezone.utc).strftime('%Y-%m-%d')
            rows.append((
                symbol,
                date_str,
                float(entry.get('o', 0.0)),
                float(entry.get('h', 0.0)),
                float(entry.get('l', 0.0)),
                float(entry.get('c', 0.0)),
                int(entry.get('v', 0) or 0)
            ))

        total += insert_rows(conn, rows)
        logger.info("Daily %s %s → %s: inserted %d", symbol, cursor_dt.date(), chunk_end.date(), len(rows))
        cursor_dt = chunk_end + timedelta(days=1)
        time.sleep(0.15)

    conn.close()
    logger.info("Daily %s: inserted %d rows", symbol, total)


def fetch_intraday(symbol, api_key, start_date=None, end_date=None, years_back=5, chunk_days=30, multiplier=5,
                   timespan='minute', rth_only=False):
    conn = sqlite3.connect(INTRADAY_DB_PATH)
    ensure_stock_prices_table(conn)

    last_dt = get_last_date(conn, symbol, INTRADAY_DB_FMT)
    step = timedelta(minutes=multiplier)
    start_dt, end_dt = resolve_date_range(
        start_date,
        end_date,
        years_back,
        last_dt,
        step=step
    )
    if not start_dt:
        logger.info("Intraday data for %s already up to date.", symbol)
        conn.close()
        return

    tz_et = ZoneInfo('America/New_York')
    cursor_dt = start_dt
    total = 0

    while cursor_dt <= end_dt:
        chunk_end = min(cursor_dt + timedelta(days=chunk_days - 1), end_dt)
        data = polygon_aggs(
            symbol,
            cursor_dt.strftime('%Y-%m-%d'),
            chunk_end.strftime('%Y-%m-%d'),
            multiplier=multiplier,
            timespan=timespan,
            api_key=api_key
        )

        rows = []
        for entry in data:
            ts = entry.get('t')
            if ts is None:
                continue
            dt_utc = datetime.fromtimestamp(ts / 1000, timezone.utc)
            if rth_only:
                dt_et = dt_utc.astimezone(tz_et)
                if dt_et.weekday() > 4:
                    continue
                hhmm = dt_et.strftime('%H:%M')
                if hhmm < '09:30' or hhmm > '16:00':
                    continue

            date_str = dt_utc.strftime(INTRADAY_DB_FMT)
            rows.append((
                symbol,
                date_str,
                float(entry.get('o', 0.0)),
                float(entry.get('h', 0.0)),
                float(entry.get('l', 0.0)),
                float(entry.get('c', 0.0)),
                int(entry.get('v', 0) or 0)
            ))

        total += insert_rows(conn, rows)
        logger.info("Intraday %s %s → %s: inserted %d", symbol, cursor_dt.date(), chunk_end.date(), len(rows))
        cursor_dt = chunk_end + timedelta(days=1)
        time.sleep(0.15)

    conn.close()
    logger.info("Intraday %s: inserted %d rows", symbol, total)


def main():
    parser = argparse.ArgumentParser(description='Fill daily and intraday Polygon data into SQLite DBs.')
    parser.add_argument('--api-key', default=os.getenv('POLYGON_API_KEY'))
    parser.add_argument('--symbols', nargs='*', default=DEFAULT_SYMBOLS)
    parser.add_argument('--mode', choices=['daily', 'intraday', 'both'], default='both')
    parser.add_argument('--start-date', help='YYYY-MM-DD start date override')
    parser.add_argument('--end-date', help='YYYY-MM-DD end date override')
    parser.add_argument('--daily-years-back', type=int, default=30)
    parser.add_argument('--intraday-years-back', type=int, default=5)
    parser.add_argument('--daily-chunk-days', type=int, default=365)
    parser.add_argument('--intraday-chunk-days', type=int, default=30)
    parser.add_argument('--intraday-multiplier', type=int, default=5)
    parser.add_argument('--intraday-timespan', default='minute')
    parser.add_argument('--rth-only', action='store_true')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

    if not args.api_key:
        raise SystemExit('Missing Polygon API key. Set POLYGON_API_KEY or pass --api-key.')

    for symbol in args.symbols:
        if args.mode in ('daily', 'both'):
            fetch_daily(
                symbol,
                args.api_key,
                start_date=args.start_date,
                end_date=args.end_date,
                years_back=args.daily_years_back,
                chunk_days=args.daily_chunk_days
            )
        if args.mode in ('intraday', 'both'):
            fetch_intraday(
                symbol,
                args.api_key,
                start_date=args.start_date,
                end_date=args.end_date,
                years_back=args.intraday_years_back,
                chunk_days=args.intraday_chunk_days,
                multiplier=args.intraday_multiplier,
                timespan=args.intraday_timespan,
                rth_only=args.rth_only
            )


if __name__ == '__main__':
    main()
