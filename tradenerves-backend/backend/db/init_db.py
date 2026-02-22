# File: /backend/db/init_db.py

import sys
import os
from pathlib import Path
import sqlite3

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import DAILY_DB_PATH

db_path = DAILY_DB_PATH

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
CREATE TABLE IF NOT EXISTS hammer (
    id INTEGER PRIMARY KEY,
    symbol TEXT,
    start_date
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
CREATE TABLE IF NOT EXISTS high_volatility (
    id INTEGER PRIMARY KEY,
    symbol TEXT,
    start_date TEXT,
    end_date TEXT,
    volatility REAL
)
''')

cur.execute('''
CREATE TABLE IF NOT EXISTS double_bottoms (
    id INTEGER PRIMARY KEY,
    symbol TEXT,
    first_bottom_date TEXT,  -- Fixed column names
    second_bottom_date TEXT
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
    sequence_length INTEGER,
    next_start TEXT,
    UNIQUE(symbol, timeframe, sequence, start_date)
)
''')

cur.execute('''
CREATE INDEX IF NOT EXISTS idx_pattern_sequences_lookup
ON pattern_sequences(sequence, timeframe, symbol)
''')

# Commit the changes and close the connection
conn.commit()
conn.close()

print("Database and tables initialized.")
