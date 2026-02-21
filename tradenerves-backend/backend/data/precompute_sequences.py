import argparse
import sqlite3
from collections import OrderedDict
from datetime import datetime
from paths import DAILY_DB_PATH, INTRADAY_DB_PATH

PATTERN_KEYS = [
    'green',
    'hammer',
    'doji',
    'red_doji',
    'red',
    'green_any'
]

INTRADAY_DB_FMT = '%Y-%m-%d-%H:%M'
INTRADAY_ISO_FMT = '%Y-%m-%dT%H:%M'
TIMEFRAMES = ['1D', '5m', '10m', '15m', '1h']


def _candle_parts(open_price, high_price, low_price, close_price):
    body = abs(close_price - open_price)
    upper_wick = high_price - max(open_price, close_price)
    lower_wick = min(open_price, close_price) - low_price
    full_range = max(high_price - low_price, 1e-12)
    return body, upper_wick, lower_wick, full_range


def candle_is_solid_green(
    open_price,
    high_price,
    low_price,
    close_price,
    body_min_abs=0.0,
    body_min_pct=0.0075,
    close_to_high_max_range_ratio=0.1,
    lower_wick_max_range_ratio=0.2,
    body_to_range_min=0.6,
):
    if close_price <= open_price:
        return False

    body, upper_wick, lower_wick, full_range = _candle_parts(open_price, high_price, low_price, close_price)
    body_min = max(body_min_abs, abs(open_price) * body_min_pct)
    if body <= body_min:
        return False

    if (body / full_range) < body_to_range_min:
        return False

    if upper_wick > (full_range * close_to_high_max_range_ratio):
        return False

    if lower_wick > (full_range * lower_wick_max_range_ratio):
        return False

    return True


def candle_is_hammer(
    open_price,
    high_price,
    low_price,
    close_price,
    lower_wick_to_body_min=2.0,
    upper_wick_to_body_max=0.5,
    body_to_range_max=0.35,
):
    body, upper_wick, lower_wick, full_range = _candle_parts(open_price, high_price, low_price, close_price)
    if body <= 0:
        return False

    if (body / full_range) > body_to_range_max:
        return False
    if (lower_wick / body) < lower_wick_to_body_min:
        return False
    if (upper_wick / body) > upper_wick_to_body_max:
        return False
    if max(open_price, close_price) < (low_price + (0.6 * full_range)):
        return False

    return True


def candle_is_doji(open_price, high_price, low_price, close_price, body_to_range_max=0.1, body_abs_max=None):
    body, _, _, full_range = _candle_parts(open_price, high_price, low_price, close_price)

    if body_abs_max is not None and body > body_abs_max:
        return False

    return (body / full_range) <= body_to_range_max


def candle_is_red_doji(open_price, high_price, low_price, close_price, body_to_range_max=0.1, body_abs_max=None):
    if close_price >= open_price:
        return False
    return candle_is_doji(
        open_price=open_price,
        high_price=high_price,
        low_price=low_price,
        close_price=close_price,
        body_to_range_max=body_to_range_max,
        body_abs_max=body_abs_max,
    )


def candle_matches_pattern(pattern_key, open_price, high_price, low_price, close_price):
    key = (pattern_key or '').strip().lower()
    if key in {'green', 'solid_green'}:
        return candle_is_solid_green(open_price, high_price, low_price, close_price)
    if key == 'hammer':
        return candle_is_hammer(open_price, high_price, low_price, close_price)
    if key == 'doji':
        return candle_is_doji(open_price, high_price, low_price, close_price)
    if key in {'red_doji', 'doji_red'}:
        return candle_is_red_doji(open_price, high_price, low_price, close_price)
    if key in {'red', 'bearish'}:
        return close_price < open_price
    if key in {'green_any', 'bullish'}:
        return close_price > open_price
    raise ValueError(f"Unknown pattern key: {pattern_key}")


def get_db_connection(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def timeframe_minutes(timeframe):
    return {
        '5m': 5,
        '10m': 10,
        '15m': 15,
        '1h': 60
    }.get(timeframe)


def to_intraday_iso(date_str):
    return datetime.strptime(date_str, INTRADAY_DB_FMT).strftime(INTRADAY_ISO_FMT)


def aggregate_intraday_rows(rows, minutes):
    buckets = OrderedDict()
    for row in rows:
        dt = datetime.strptime(row['date'], INTRADAY_DB_FMT)
        bucket = dt.replace(minute=(dt.minute // minutes) * minutes, second=0, microsecond=0)
        key = bucket.strftime(INTRADAY_ISO_FMT)
        if key not in buckets:
            buckets[key] = {
                'date': key,
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': int(row['volume']) if row['volume'] is not None else 0
            }
        else:
            bucket_row = buckets[key]
            bucket_row['high'] = max(bucket_row['high'], float(row['high']))
            bucket_row['low'] = min(bucket_row['low'], float(row['low']))
            bucket_row['close'] = float(row['close'])
            bucket_row['volume'] += int(row['volume']) if row['volume'] is not None else 0
    return list(buckets.values())


def get_timeframe_bars(conn, symbol, timeframe):
    cur = conn.cursor()
    cur.execute(
        'SELECT date, open, high, low, close, volume FROM stock_prices WHERE symbol = ? ORDER BY date ASC',
        (symbol,)
    )
    rows = cur.fetchall()
    if not rows:
        return []

    if timeframe == '1D':
        return [
            {
                'date': row['date'],
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': int(row['volume']) if row['volume'] is not None else 0
            }
            for row in rows
        ]

    if timeframe == '5m':
        return [
            {
                'date': to_intraday_iso(row['date']),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': int(row['volume']) if row['volume'] is not None else 0
            }
            for row in rows
        ]

    minutes = timeframe_minutes(timeframe)
    return aggregate_intraday_rows(rows, minutes)


def ensure_pattern_sequences_table(conn):
    conn.execute('''
        CREATE TABLE IF NOT EXISTS pattern_sequences (
            id INTEGER PRIMARY KEY,
            symbol TEXT,
            timeframe TEXT,
            sequence TEXT,
            start_date TEXT,
            end_date TEXT,
            next_start TEXT,
            UNIQUE(symbol, timeframe, sequence, start_date)
        )
    ''')
    conn.execute('''
        CREATE INDEX IF NOT EXISTS idx_pattern_sequences_lookup
        ON pattern_sequences(sequence, timeframe, symbol)
    ''')
    conn.commit()


def fetch_symbols(conn):
    cur = conn.cursor()
    cur.execute('SELECT symbol FROM stock_prices GROUP BY symbol')
    return [row['symbol'] for row in cur.fetchall()]


def insert_sequences(conn, rows):
    if not rows:
        return 0
    conn.executemany(
        '''
        INSERT OR IGNORE INTO pattern_sequences
        (symbol, timeframe, sequence, start_date, end_date, next_start)
        VALUES (?, ?, ?, ?, ?, ?)
        ''',
        rows
    )
    conn.commit()
    return len(rows)


def compute_two_candle_sequences(bars, symbol, timeframe):
    tuples = [
        (bar['date'], bar['open'], bar['high'], bar['low'], bar['close'])
        for bar in bars
    ]
    if len(tuples) < 3:
        return []

    matches_per_bar = []
    for date, open_price, high_price, low_price, close_price in tuples:
        matches = [
            key for key in PATTERN_KEYS
            if candle_matches_pattern(key, open_price, high_price, low_price, close_price)
        ]
        matches_per_bar.append(matches)

    rows = []
    for idx in range(len(tuples) - 2):
        first_patterns = matches_per_bar[idx]
        second_patterns = matches_per_bar[idx + 1]
        if not first_patterns or not second_patterns:
            continue
        start_date = tuples[idx][0]
        end_date = tuples[idx + 1][0]
        next_start = tuples[idx + 2][0]
        for p1 in first_patterns:
            for p2 in second_patterns:
                rows.append((
                    symbol,
                    timeframe,
                    f"{p1},{p2}",
                    start_date,
                    end_date,
                    next_start
                ))
    return rows


def main():
    parser = argparse.ArgumentParser(description='Precompute and store all two-candle pattern sequences.')
    parser.add_argument('--timeframes', nargs='*', default=TIMEFRAMES)
    parser.add_argument('--symbols', nargs='*')
    args = parser.parse_args()

    for timeframe in args.timeframes:
        if timeframe == '1D':
            conn = get_db_connection(DAILY_DB_PATH)
        else:
            conn = get_db_connection(INTRADAY_DB_PATH)
        ensure_pattern_sequences_table(conn)

        symbols = args.symbols or fetch_symbols(conn)
        for symbol in symbols:
            bars = get_timeframe_bars(conn, symbol, timeframe)
            if not bars:
                continue
            rows = compute_two_candle_sequences(bars, symbol, timeframe)
            insert_sequences(conn, rows)

        conn.close()


if __name__ == '__main__':
    main()
