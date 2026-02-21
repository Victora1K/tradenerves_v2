from __future__ import annotations

import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent

DB_DIR = BACKEND_DIR / 'db'
DATA_DIR = BACKEND_DIR / 'data'

DAILY_DB_PATH = os.getenv('TRADENERVES_DAILY_DB_PATH') or str(DB_DIR / 'stocks.db')
INTRADAY_DB_PATH = os.getenv('TRADENERVES_INTRADAY_DB_PATH') or str(DB_DIR / 'stocks_five.db')
TRADING_DB_PATH = os.getenv('TRADENERVES_TRADING_DB_PATH') or str(BACKEND_DIR / 'trading.db')
