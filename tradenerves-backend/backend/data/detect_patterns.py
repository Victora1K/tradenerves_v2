import os
import sqlite3
import numpy as np
from pathlib import Path

# Path to the database
BACKEND_DIR = Path(__file__).resolve().parents[1]
db_path = os.getenv('TRADENERVES_DAILY_DB_PATH') or str(BACKEND_DIR / 'db' / 'stocks.db')


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

    # close should be near the high (small upper wick)
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

    # Typical hammer shape: small body near the high, long lower wick, small upper wick.
    if (body / full_range) > body_to_range_max:
        return False
    if (lower_wick / body) < lower_wick_to_body_min:
        return False
    if (upper_wick / body) > upper_wick_to_body_max:
        return False

    # Body should be in the upper portion of the candle
    if max(open_price, close_price) < (low_price + (0.6 * full_range)):
        return False

    return True


def candle_is_doji(open_price, high_price, low_price, close_price, body_to_range_max=0.1, body_abs_max=None):
    body, upper_wick, lower_wick, full_range = _candle_parts(open_price, high_price, low_price, close_price)

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


def detect_pattern_sequence(rows, sequence):
    """Find occurrences of a consecutive candle pattern sequence.

    rows: iterable of (date, open, high, low, close) ordered ascending by date.
    sequence: list[str] pattern keys.

    Returns list[str] of start dates for each match.
    """
    seq = [s.strip() for s in (sequence or []) if str(s).strip()]
    if not seq:
        return []

    window = len(seq)
    if len(rows) < window:
        return []

    matches = []
    for i in range(0, len(rows) - window + 1):
        ok = True
        for j, pattern_key in enumerate(seq):
            date, open_price, high_price, low_price, close_price = rows[i + j]
            if not candle_matches_pattern(pattern_key, open_price, high_price, low_price, close_price):
                ok = False
                break
        if ok:
            matches.append(rows[i][0])
    return matches


def detect_pattern_sequence_next_start(rows, sequence):
    """Like detect_pattern_sequence, but returns the date of the candle immediately AFTER the matched window.

    This is useful when you want the pattern/sequence to be fully visible *before* the simulated playback starts.
    """
    seq = [s.strip() for s in (sequence or []) if str(s).strip()]
    if not seq:
        return []

    window = len(seq)
    if len(rows) <= window:
        return []

    next_starts = []
    for i in range(0, len(rows) - window):
        ok = True
        for j, pattern_key in enumerate(seq):
            date, open_price, high_price, low_price, close_price = rows[i + j]
            if not candle_matches_pattern(pattern_key, open_price, high_price, low_price, close_price):
                ok = False
                break
        if ok:
            next_starts.append(rows[i + window][0])
    return next_starts


def detect_pattern_sequence_windows(rows, sequence):
    """Return matches with start/end/next candle dates for a sequence.

    rows: iterable of (date, open, high, low, close) ordered ascending by date.
    sequence: list[str] pattern keys.
    """
    seq = [s.strip() for s in (sequence or []) if str(s).strip()]
    if not seq:
        return []

    window = len(seq)
    if len(rows) <= window:
        return []

    matches = []
    for i in range(0, len(rows) - window):
        ok = True
        for j, pattern_key in enumerate(seq):
            date, open_price, high_price, low_price, close_price = rows[i + j]
            if not candle_matches_pattern(pattern_key, open_price, high_price, low_price, close_price):
                ok = False
                break
        if ok:
            matches.append({
                'start_date': rows[i][0],
                'end_date': rows[i + window - 1][0],
                'next_start': rows[i + window][0]
            })
    return matches

#collects prices list from database
def calculate_volatility(prices, period=14):
    #np.diff subtracts index value i from i+1 and returns a list i.e. np.diff[ 2 3 5] returns [1 2] & prices[:-1] returns all
    #except the last value of prices list or array
    daily_returns = np.diff(prices) / prices[:-1]
    volatility = np.std(daily_returns[-period:])
    return volatility

def is_valid_low(prices):
    low_price = []
    low_index = []
    valid_lows = []
    for i in range(2,len(prices) - 2):
                # Detect a potential bottom: price is lower than the previous and next day
        if prices[i-1] < prices[i-2] and prices[i] <= prices[i-1] and prices[i] < prices[i+1] and prices[i+1] <= prices[i+2]:
            low_price.append(prices[i])
            low_index.append(i)
            
    valid_lows.append((low_index))  
    #print(f"{valid_lows} are lows fed to valid lows")      
    #print(f"{low_index} are lows fed to low index")
    return low_index
    
    
#hammer detection function uses valid lows to see if they also meet a wick structure pattern
def detect_hammer(prices, prices_close, prices_high, prices_open, dates, symbol):
    valid_hammers = []
    check_for_lows = is_valid_low(prices)
    #print(f"{check_for_lows} are lows fed to hammer for symbol {symbol}")
    #low_prices = check_for_lows[0]
    #low_indices = check_for_lows[1]
    if check_for_lows:
        low_check_prices = check_for_lows[0]
        for i in range(1,len(check_for_lows)):
            open = prices_open[check_for_lows[i]]
            close = prices_close[check_for_lows[i]]
            high = prices_high[check_for_lows[i]]
            low = prices[check_for_lows[i]]
            date = dates[check_for_lows[i]]
            body = abs(close - open)
            wick = abs(high - low)
            if (wick > 1.25 * body and (open == high or close == high)):
                valid_hammers.append((symbol, date))
            else:
                print(f"{prices[i]} is a low but not a hammer. ")
    else: 
        valid_hammers = []  #Because there's no lows.
        # Return the list of double bottom pairs (if any)
    if len(valid_hammers) > 0:
        #print(f"Valid hammers found: {valid_hammers}")
        return valid_hammers
    else:
        print(f"No Valid hammers found.")
        return []    
    
    
    

# Updated double bottom detection to handle multiple bottoms and return the symbol
def detect_double_bottoms(prices, dates, symbol, tolerance=0.0000125):
    double_bottoms = []  # To store multiple pairs of double bottoms (tuples of symbol, start and end dates)
    current_bottom = None  # Track the current lowest bottom
    bottom_index = []
    #bottom_price = []
    
    check_for_lows = is_valid_low(prices)
    #print(f"{check_for_lows} are lows fed to double_bottom for symbol {symbol}")
    
    

        # Detect a potential bottom: price is lower than the previous and next day
    if check_for_lows:
            low_check_prices = check_for_lows
            print(f"{low_check_prices} are lows zero index fed to double_bottom for symbol {symbol}")
            for bottom in range(2,len(low_check_prices)-2):
                for second_bottom in range(bottom + 1, len(low_check_prices) -2):
                    #price_difference = abs(low_check_prices[bottom] - low_check_prices[second_bottom]) / low_check_prices[bottom]
                    price_difference = abs(prices[low_check_prices[bottom]] - prices[low_check_prices[second_bottom]]) / prices[low_check_prices[bottom]]
                    
                    if price_difference <= tolerance and second_bottom - bottom >= 5:
                        #print(f"{low_check_prices[bottom]} and {low_check_prices[second_bottom]} are lows. ")
                        if low_check_prices[bottom] not in double_bottoms :
                            #print(f"Price difference: {price_difference}, Tolerance: {tolerance}")                  
                            #print(f"Double bottom confirmed between indices {bottom} and {second_bottom}")
                            #print(f"Double bottom match between prices {bottom_price[bottom]} and {bottom_price[second_bottom]}")
                            #print(f"Double bottom confirmed between indices {bottom} and {second_bottom} already in list")
                            double_bottoms.append((symbol, dates[bottom], dates[second_bottom]))
                        else:
                            print(f"Bottom at index {bottom} does not meet criteria (tolerance or distance).")
                            # Re-assign this as the new potential first bottom
    else:
        low_check_prices = None
                                                
    
    # Return the list of double bottom pairs (if any)
    if len(double_bottoms) > 0:
        #print(f"Double bottoms found: {double_bottoms}")
        return double_bottoms
    else:
        #print(f"No double bottoms found.")
        return []
    
def detect_green(prices, prices_close, prices_high, prices_open, dates, symbol):
    valid_greens = []
    print(f"All prices {len(prices)}")
    for candle in range(len(prices)-1):
        #print(f"{prices[candle]} occured at date: {dates[candle]}")
        if prices_close[candle] - prices_open[candle] > 4 and prices_high[candle] - prices_close[candle] < 0.28:
            valid_greens.append((symbol , dates[candle]))
            #print(f"Appending {dates[candle]} and {symbol} ticker to valid greens. ")
            #print(f"Found a green day at date: {dates[candle]}")
    if len(valid_greens) > 0:
        #print(f"Valid green days found: {valid_greens}")
        print(len(valid_greens))
    return valid_greens

def detect_and_store_patterns(symbol):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Fetch low prices and dates for the symbol
    cur.execute(f"SELECT low, date, close, high, open FROM stock_prices WHERE symbol = ? ORDER BY date ASC", (symbol,))
    rows = cur.fetchall()

    prices = [row[0] for row in rows]  # Using low prices    
    dates = [row[1] for row in rows]
    prices_close = [row[2] for row in rows]
    prices_high = [row[3] for row in rows]
    prices_open = [row[4] for row in rows]


    # Detect high volatility periods
    for i in range(14, len(prices), 3):
        lows = prices[i-14:i]  # Using low prices for volatility calculation
        volatility = calculate_volatility(lows)
        if volatility > 0.02:  # Threshold for high volatility
            cur.execute('''
                INSERT INTO high_volatility (symbol, start_date, end_date, volatility)
                VALUES (?, ?, ?, ?)
            ''', (symbol, dates[i-14], dates[i], volatility))

    # Detect double bottoms
    double_bottoms = detect_double_bottoms(prices, dates, symbol, tolerance=0.0028)
    if double_bottoms:
        for (symbol, first_bottom_date, second_bottom_date) in double_bottoms:
            cur.execute('''
                INSERT INTO double_bottoms (symbol, first_bottom_date, second_bottom_date)
                VALUES (?, ?, ?)
            ''', (symbol, first_bottom_date, second_bottom_date))
            
    #Detect hammer pattern and occurences
    hammer_results = detect_hammer(prices, prices_close, prices_high, prices_open, dates, symbol)
    if hammer_results:
        for (symbol, start_date) in hammer_results:
            cur.execute('''
                    INSERT INTO hammer (symbol, start_date)
                    VALUES (?,?)
                    ''',(symbol, start_date))
    green_days = detect_green(prices, prices_close, prices_high, prices_open, dates, symbol)
    if green_days:
        for (symbol, start_date) in green_days:
            cur.execute('''
                        INSERT INTO green (symbol, start_date)
                        VALUES (?,?)
                        ''',(symbol, start_date))
            

    conn.commit()
    conn.close()

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

for symbol in symbols:
    detect_and_store_patterns(symbol)

print("Patterns detected and stored.")
