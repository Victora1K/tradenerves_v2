from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import os
from data.intra_day import get_intra_day
from data.detect_patterns import (
    detect_double_bottoms,
    detect_hammer,
    calculate_volatility,
    detect_and_store_patterns,
    detect_pattern_sequence_next_start,
    detect_pattern_sequence_windows
)
# Intraday imports disabled - uncomment when stocks_five.db is populated
# from data.detect_green_five import detect_and_store_patterns as detect_patterns_five
# from data.fetch_data_five import fetch_and_store_stock_data as fetch_five_min
from data.fetch_data import populate_database as fetch_daily

# Import new optimized routes (v2 API)
from routes.optimized_patterns import optimized_patterns_bp

import requests
from datetime import datetime, timedelta, timezone
from collections import OrderedDict
import random
import threading
from paths import DAILY_DB_PATH, INTRADAY_DB_PATH, TRADING_DB_PATH

# API Key for Polygon.io
API_KEY = 'gNUdx8Rrob9OtDQSGK9EBX7K179qpNjQ'  # Test API Key

app = Flask(__name__)
CORS(app)  # Enable CORS for the entire Flask app

# Register optimized patterns blueprint (v2 API - coexists with existing routes)
app.register_blueprint(optimized_patterns_bp)

# Path to the database
db_path = DAILY_DB_PATH
five_db_path = INTRADAY_DB_PATH

#init_db_day()

def get_db_connection():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_db():
    conn = sqlite3.connect(TRADING_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_five_db():
    conn = sqlite3.connect(five_db_path)
    conn.row_factory = sqlite3.Row
    return conn


INTRADAY_DB_FMT = '%Y-%m-%d-%H:%M'
INTRADAY_ISO_FMT = '%Y-%m-%dT%H:%M'
TIMEFRAME_ALIASES = {
    '1d': '1D',
    '1day': '1D',
    'day': '1D',
    'd': '1D',
    '1D': '1D',
    '5m': '5m',
    '5min': '5m',
    '5minute': '5m',
    '10m': '10m',
    '10min': '10m',
    '15m': '15m',
    '15min': '15m',
    '1h': '1h',
    '60m': '1h',
    '60min': '1h',
    'hour': '1h',
    '1hour': '1h'
}

PATTERN_ALIASES = {
    'solid_green': 'green',
    'doji_red': 'red_doji',
    'bearish': 'red',
    'bullish': 'green_any'
}


def normalize_timeframe(value):
    if not value:
        return '1D'
    key = str(value).strip().lower()
    return TIMEFRAME_ALIASES.get(key, '1D')


def normalize_pattern_key(value):
    key = str(value or '').strip().lower()
    return PATTERN_ALIASES.get(key, key)


def timeframe_minutes(timeframe):
    return {
        '5m': 5,
        '10m': 10,
        '15m': 15,
        '1h': 60
    }.get(timeframe)


def to_intraday_iso(date_str):
    return datetime.strptime(date_str, INTRADAY_DB_FMT).strftime(INTRADAY_ISO_FMT)


def parse_intraday_timestamp(value):
    if not value:
        return None
    for fmt in (INTRADAY_ISO_FMT, INTRADAY_DB_FMT, '%Y-%m-%d'):
        try:
            dt = datetime.strptime(value, fmt)
            if fmt == '%Y-%m-%d':
                dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
            return dt
        except ValueError:
            continue
    return None


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


def get_timeframe_bars(symbol, timeframe):
    tf = normalize_timeframe(timeframe)
    if tf == '1D':
        conn = get_db_connection()
    else:
        conn = get_five_db()

    cur = conn.cursor()
    cur.execute(
        'SELECT date, open, high, low, close, volume FROM stock_prices WHERE symbol = ? ORDER BY date ASC',
        (symbol,)
    )
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return []

    if tf == '1D':
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

    if tf == '5m':
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

    minutes = timeframe_minutes(tf)
    return aggregate_intraday_rows(rows, minutes)


def filter_bars_after_timestamp(bars, timestamp, timeframe, lookback=0):
    if not timestamp:
        return bars

    try:
        lookback = max(int(lookback or 0), 0)
    except (TypeError, ValueError):
        lookback = 0

    ts_dt = parse_intraday_timestamp(timestamp)
    if not ts_dt:
        try:
            ts_dt = datetime.strptime(timestamp.split('T')[0], '%Y-%m-%d')
        except ValueError:
            return bars

    for idx, bar in enumerate(bars):
        bar_dt = parse_intraday_timestamp(bar.get('date'))
        if not bar_dt:
            try:
                bar_dt = datetime.strptime(str(bar.get('date')).split('T')[0], '%Y-%m-%d')
            except ValueError:
                bar_dt = None
        if bar_dt and bar_dt >= ts_dt:
            start_idx = max(0, idx - lookback) if lookback else idx
            return bars[start_idx:]

    return []


def get_sequence_db(timeframe):
    tf = normalize_timeframe(timeframe)
    return get_db_connection() if tf == '1D' else get_five_db()


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


def fetch_sequence_match(cur, sequence_key, timeframe, symbol=None):
    if symbol:
        cur.execute(
            'SELECT symbol, next_start FROM pattern_sequences '
            'WHERE sequence = ? AND timeframe = ? AND symbol = ? '
            'ORDER BY RANDOM() LIMIT 1',
            (sequence_key, timeframe, symbol)
        )
    else:
        cur.execute(
            'SELECT symbol, next_start FROM pattern_sequences '
            'WHERE sequence = ? AND timeframe = ? '
            'ORDER BY RANDOM() LIMIT 1',
            (sequence_key, timeframe)
        )
    return cur.fetchone()


def store_sequence_matches(conn, symbol, timeframe, sequence_key, matches):
    if not matches:
        return
    rows = [
        (
            symbol,
            timeframe,
            sequence_key,
            match['start_date'],
            match['end_date'],
            match['next_start']
        )
        for match in matches
    ]
    conn.executemany(
        '''
        INSERT OR IGNORE INTO pattern_sequences
        (symbol, timeframe, sequence, start_date, end_date, next_start)
        VALUES (?, ?, ?, ?, ?, ?)
        ''',
        rows
    )
    conn.commit()


def get_symbols_for_timeframe(timeframe):
    tf = normalize_timeframe(timeframe)
    conn = get_db_connection() if tf == '1D' else get_five_db()
    cur = conn.cursor()
    cur.execute('SELECT symbol FROM stock_prices GROUP BY symbol')
    symbols = [row['symbol'] for row in cur.fetchall()]
    conn.close()
    return symbols

# Initialize database and fetch data
def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS historical_queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            query_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.execute("""
        CREATE INDEX IF NOT EXISTS idx_historical_queries_symbol 
        ON historical_queries(symbol)
    """)
    db.commit()

        


def fetch_all_data():
    symbols = [
        'SPY',
        'AAPL', 'NVDA', 'TSLA', 'MSFT', 'GOOGL', 'AMZN',  # Technology
        'JPM', 'BAC', 'WFC', 'GS', 'AXP',  # Banking
        'JNJ', 'UNH', 'PFE',  # Healthcare
        'XOM', 'CVX', 'COP',  # Energy
        'WMT', 'PG', 'KO',  # Consumer
        'META', 'NFLX', 'ADBE',  # Internet/Software
        'AAL', 'PLTR', 'FTNT', 'PANW', 'ZS' #Security & Interests
    ]

    print("Starting data fetch and pattern detection...")
    
    # Fetch daily data and detect patterns
    for symbol in symbols:
        try:
            print(f"Fetching daily data for {symbol}...")
            fetch_daily(symbol)
            print(f"Detecting patterns for {symbol}...")
            detect_and_store_patterns(symbol)
        except Exception as e:
            print(f"Error processing daily data for {symbol}: {str(e)}")

    # Fetch 5-minute data
    # for symbol in symbols:
    #     try:
    #         print(f"Fetching 5-minute data for {symbol}...")
    #         fetch_five_min(symbol)
    #         print(f"Detecting 5-minute patterns for {symbol}...")
    #         detect_patterns_five(symbol)
    #     except Exception as e:
    #         print(f"Error processing 5-minute data for {symbol}: {str(e)}")

    print("Data fetch and pattern detection completed!")

# Initialize database and start data fetch in background
with app.app_context():
    init_db()
    # Start data fetch in a background thread
    threading.Thread(target=fetch_all_data, daemon=True).start()

# Register database close function
def close_db(e=None):
    db = get_db()
    db.close()

app.teardown_appcontext(close_db)

@app.route('/api/historical/<symbol>/<start_date>/<end_date>')
def get_historical_data(symbol, start_date, end_date):
    try:
        # Basic validation
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            if start > end:
                return jsonify({'error': 'Start date must be before end date'}), 400
            if (end - start).days > 365:
                return jsonify({'error': 'Date range cannot exceed 1 year'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

        # Fetch data from Polygon.io
        url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/{start_date}/{end_date}?apiKey={API_KEY}"
        response = requests.get(url)
        
        if response.status_code != 200:
            return jsonify({'error': f'API request failed with status {response.status_code}'}), 500

        data = response.json().get('results', [])
        if not data:
            return jsonify({'error': 'No data found for the specified date range'}), 404

        # Format the response
        formatted_data = []
        for entry in data:
            timestamp = datetime.fromtimestamp(entry['t'] / 1000).strftime('%Y-%m-%d')
            formatted_data.append({
                'date': timestamp,
                'open': float(entry['o']) if 'o' in entry and entry['o'] is not None else 0.0,
                'high': float(entry['h']) if 'h' in entry and entry['h'] is not None else 0.0,
                'low': float(entry['l']) if 'l' in entry and entry['l'] is not None else 0.0,
                'close': float(entry['c']) if 'c' in entry and entry['c'] is not None else 0.0,
                'volume': int(entry['v']) if 'v' in entry and entry['v'] is not None else 0
            })

        # Sort by date
        formatted_data.sort(key=lambda x: x['date'])

        # Log the query
        db = get_db()
        db.execute(
            'INSERT INTO historical_queries (symbol, start_date, end_date) VALUES (?, ?, ?)',
            (symbol, start_date, end_date)
        )
        db.commit()

        return jsonify(formatted_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stock_prices/<symbol>/<timestamp>', methods=['GET'])
def get_stock_data_from_timestamp(symbol, timestamp):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Fetch stock data from the given timestamp onwards
        cur.execute('''
            SELECT date, open, high, low, close, volume
            FROM stock_prices
            WHERE symbol = ? AND date >= ?
            ORDER BY date ASC
        ''', (symbol, timestamp))
        
        rows = cur.fetchall()
        conn.close()

        if rows:
            results = [
                {
                    'date': row['date'],
                    'open': row['open'],
                    'high': row['high'],
                    'low': row['low'],
                    'close': row['close'],
                    'volume': row['volume']
                }
                for row in rows
            ]
            return jsonify(results)
        else:
            return jsonify({'error': 'No stock data found from this timestamp'}), 404
    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500


@app.route('/api/stock_prices_timeframe/<symbol>/<timestamp>', methods=['GET'])
def get_stock_data_from_timestamp_timeframe(symbol, timestamp):
    try:
        timeframe = normalize_timeframe(request.args.get('timeframe') or request.args.get('tf'))
        lookback = request.args.get('lookback')
        bars = get_timeframe_bars(symbol, timeframe)
        if not bars:
            return jsonify({'error': 'No stock data found'}), 404

        filtered = filter_bars_after_timestamp(bars, timestamp, timeframe, lookback=lookback)
        if filtered:
            return jsonify(filtered)
        return jsonify({'error': 'No stock data found from this timestamp'}), 404
    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/api/stock_prices_intra/<symbol>/<timestamp>', methods=['GET'])
def get_stock_intra_from_timestamp(symbol, timestamp):
    try:
        rows = get_intra_day(symbol, timestamp)
        
        if rows:
            results = [
                {
                    'date': datetime.fromtimestamp(row['t'] / 1000, timezone.utc).strftime('%y/%m/%d-%H:%M'),
                    'open': row['o'],
                    'high': row['h'],
                    'low': row['l'],
                    'close': row['c'],
                    'volume': row['v']
                }
                for row in rows
            ]
            return jsonify(results)
        else:
            return jsonify({'error': 'No stock data found from this timestamp'}), 404
    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500

# Random Stock and Timestamp API
@app.route('/api/random_stock', methods=['GET'])
def random_stock():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Select a random stock symbol
        cur.execute('SELECT symbol FROM stock_prices GROUP BY symbol ORDER BY RANDOM() LIMIT 1')
        stock_row = cur.fetchone()
        
        if stock_row:
            symbol = stock_row['symbol']
            
            # Select a random timestamp for that stock
            cur.execute('SELECT date FROM stock_prices WHERE symbol = ? ORDER BY RANDOM() LIMIT 1', (symbol,))
            timestamp_row = cur.fetchone()

            conn.close()
            
            if timestamp_row:
                return jsonify({
                    'symbol': symbol,
                    'timestamp': timestamp_row['date']
                })
            else:
                return jsonify({'error': 'No timestamp found for this stock'}), 404
        else:
            return jsonify({'error': 'No stock found'}), 404
    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500


# High Volatility Stocks API
@app.route('/api/stocks/high_volatility', methods=['GET'])
def high_volatility_stocks():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Select a random high volatility period
        cur.execute('SELECT symbol, start_date FROM high_volatility ORDER BY RANDOM() LIMIT 1')
        volatility_row = cur.fetchone()
        
        if volatility_row:
            symbol = volatility_row['symbol']
            start_date = volatility_row['start_date']
            
            # Send the start date instead of row index
            return jsonify({'symbol': symbol, 'timestamp': start_date})
        else:
            return jsonify({'error': 'No high volatility periods found'}), 404
    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500


# Double Bottom Stocks API
@app.route('/api/stocks/double_bottoms', methods=['GET'])
def double_bottom_stocks():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Select a random double bottom pattern
        cur.execute('SELECT symbol, first_bottom_date FROM double_bottoms ORDER BY RANDOM() LIMIT 1')
        double_bottom_row = cur.fetchone()
        
        if double_bottom_row:
            symbol = double_bottom_row['symbol']
            first_bottom_date = double_bottom_row['first_bottom_date']
            
            # Send the date instead of row index
            return jsonify({'symbol': symbol, 'timestamp': first_bottom_date})
        else:
            return jsonify({'error': 'No double bottom patterns found'}), 404
    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500


#Hammer API 
@app.route('/api/stocks/hammer', methods=['GET'])
def hammer_stocks():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        #Select Hammer pattern
        cur.execute('SELECT symbol, start_date FROM hammer ORDER BY RANDOM() LIMIT 1')
        hammer_row = cur.fetchone()
        
        if hammer_row:
            symbol = hammer_row['symbol']
            hammer_date = hammer_row['start_date']
            
            return jsonify({'symbol': symbol, 'timestamp': hammer_date})
        else:
            return jsonify({'error': 'No hammer patterns found'}), 404
    except Exception as e:
        print(f"Error occured: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500
        
        
#Green day API 
@app.route('/api/stocks/green', methods=['GET'])
def green_stocks():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
            
            #Select green pattern
        cur.execute('SELECT symbol, start_date FROM green ORDER BY RANDOM() LIMIT 1')
        green_row = cur.fetchone()
            
        if green_row:
            symbol = green_row['symbol']
            green_date = green_row['start_date']
                
            return jsonify({'symbol': symbol, 'timestamp': green_date})
        else:
            return jsonify({'error': 'No green patterns found'}), 404
    except Exception as e:
        print(f"Error occured: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500
    
    
#Green_five day API 
@app.route('/api/stocks/green_five', methods=['GET'])
def green_five_stocks():
    try:
        conn = get_five_db()
        cur = conn.cursor()
            
            #Select green pattern
        cur.execute('SELECT symbol, start_date FROM green ORDER BY RANDOM() LIMIT 1')
        green_row = cur.fetchone()
            
        if green_row:
            symbol = green_row['symbol']
            green_date = datetime.strptime(green_row['start_date'], '%Y-%m-%d-%H:%M').strftime('%Y-%m-%d')
                
            return jsonify({'symbol': symbol, 'timestamp': green_date})
        else:
            return jsonify({'error': 'No green patterns found'}), 404
    except Exception as e:
        print(f"Error occured: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500


@app.route('/api/stocks/sequence', methods=['GET'])
def sequence_stocks():
    try:
        raw_seq = request.args.get('seq')
        symbol = request.args.get('symbol')
        timeframe = normalize_timeframe(request.args.get('timeframe') or request.args.get('tf'))

        if not raw_seq:
            return jsonify({'error': 'Missing required query param: seq'}), 400

        sequence = [normalize_pattern_key(p) for p in raw_seq.split(',') if p.strip()]
        if not sequence:
            return jsonify({'error': 'Invalid seq'}), 400

        sequence_key = ','.join(sequence)
        seq_conn = get_sequence_db(timeframe)
        ensure_pattern_sequences_table(seq_conn)
        seq_cur = seq_conn.cursor()

        cached = fetch_sequence_match(seq_cur, sequence_key, timeframe, symbol)
        if cached:
            result_symbol = cached['symbol'] if isinstance(cached, sqlite3.Row) else cached[0]
            result_timestamp = cached['next_start'] if isinstance(cached, sqlite3.Row) else cached[1]
            seq_conn.close()
            return jsonify({'symbol': result_symbol, 'timestamp': result_timestamp})

        def find_match_for_symbol(sym):
            bars = get_timeframe_bars(sym, timeframe)
            if not bars:
                return None
            formatted = [
                (bar['date'], float(bar['open']), float(bar['high']), float(bar['low']), float(bar['close']))
                for bar in bars
            ]
            matches = detect_pattern_sequence_windows(formatted, sequence)
            if not matches:
                return None
            store_sequence_matches(seq_conn, sym, timeframe, sequence_key, matches)
            return random.choice(matches)['next_start']

        if symbol:
            timestamp = find_match_for_symbol(symbol)
            seq_conn.close()
            if not timestamp:
                return jsonify({'error': 'No matches found for symbol/sequence'}), 404
            return jsonify({'symbol': symbol, 'timestamp': timestamp})

        symbols = get_symbols_for_timeframe(timeframe)
        random.shuffle(symbols)

        for sym in symbols[:250]:
            timestamp = find_match_for_symbol(sym)
            if timestamp:
                seq_conn.close()
                return jsonify({'symbol': sym, 'timestamp': timestamp})

        seq_conn.close()

        return jsonify({'error': 'No matches found for sequence'}), 404

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Error occured: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint for Docker and monitoring"""
    return jsonify({'status': 'healthy', 'service': 'tradenerves-backend'}), 200

if __name__ == '__main__':
    app.run(debug=True)
