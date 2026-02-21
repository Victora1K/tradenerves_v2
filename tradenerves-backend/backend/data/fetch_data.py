# data/fetch_data.py
import os
from pathlib import Path
import sqlite3
import requests
from datetime import datetime, timedelta

API_KEY = os.getenv('POLYGON_API_KEY')

SYMBOLS = ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'META', 'ZS', 
           'JPM', 'BAC', 'GS', 'WFC', 'JNJ', 'UNH', 'PFE']

BACKEND_DIR = Path(__file__).resolve().parents[1]
DB_PATH = os.getenv('TRADENERVES_DAILY_DB_PATH') or str(BACKEND_DIR / 'db' / 'stocks.db')

def fetch_polygon_data(symbol, from_date, to_date):
    url = f'https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/{from_date}/{to_date}'
    params = {'apiKey': API_KEY, 'limit': 50000}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return {}

def init_database(conn):
    """Create tables if they don't exist"""
    cur = conn.cursor()
    
    # Create stock_prices table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS stock_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            date TEXT NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume INTEGER,
            UNIQUE(symbol, date)
        )
    ''')
    
    # Create index for faster queries
    cur.execute('''
        CREATE INDEX IF NOT EXISTS idx_stock_prices_symbol_date 
        ON stock_prices(symbol, date)
    ''')
    
    conn.commit()
    print("✓ Database tables initialized")

def populate_database():
    print(f"Using database: {DB_PATH}")
    
    # Ensure db directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Initialize tables FIRST
    init_database(conn)
    
    # Calculate 20 years back
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=20*365)).strftime('%Y-%m-%d')
    
    total_rows = 0
    
    for symbol in SYMBOLS:
        print(f"\nFetching {symbol}...")
        data = fetch_polygon_data(symbol, start_date, end_date)
        
        if 'results' in data:
            rows_added = 0
            for bar in data['results']:
                try:
                    cur.execute('''
                        INSERT OR IGNORE INTO stock_prices 
                        (symbol, date, open, high, low, close, volume)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        symbol,
                        datetime.fromtimestamp(bar['t']/1000).strftime('%Y-%m-%d'),
                        bar['o'], bar['h'], bar['l'], bar['c'], bar['v']
                    ))
                    rows_added += 1
                except Exception as e:
                    print(f"  Error inserting bar: {e}")
            
            conn.commit()
            total_rows += rows_added
            print(f"✓ {symbol}: {rows_added} bars added")
        else:
            print(f"✗ {symbol}: No data returned")
            if 'error' in data:
                print(f"  Error: {data.get('error')}")
    
    conn.close()
    print(f"\n{'='*50}")
    print(f"✅ COMPLETE: {total_rows} total bars added to database")
    print(f"Database: {DB_PATH}")

if __name__ == '__main__':
    populate_database()