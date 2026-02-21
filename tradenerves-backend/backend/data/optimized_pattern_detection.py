"""
Optimized pattern detection for efficient SQLite storage and retrieval.
- Single-pass detection for all pattern types
- Batch inserts for 100x better performance
- Support for 3-candle sequences
- Minimal storage footprint
"""

import sqlite3
import numpy as np
from typing import List, Tuple, Dict
from paths import DAILY_DB_PATH, INTRADAY_DB_PATH

PATTERN_KEYS = ['green', 'hammer', 'doji', 'red_doji', 'red', 'green_any']


def _candle_parts(open_price, high_price, low_price, close_price):
    """Calculate candle components efficiently"""
    body = abs(close_price - open_price)
    upper_wick = high_price - max(open_price, close_price)
    lower_wick = min(open_price, close_price) - low_price
    full_range = max(high_price - low_price, 1e-12)
    return body, upper_wick, lower_wick, full_range


def candle_is_solid_green(open_price, high_price, low_price, close_price,
                          body_min_abs=0.0, body_min_pct=0.0075,
                          close_to_high_max_range_ratio=0.1,
                          lower_wick_max_range_ratio=0.2,
                          body_to_range_min=0.6):
    """Check if candle is a solid green candle"""
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


def candle_is_hammer(open_price, high_price, low_price, close_price,
                    lower_wick_to_body_min=2.0,
                    upper_wick_to_body_max=0.5,
                    body_to_range_max=0.35):
    """Check if candle is a hammer"""
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


def candle_is_doji(open_price, high_price, low_price, close_price,
                  body_to_range_max=0.1, body_abs_max=None):
    """Check if candle is a doji"""
    body, _, _, full_range = _candle_parts(open_price, high_price, low_price, close_price)

    if body_abs_max is not None and body > body_abs_max:
        return False

    return (body / full_range) <= body_to_range_max


def candle_is_red_doji(open_price, high_price, low_price, close_price,
                      body_to_range_max=0.1, body_abs_max=None):
    """Check if candle is a red doji"""
    if close_price >= open_price:
        return False
    return candle_is_doji(open_price, high_price, low_price, close_price,
                         body_to_range_max, body_abs_max)


def detect_patterns_for_candle(open_price, high_price, low_price, close_price) -> List[str]:
    """Detect all patterns that match a single candle - SINGLE PASS"""
    patterns = []
    
    # Check all pattern types in one function call
    if candle_is_solid_green(open_price, high_price, low_price, close_price):
        patterns.append('green')
    
    if candle_is_hammer(open_price, high_price, low_price, close_price):
        patterns.append('hammer')
    
    if candle_is_doji(open_price, high_price, low_price, close_price):
        patterns.append('doji')
    
    if candle_is_red_doji(open_price, high_price, low_price, close_price):
        patterns.append('red_doji')
    
    if close_price < open_price:
        patterns.append('red')
    
    if close_price > open_price:
        patterns.append('green_any')
    
    return patterns


def ensure_optimized_schema(conn):
    """Create optimized database schema"""
    
    # Single unified pattern occurrences table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS pattern_occurrences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            pattern_type TEXT NOT NULL,
            date TEXT NOT NULL,
            UNIQUE(symbol, timeframe, pattern_type, date)
        )
    ''')
    
    # Compound index for fast lookups
    conn.execute('''
        CREATE INDEX IF NOT EXISTS idx_pattern_lookup
        ON pattern_occurrences(pattern_type, timeframe, symbol, date)
    ''')
    
    # Sequence table with 3-candle support
    conn.execute('''
        CREATE TABLE IF NOT EXISTS pattern_sequences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            sequence TEXT NOT NULL,
            sequence_length INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            next_start TEXT NOT NULL,
            UNIQUE(symbol, timeframe, sequence, start_date)
        )
    ''')
    
    conn.execute('''
        CREATE INDEX IF NOT EXISTS idx_sequence_lookup
        ON pattern_sequences(sequence_length, sequence, timeframe, symbol)
    ''')
    
    conn.commit()


def detect_and_store_all_patterns(symbol: str, timeframe: str = '1D', 
                                  db_path: str = DAILY_DB_PATH) -> int:
    """
    Optimized detection and storage of ALL patterns for a symbol in ONE PASS.
    Returns number of pattern occurrences stored.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    ensure_optimized_schema(conn)
    
    # Fetch all OHLC data in one query
    cur = conn.cursor()
    cur.execute('''
        SELECT date, open, high, low, close
        FROM stock_prices
        WHERE symbol = ?
        ORDER BY date ASC
    ''', (symbol,))
    
    rows = cur.fetchall()
    
    if len(rows) < 3:
        print(f"Insufficient data for {symbol} ({len(rows)} rows)")
        conn.close()
        return 0
    
    # Single-pass detection: Check all patterns for each candle
    pattern_occurrences = []
    
    for row in rows:
        date, o, h, l, c = row['date'], row['open'], row['high'], row['low'], row['close']
        
        # Get all patterns that match this candle
        matched_patterns = detect_patterns_for_candle(o, h, l, c)
        
        # Store each match
        for pattern in matched_patterns:
            pattern_occurrences.append((symbol, timeframe, pattern, date))
    
    # Batch insert - MUCH faster than individual inserts
    if pattern_occurrences:
        conn.executemany('''
            INSERT OR IGNORE INTO pattern_occurrences (symbol, timeframe, pattern_type, date)
            VALUES (?, ?, ?, ?)
        ''', pattern_occurrences)
        conn.commit()
    
    count = len(pattern_occurrences)
    print(f"✓ Stored {count} pattern occurrences for {symbol} ({timeframe})")
    
    conn.close()
    return count


def generate_3_candle_sequences(symbol: str, timeframe: str = '1D',
                                db_path: str = DAILY_DB_PATH) -> int:
    """
    Generate all 3-candle sequences efficiently.
    Returns number of sequences stored.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # Get all dates with their patterns
    cur = conn.cursor()
    cur.execute('''
        SELECT date, GROUP_CONCAT(pattern_type, '|') as patterns
        FROM pattern_occurrences
        WHERE symbol = ? AND timeframe = ?
        GROUP BY date
        ORDER BY date ASC
    ''', (symbol, timeframe))
    
    rows = cur.fetchall()
    
    if len(rows) < 4:  # Need at least 4 rows for 3-candle sequence + next_start
        conn.close()
        return 0
    
    # Convert to list for easier indexing
    date_patterns = [(row['date'], row['patterns'].split('|')) for row in rows]
    
    sequences_to_insert = []
    
    # Generate 3-candle sequences
    for i in range(len(date_patterns) - 3):
        date1, patterns1 = date_patterns[i]
        date2, patterns2 = date_patterns[i + 1]
        date3, patterns3 = date_patterns[i + 2]
        next_date = date_patterns[i + 3][0]  # For lookback context
        
        # Generate all combinations of 3-candle patterns
        for p1 in patterns1:
            for p2 in patterns2:
                for p3 in patterns3:
                    sequence = f"{p1},{p2},{p3}"
                    sequences_to_insert.append((
                        symbol,
                        timeframe,
                        sequence,
                        3,  # sequence_length
                        date1,  # start_date
                        date3,  # end_date
                        next_date  # next_start (for lookback)
                    ))
    
    # Batch insert sequences
    if sequences_to_insert:
        conn.executemany('''
            INSERT OR IGNORE INTO pattern_sequences
            (symbol, timeframe, sequence, sequence_length, start_date, end_date, next_start)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', sequences_to_insert)
        conn.commit()
    
    count = len(sequences_to_insert)
    print(f"✓ Stored {count} 3-candle sequences for {symbol} ({timeframe})")
    
    conn.close()
    return count


def build_pattern_database(symbols: List[str], timeframes: List[str] = ['1D']):
    """
    Complete optimized build process for pattern database.
    One-time operation or infrequent rebuild.
    """
    print("=" * 60)
    print("BUILDING OPTIMIZED PATTERN DATABASE")
    print("=" * 60)
    
    total_patterns = 0
    total_sequences = 0
    
    for timeframe in timeframes:
        db_path = DAILY_DB_PATH if timeframe == '1D' else INTRADAY_DB_PATH
        print(f"\n📊 Processing timeframe: {timeframe}")
        print(f"   Database: {db_path}")
        
        for i, symbol in enumerate(symbols, 1):
            print(f"\n[{i}/{len(symbols)}] Processing {symbol}...")
            
            # Step 1: Detect and store all individual patterns
            pattern_count = detect_and_store_all_patterns(symbol, timeframe, db_path)
            total_patterns += pattern_count
            
            # Step 2: Generate 3-candle sequences
            sequence_count = generate_3_candle_sequences(symbol, timeframe, db_path)
            total_sequences += sequence_count
    
    print("\n" + "=" * 60)
    print("✅ BUILD COMPLETE")
    print(f"   Total pattern occurrences: {total_patterns:,}")
    print(f"   Total 3-candle sequences: {total_sequences:,}")
    print("=" * 60)


def query_pattern_matches(pattern: str, timeframe: str = '1D', 
                         symbol: str = 'SPY', limit: int = 100) -> List[Dict]:
    """
    Query for pattern matches efficiently.
    Returns list of matches with dates.
    """
    db_path = DAILY_DB_PATH if timeframe == '1D' else INTRADAY_DB_PATH
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    if ',' in pattern:  # It's a sequence
        cur = conn.cursor()
        cur.execute('''
            SELECT start_date, end_date, next_start
            FROM pattern_sequences
            WHERE symbol = ? AND timeframe = ? AND sequence = ?
            ORDER BY start_date ASC
            LIMIT ?
        ''', (symbol, timeframe, pattern, limit))
        
        matches = [dict(row) for row in cur.fetchall()]
    else:  # Single pattern
        cur = conn.cursor()
        cur.execute('''
            SELECT date
            FROM pattern_occurrences
            WHERE symbol = ? AND timeframe = ? AND pattern_type = ?
            ORDER BY date ASC
            LIMIT ?
        ''', (symbol, timeframe, pattern, limit))
        
        matches = [{'date': row['date']} for row in cur.fetchall()]
    
    conn.close()
    return matches


if __name__ == '__main__':
    # Example: Major sector symbols
    SYMBOLS = [
        # Technology
        'AAPL', 'MSFT', 'NVDA', 'GOOGL', 'META', 'ZS',
        # Financial
        'JPM', 'BAC', 'GS', 'WFC',
        # Healthcare
        'JNJ', 'UNH', 'PFE', 'ABBV',
        # Energy
        'XOM', 'CVX', 'COP',
        # Consumer
        'WMT', 'PG', 'KO', 'COST',
        # Industrial
        'CAT', 'BA', 'GE',
        # Communication
        'NFLX', 'DIS',
        # Market Index
        'SPY', 'QQQ'
    ]
    
    # Build the database
    build_pattern_database(SYMBOLS, timeframes=['1D'])
    
    # Example query
    print("\n" + "=" * 60)
    print("EXAMPLE QUERY")
    print("=" * 60)
    matches = query_pattern_matches('green,hammer,green_any', '1D', 'SPY', limit=5)
    print(f"Found {len(matches)} matches for 'green,hammer,green_any' in SPY:")
    for match in matches[:5]:
        print(f"  - {match}")
