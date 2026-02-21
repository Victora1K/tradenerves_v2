# Frontend Integration Example

## How to Gradually Migrate to v2 API

### Current Dashboard Pattern Fetching (Old Way)

```javascript
// Current code in Dashboard.js
const fetchPatternData = async () => {
  const response = await fetch(`http://localhost:5000/api/pattern/${patternType}/${timeframe}/${symbol}`);
  const data = await response.json();
  
  // Returns full OHLCV data directly
  setStockData(data);
};
```

### New Pattern Fetching (v2 API - Optimized)

```javascript
import { fetchPatternDataOptimized } from '../services/patternApi';

const fetchPatternData = async () => {
  try {
    // This automatically:
    // 1. Gets pattern matches (fast)
    // 2. Picks first match
    // 3. Fetches OHLCV with 50-bar lookback
    const result = await fetchPatternDataOptimized(
      patternType,     // e.g., 'green,hammer,doji'
      symbol,          // e.g., 'SPY'
      timeframe,       // e.g., '1D'
      50               // lookback bars
    );
    
    // result.data has the OHLCV bars with lookback context
    setStockData({
      dates: result.data.map(d => d.date),
      open: result.data.map(d => d.open),
      high: result.data.map(d => d.high),
      low: result.data.map(d => d.low),
      close: result.data.map(d => d.close),
      volume: result.data.map(d => d.volume)
    });
    
    // Optional: Store matches for user to browse
    setAllMatches(result.matches);
    setTotalMatches(result.totalMatches);
    
  } catch (error) {
    console.error('Error fetching pattern data:', error);
  }
};
```

### Advanced: Let User Browse Multiple Matches

```javascript
import { getPatternMatches, getDataForMatch } from '../services/patternApi';

const [matches, setMatches] = useState([]);
const [currentMatchIndex, setCurrentMatchIndex] = useState(0);

// Step 1: Fetch all matches when pattern selected
const fetchMatches = async () => {
  try {
    const result = await getPatternMatches(patternType, symbol, timeframe, 100);
    setMatches(result.matches);
    setCurrentMatchIndex(0);
    
    // Load first match
    if (result.matches.length > 0) {
      await loadMatchData(result.matches[0]);
    }
  } catch (error) {
    console.error('Error fetching matches:', error);
  }
};

// Step 2: Load data for specific match
const loadMatchData = async (match) => {
  try {
    const result = await getDataForMatch(match, symbol, timeframe, 50, 100);
    
    setStockData({
      dates: result.data.map(d => d.date),
      open: result.data.map(d => d.open),
      high: result.data.map(d => d.high),
      low: result.data.map(d => d.low),
      close: result.data.map(d => d.close),
      volume: result.data.map(d => d.volume)
    });
  } catch (error) {
    console.error('Error loading match data:', error);
  }
};

// Step 3: Navigate between matches
const nextMatch = () => {
  const newIndex = (currentMatchIndex + 1) % matches.length;
  setCurrentMatchIndex(newIndex);
  loadMatchData(matches[newIndex]);
};

const prevMatch = () => {
  const newIndex = (currentMatchIndex - 1 + matches.length) % matches.length;
  setCurrentMatchIndex(newIndex);
  loadMatchData(matches[newIndex]);
};

// UI: Add navigation buttons
<div>
  <button onClick={prevMatch}>← Previous Match</button>
  <span>{currentMatchIndex + 1} of {matches.length}</span>
  <button onClick={nextMatch}>Next Match →</button>
</div>
```

## Migration Strategy (Zero Breaking Changes)

### Option 1: Feature Flag (Safest)

```javascript
const USE_V2_API = false; // Change to true when ready

const fetchPatternData = async () => {
  if (USE_V2_API) {
    // New v2 API
    const result = await fetchPatternDataOptimized(patternType, symbol, timeframe, 50);
    setStockData(transformData(result.data));
  } else {
    // Old API (still works)
    const response = await fetch(`http://localhost:5000/api/pattern/${patternType}/${timeframe}/${symbol}`);
    const data = await response.json();
    setStockData(data);
  }
};
```

### Option 2: Fallback (Most Robust)

```javascript
const fetchPatternData = async () => {
  try {
    // Try v2 API first
    const result = await fetchPatternDataOptimized(patternType, symbol, timeframe, 50);
    setStockData(transformData(result.data));
  } catch (error) {
    console.warn('V2 API failed, falling back to v1:', error);
    
    // Fallback to old API
    const response = await fetch(`http://localhost:5000/api/pattern/${patternType}/${timeframe}/${symbol}`);
    const data = await response.json();
    setStockData(data);
  }
};
```

### Option 3: Separate Component (Cleanest)

```javascript
// Create DashboardV2.js with new API
// Keep Dashboard.js with old API
// Route to /dashboard-v2 for testing
// Switch route when confident
```

## Quick Test Checklist

Before migrating each component:

1. ✅ Backend is running: `python app.py`
2. ✅ Pattern database is built: `python build_patterns.py`
3. ✅ Test v2 endpoint manually:
   ```bash
   curl "http://localhost:5000/api/v2/patterns/matches?pattern=green&symbol=SPY&limit=5"
   ```
4. ✅ Import patternApi in component
5. ✅ Update one fetch function
6. ✅ Test in browser
7. ✅ Verify data displays correctly
8. ✅ Move to next component

## Key Differences to Remember

| Old API | New API | Benefit |
|---------|---------|---------|
| Returns full data immediately | Returns dates first | 100x faster |
| Single request | Two requests (matches, then data) | User can browse |
| Large payload (5-20MB) | Small payloads (<100KB) | Faster load |
| Real-time detection | Pre-computed | Consistent results |

## Pattern Format Changes

### Single Patterns (Same)
- Old: `'green'`, `'hammer'`, `'doji'`
- New: `'green'`, `'hammer'`, `'doji'` ✅

### Sequences (New Format)
- Old: Not well supported
- New: `'green,hammer,doji'` (comma-separated, 3 candles) ✨

## Data Structure Changes

### Old Response
```javascript
{
  dates: ["2020-01-02", "2020-01-03", ...],
  open: [320.5, 322.1, ...],
  high: [323.1, 324.5, ...],
  // ... etc
}
```

### New Response
```javascript
{
  data: [
    {date: "2020-01-02", open: 320.5, high: 323.1, low: 319.8, close: 322.4, volume: 75000000},
    {date: "2020-01-03", open: 322.1, high: 324.5, low: 321.2, close: 323.8, volume: 68000000},
    // ... etc
  ]
}
```

### Helper Function to Transform
```javascript
function transformData(dataArray) {
  return {
    dates: dataArray.map(d => d.date),
    open: dataArray.map(d => d.open),
    high: dataArray.map(d => d.high),
    low: dataArray.map(d => d.low),
    close: dataArray.map(d => d.close),
    volume: dataArray.map(d => d.volume)
  };
}
```

## Common Issues & Solutions

### Issue: "Pattern not found"
**Cause:** Pattern doesn't exist in precomputed database  
**Solution:** Check available patterns first
```javascript
import { getAvailablePatterns } from '../services/patternApi';
const available = await getAvailablePatterns('SPY', '1D');
console.log(available.patterns); // See what's available
```

### Issue: Data format mismatch
**Cause:** New API returns array of objects, not separate arrays  
**Solution:** Use transform helper function above

### Issue: Lookback not working
**Cause:** Not using `next_start` date from sequence matches  
**Solution:** Use `match.next_start` or `match.start_date` for data fetch

## Timeline Suggestion

**Week 1:** Test & Verify
- Build pattern database
- Test API endpoints manually
- Verify data in database

**Week 2:** Gradual Migration
- Update Dashboard component
- Add match browsing UI
- Test thoroughly

**Week 3:** Expand
- Update Practice component
- Update Events component
- Polish UI

**Week 4:** Cleanup
- Remove old code (optional)
- Optimize performance
- Document learnings
