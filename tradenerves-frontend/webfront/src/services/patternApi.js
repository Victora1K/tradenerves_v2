/**
 * Pattern API Service - Optimized v2 endpoints
 * Handles pattern queries and data retrieval with lookback context
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

/**
 * Get all matches for a pattern or sequence
 * @param {string} pattern - Pattern key or sequence (e.g., 'green,hammer,doji')
 * @param {string} symbol - Stock symbol (default: 'SPY')
 * @param {string} timeframe - Timeframe (default: '1D')
 * @param {number} limit - Max results (default: 100)
 */
export async function getPatternMatches(pattern, symbol = 'SPY', timeframe = '1D', limit = 100) {
  try {
    const params = new URLSearchParams({
      pattern,
      symbol,
      timeframe,
      limit: limit.toString()
    });
    
    const response = await fetch(`${API_BASE_URL}/api/v2/patterns/matches?${params}`);
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching pattern matches:', error);
    throw error;
  }
}

/**
 * Get OHLCV data with lookback context
 * @param {string} symbol - Stock symbol
 * @param {string} startDate - Start date for pattern
 * @param {string} timeframe - Timeframe (default: '1D')
 * @param {number} lookback - Bars before start_date (default: 50)
 * @param {number} forward - Bars after start_date (default: 100)
 */
export async function getDataWithLookback(symbol, startDate, timeframe = '1D', lookback = 50, forward = 100) {
  try {
    const params = new URLSearchParams({
      symbol,
      start_date: startDate,
      timeframe,
      lookback: lookback.toString(),
      forward: forward.toString()
    });
    
    const response = await fetch(`${API_BASE_URL}/api/v2/data/with-lookback?${params}`);
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching data with lookback:', error);
    throw error;
  }
}

/**
 * Get a random pattern match for practice mode
 * @param {string} pattern - Pattern or sequence
 * @param {string} symbol - Stock symbol (default: 'SPY')
 * @param {string} timeframe - Timeframe (default: '1D')
 */
export async function getRandomPatternMatch(pattern, symbol = 'SPY', timeframe = '1D') {
  try {
    const params = new URLSearchParams({
      pattern,
      symbol,
      timeframe
    });
    
    const response = await fetch(`${API_BASE_URL}/api/v2/patterns/random?${params}`);
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching random pattern match:', error);
    throw error;
  }
}

/**
 * Get available patterns and their counts
 * @param {string} symbol - Stock symbol (optional)
 * @param {string} timeframe - Timeframe (default: '1D')
 */
export async function getAvailablePatterns(symbol = null, timeframe = '1D') {
  try {
    const params = new URLSearchParams({ timeframe });
    if (symbol) {
      params.append('symbol', symbol);
    }
    
    const response = await fetch(`${API_BASE_URL}/api/v2/patterns/available?${params}`);
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching available patterns:', error);
    throw error;
  }
}

/**
 * Helper: Convert match list to data using lookback
 * This is the typical workflow: get matches → pick one → get data
 * Sequence ends the chart - last candle is end_date
 */
export async function getDataForMatch(match, symbol, timeframe = '1D', lookback = 50, forward = 0) {
  // Use end_date as anchor so sequence is the LAST thing displayed initially
  // For 3-candle sequence: need lookback + 2 extra bars to include full sequence
  const anchorDate = match.end_date || match.start_date || match.date;
  const adjustedLookback = lookback + 2; // +2 to account for first 2 candles of sequence
  
  console.log('🔧 getDataForMatch called:', {
    match,
    symbol,
    anchorDate,
    lookback,
    adjustedLookback,
    forward
  });
  
  return await getDataWithLookback(symbol, anchorDate, timeframe, adjustedLookback, forward);
}

/**
 * Fetch pattern data (OPTIMIZED WORKFLOW)
 * 1. Get pattern matches (lightweight)
 * 2. Pick first/random match
 * 3. Get OHLCV data with lookback for that match
 */
export async function fetchPatternDataOptimized(pattern, symbol, timeframe = '1D', lookback = 50, forward = 0) {
  try {
    // Step 1: Get all matches (dates only - fast)
    const matchesResult = await getPatternMatches(pattern, symbol, timeframe, 100);
    
    if (!matchesResult.matches || matchesResult.matches.length === 0) {
      throw new Error(`No matches found for pattern: ${pattern}`);
    }
    
    // Random: Pick random match
    const randomIndex = Math.floor(Math.random() * matchesResult.matches.length);
    const firstMatch = matchesResult.matches[randomIndex];
    
    // Step 3: Get OHLCV data - use actual symbol from backend response (not 'any')
    const actualSymbol = matchesResult.symbol; // Backend returns the selected symbol
    const dataResult = await getDataForMatch(firstMatch, actualSymbol, timeframe, lookback, forward);
    
    return {
      matches: matchesResult.matches,
      selectedMatch: firstMatch,
      data: dataResult.data,
      symbol: actualSymbol, // Return the actual symbol used
      totalMatches: matchesResult.match_count
    };
  } catch (error) {
    console.error('Error in optimized pattern fetch:', error);
    throw error;
  }
}

export default {
  getPatternMatches,
  getDataWithLookback,
  getRandomPatternMatch,
  getAvailablePatterns,
  getDataForMatch,
  fetchPatternDataOptimized
};
