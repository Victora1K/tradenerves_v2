"""
Optimized API endpoints for pattern queries with lookback context.
Designed for efficient SQLite queries and minimal data transfer.
"""

from flask import Blueprint, jsonify, request
import sqlite3
from paths import DAILY_DB_PATH, INTRADAY_DB_PATH

optimized_patterns_bp = Blueprint('optimized_patterns', __name__)

TIMEFRAME_MAP = {
    '1d': '1D', '1day': '1D', 'day': '1D', 'd': '1D', '1D': '1D',
    '5m': '5m', '10m': '10m', '15m': '15m', '1h': '1h'
}


def normalize_timeframe(tf):
    """Normalize timeframe input"""
    return TIMEFRAME_MAP.get(str(tf).lower().strip(), '1D')


def get_db_for_timeframe(timeframe):
    """Get appropriate database connection"""
    db_path = DAILY_DB_PATH if timeframe == '1D' else INTRADAY_DB_PATH
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


@optimized_patterns_bp.route('/api/v2/patterns/matches', methods=['GET'])
def get_pattern_matches():
    """
    Get all matches for a pattern or sequence.
    
    Query params:
    - pattern: Pattern key or comma-separated sequence (e.g., 'green,hammer,doji')
    - symbol: Stock symbol (default: SPY)
    - timeframe: Timeframe (default: 1D)
    - limit: Max results (default: 100)
    
    Returns:
    {
        "symbol": "SPY",
        "timeframe": "1D",
        "pattern": "green,hammer,doji",
        "match_count": 15,
        "matches": [
            {"start_date": "2020-01-15", "end_date": "2020-01-17", "next_start": "2020-01-18"},
            ...
        ]
    }
    """
    pattern = request.args.get('pattern', '').strip()
    symbol_param = request.args.get('symbol', 'any').strip().upper()
    timeframe = normalize_timeframe(request.args.get('timeframe', '1D'))
    limit = min(int(request.args.get('limit', 100)), 1000)
    
    if not pattern:
        return jsonify({'error': 'Pattern parameter required'}), 400
    
    try:
        conn = get_db_for_timeframe(timeframe)
        cur = conn.cursor()
        
        # Dynamic symbol selection - pick any symbol with matches
        if symbol_param == 'ANY' or symbol_param == '':
            if ',' in pattern:  # Sequence query
                # Get a random symbol that has this sequence
                cur.execute('''
                    SELECT symbol, COUNT(*) as count
                    FROM pattern_sequences
                    WHERE timeframe = ? AND sequence = ?
                    GROUP BY symbol
                    HAVING count > 0
                    ORDER BY RANDOM()
                    LIMIT 1
                ''', (timeframe, pattern))
                
                result = cur.fetchone()
                if result:
                    symbol = result['symbol']
                else:
                    return jsonify({
                        'error': f'No matches found for pattern: {pattern}',
                        'pattern': pattern,
                        'timeframe': timeframe
                    }), 404
            else:  # Single pattern query
                # Get a random symbol that has this pattern
                cur.execute('''
                    SELECT symbol, COUNT(*) as count
                    FROM pattern_occurrences
                    WHERE timeframe = ? AND pattern_type = ?
                    GROUP BY symbol
                    HAVING count > 0
                    ORDER BY RANDOM()
                    LIMIT 1
                ''', (timeframe, pattern))
                
                result = cur.fetchone()
                if result:
                    symbol = result['symbol']
                else:
                    return jsonify({
                        'error': f'No matches found for pattern: {pattern}',
                        'pattern': pattern,
                        'timeframe': timeframe
                    }), 404
        else:
            symbol = symbol_param
        
        # Now fetch matches for the selected symbol
        if ',' in pattern:  # Sequence query
            cur.execute('''
                SELECT start_date, end_date, next_start
                FROM pattern_sequences
                WHERE symbol = ? AND timeframe = ? AND sequence = ?
                ORDER BY start_date DESC
                LIMIT ?
            ''', (symbol, timeframe, pattern, limit))
            
            matches = [dict(row) for row in cur.fetchall()]
        else:  # Single pattern query
            cur.execute('''
                SELECT date as start_date
                FROM pattern_occurrences
                WHERE symbol = ? AND timeframe = ? AND pattern_type = ?
                ORDER BY date DESC
                LIMIT ?
            ''', (symbol, timeframe, pattern, limit))
            
            matches = [dict(row) for row in cur.fetchall()]
        
        conn.close()
        
        return jsonify({
            'symbol': symbol,
            'timeframe': timeframe,
            'pattern': pattern,
            'match_count': len(matches),
            'matches': matches
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@optimized_patterns_bp.route('/api/v2/data/with-lookback', methods=['GET'])
def get_data_with_lookback():
    """
    Get OHLCV data with lookback bars before a start date.
    
    Query params:
    - symbol: Stock symbol (required)
    - start_date: Start date for pattern (required)
    - timeframe: Timeframe (default: 1D)
    - lookback: Number of bars to include before start_date (default: 50)
    - forward: Number of bars to include after start_date (default: 100)
    
    Returns:
    {
        "symbol": "SPY",
        "timeframe": "1D",
        "start_date": "2020-01-15",
        "lookback_bars": 50,
        "forward_bars": 100,
        "data": [
            {"date": "2019-11-01", "open": 300.5, "high": 302.1, ...},
            ...
        ]
    }
    """
    symbol = request.args.get('symbol', '').upper()
    start_date = request.args.get('start_date', '').strip()
    timeframe = normalize_timeframe(request.args.get('timeframe', '1D'))
    lookback = int(request.args.get('lookback', 50))
    forward = int(request.args.get('forward', 100))
    
    if not symbol or not start_date:
        return jsonify({'error': 'symbol and start_date parameters required'}), 400
    
    try:
        conn = get_db_for_timeframe(timeframe)
        cur = conn.cursor()
        
        # Debug: Check what data exists for this symbol
        cur.execute('SELECT COUNT(*), MIN(date), MAX(date) FROM stock_prices WHERE symbol = ?', (symbol,))
        debug_info = cur.fetchone()
        print(f"DEBUG: Symbol {symbol} has {debug_info[0]} rows, dates {debug_info[1]} to {debug_info[2]}")
        print(f"DEBUG: Requesting data for start_date={start_date}, lookback={lookback}, forward={forward}")
        
        # Use window functions for efficient lookback/forward selection
        query = '''
            WITH indexed AS (
                SELECT 
                    date, open, high, low, close, volume,
                    ROW_NUMBER() OVER (ORDER BY date ASC) as rn
                FROM stock_prices
                WHERE symbol = ?
            ),
            target_row AS (
                SELECT rn FROM indexed WHERE date >= ? LIMIT 1
            )
            SELECT date, open, high, low, close, volume
            FROM indexed
            WHERE rn >= (SELECT rn FROM target_row) - ?
              AND rn < (SELECT rn FROM target_row) + ?
            ORDER BY date ASC
        '''
        
        cur.execute(query, (symbol, start_date, lookback, forward))
        rows = cur.fetchall()
        print(f"DEBUG: Query returned {len(rows)} rows")
        
        data = [dict(row) for row in rows]
        conn.close()
        
        return jsonify({
            'symbol': symbol,
            'timeframe': timeframe,
            'start_date': start_date,
            'lookback_bars': lookback,
            'forward_bars': forward,
            'total_bars': len(data),
            'data': data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@optimized_patterns_bp.route('/api/v2/patterns/available', methods=['GET'])
def get_available_patterns():
    """
    Get list of available patterns and their occurrence counts.
    
    Query params:
    - symbol: Stock symbol (optional, default: all symbols)
    - timeframe: Timeframe (default: 1D)
    
    Returns:
    {
        "timeframe": "1D",
        "patterns": {
            "green": 1250,
            "hammer": 324,
            "doji": 892,
            ...
        },
        "sequences": {
            "green,hammer,doji": 45,
            "hammer,green,green_any": 67,
            ...
        }
    }
    """
    symbol = request.args.get('symbol', '').upper() or None
    timeframe = normalize_timeframe(request.args.get('timeframe', '1D'))
    
    try:
        conn = get_db_for_timeframe(timeframe)
        cur = conn.cursor()
        
        # Get single pattern counts
        if symbol:
            cur.execute('''
                SELECT pattern_type, COUNT(*) as count
                FROM pattern_occurrences
                WHERE symbol = ? AND timeframe = ?
                GROUP BY pattern_type
                ORDER BY count DESC
            ''', (symbol, timeframe))
        else:
            cur.execute('''
                SELECT pattern_type, COUNT(*) as count
                FROM pattern_occurrences
                WHERE timeframe = ?
                GROUP BY pattern_type
                ORDER BY count DESC
            ''', (timeframe,))
        
        patterns = {row['pattern_type']: row['count'] for row in cur.fetchall()}
        
        # Get sequence counts (top 20 most common)
        if symbol:
            cur.execute('''
                SELECT sequence, COUNT(*) as count
                FROM pattern_sequences
                WHERE symbol = ? AND timeframe = ? AND sequence_length = 3
                GROUP BY sequence
                ORDER BY count DESC
                LIMIT 20
            ''', (symbol, timeframe))
        else:
            cur.execute('''
                SELECT sequence, COUNT(*) as count
                FROM pattern_sequences
                WHERE timeframe = ? AND sequence_length = 3
                GROUP BY sequence
                ORDER BY count DESC
                LIMIT 20
            ''', (timeframe,))
        
        sequences = {row['sequence']: row['count'] for row in cur.fetchall()}
        
        conn.close()
        
        return jsonify({
            'symbol': symbol or 'all',
            'timeframe': timeframe,
            'patterns': patterns,
            'sequences': sequences
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@optimized_patterns_bp.route('/api/v2/patterns/random', methods=['GET'])
def get_random_pattern_match():
    """
    Get a random pattern match for practice/exploration.
    
    Query params:
    - pattern: Pattern or sequence
    - symbol: Stock symbol (default: SPY)
    - timeframe: Timeframe (default: 1D)
    
    Returns single random match with same structure as get_pattern_matches
    """
    pattern = request.args.get('pattern', '').strip()
    symbol = request.args.get('symbol', 'SPY').upper()
    timeframe = normalize_timeframe(request.args.get('timeframe', '1D'))
    
    if not pattern:
        return jsonify({'error': 'Pattern parameter required'}), 400
    
    try:
        conn = get_db_for_timeframe(timeframe)
        cur = conn.cursor()
        
        if ',' in pattern:  # Sequence
            cur.execute('''
                SELECT start_date, end_date, next_start
                FROM pattern_sequences
                WHERE symbol = ? AND timeframe = ? AND sequence = ?
                ORDER BY RANDOM()
                LIMIT 1
            ''', (symbol, timeframe, pattern))
        else:  # Single pattern
            cur.execute('''
                SELECT date as start_date
                FROM pattern_occurrences
                WHERE symbol = ? AND timeframe = ? AND pattern_type = ?
                ORDER BY RANDOM()
                LIMIT 1
            ''', (symbol, timeframe, pattern))
        
        row = cur.fetchone()
        conn.close()
        
        if not row:
            return jsonify({'error': 'No matches found'}), 404
        
        return jsonify({
            'symbol': symbol,
            'timeframe': timeframe,
            'pattern': pattern,
            'match': dict(row)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
