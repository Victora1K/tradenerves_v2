import sqlite3
from flask import g
from paths import TRADING_DB_PATH

DATABASE = TRADING_DB_PATH

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            DATABASE,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Initialize the database with required tables"""
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
    
    # Create index for faster queries
    db.execute("""
        CREATE INDEX IF NOT EXISTS idx_historical_queries_symbol 
        ON historical_queries(symbol)
    """)
    
    db.commit()
