# File: /backend/db/init_five_db.py

import sys
import os
from pathlib import Path
import sqlite3

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import INTRADAY_DB_PATH

db_path = INTRADAY_DB_PATH

# Connect to the database using the absolute path
conn = sqlite3.connect(db_path)

# Create cursor
cur = conn.cursor()

# Create tables
cur.execute('''
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

cur.execute('''
CREATE TABLE IF NOT EXISTS green (
    id INTEGER PRIMARY KEY,
    symbol TEXT,
    start_date
)
''')

cur.execute('''
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

cur.execute('''
CREATE INDEX IF NOT EXISTS idx_pattern_sequences_lookup
ON pattern_sequences(sequence, timeframe, symbol)
''')

conn.commit()
conn.close()