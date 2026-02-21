"""
Simple build script for pattern database.
Run this once to build/rebuild your pattern database.

Usage:
    python build_patterns.py
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from data.optimized_pattern_detection import build_pattern_database

# Your stock symbols - Edit this list as needed
SYMBOLS = [
    # Market Indexes
    'SPY', 'QQQ',
    
    # Technology (5)
    'AAPL', 'MSFT', 'NVDA', 'GOOGL', 'META',
    
    # Financial (4)
    'JPM', 'BAC', 'GS', 'WFC',
    
    # Healthcare (4)
    'JNJ', 'UNH', 'PFE', 'ABBV',
    
    # Energy (3)
    'XOM', 'CVX', 'COP',
    
    # Consumer (4)
    'WMT', 'PG', 'KO', 'COST',
    
    # Industrial (3)
    'CAT', 'BA', 'GE',
    
    # Communication (2)
    'NFLX', 'DIS'
]

# Timeframes to process
TIMEFRAMES = ['1D']  # Add '5m', '10m' etc. if you have intraday data

if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("TRADENERVES PATTERN DATABASE BUILD")
    print("=" * 70)
    print(f"\nSymbols to process: {len(SYMBOLS)}")
    print(f"Timeframes: {', '.join(TIMEFRAMES)}")
    print("\nThis will take approximately 5-10 minutes...")
    
    # Ask for confirmation
    response = input("\nProceed with build? (y/n): ").strip().lower()
    
    if response != 'y':
        print("Build cancelled.")
        sys.exit(0)
    
    print("\nStarting build...\n")
    
    try:
        build_pattern_database(SYMBOLS, TIMEFRAMES)
        
        print("\n" + "=" * 70)
        print("✅ BUILD SUCCESSFUL!")
        print("=" * 70)
        print("\nYour pattern database is ready to use.")
        print("\nNext steps:")
        print("1. Start your Flask backend: python app.py")
        print("2. Test the API: http://localhost:5000/api/v2/patterns/available")
        print("3. Update your frontend to use /api/v2/* endpoints")
        print("\n")
        
    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ BUILD FAILED")
        print("=" * 70)
        print(f"\nError: {e}")
        print("\nPlease check:")
        print("1. Database file exists and has data")
        print("2. stock_prices table contains data for your symbols")
        print("3. SQLite database is not corrupted")
        sys.exit(1)
