import React, { useState, useEffect } from 'react';
import Plot from 'react-plotly.js';
import { useTrading } from '../context/TradingContext';
import { usePlayback } from '../hooks/usePlayback';
import API from '../services/api';
import { fetchPatternDataOptimized, getPatternMatches, getDataWithLookback } from '../services/patternApi';
import Card from './ui/Card';
import Button from './ui/Button';
import { motion } from 'framer-motion';
import { 
  Play, 
  Pause, 
  RotateCcw, 
  FastForward, 
  Rewind,
  SkipForward,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Activity,
  BarChart3,
  Eye,
  EyeOff,
  Zap,
  Copy,
  Check
} from 'lucide-react';
import './Dashboard.css';

const Dashboard = ({ totalAccountValue, setTotalAccountValue }) => {
  const LOOKBACK_BARS = 10;   // Bars before the sequence
  const FORWARD_BARS = 100;   // Bars after the sequence for playback
  // State
  const [symbol, setSymbol] = useState('');
  const [stockData, setStockData] = useState({ dates: [], open: [], high: [], low: [], close: [], volume: [] });
  const [sequenceStartIndex, setSequenceStartIndex] = useState(null); // Track where sequence starts
  const [patternType, setPatternType] = useState('random');
  const [sequenceText, setSequenceText] = useState('green,hammer,red_doji');
  const [sequenceDraft, setSequenceDraft] = useState('green');
  const [timeframe, setTimeframe] = useState('1D');
  const [selectedProfitView, setSelectedProfitView] = useState('total');
  const [dayTrade, setDayTrade] = useState(false);
  const [isDarkTheme, setIsDarkTheme] = useState(false);
  const [isSymbolScrambled, setIsSymbolScrambled] = useState(true);
  const [scrambledSymbol, setScrambledSymbol] = useState('');
  const [walletCopied, setWalletCopied] = useState(false);

  // Custom hooks
  const { state: tradingState, dispatch: tradingDispatch } = useTrading();
  const { 
    displayData, 
    currentIndex,
    isPlaying,
    playSpeed,
    controls: playbackControls
  } = usePlayback(stockData, 500, LOOKBACK_BARS + 3); // Show lookback + sequence initially

  // Format currency with commas and 2 decimal places
  const formatCurrency = (value) => {
    if (value === undefined || value === null) return '$0.00';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  // Theme and Layout
  const darkThemeLayout = {
    title: {
      text: `${isSymbolScrambled ? scrambledSymbol : symbol} Candlestick Chart`,
      font: { color: '#FFFFFF' },
    },
    xaxis: {
      title: 'Date',
      color: '#FFFFFF',
      tickfont: { color: '#FFFFFF' },
      gridcolor: '#444444',
      rangeslider: { visible: false },
    },
    yaxis: {
      title: 'Price',
      color: '#FFFFFF',
      tickfont: { color: '#FFFFFF' },
      gridcolor: '#444444',
    },
    grid: {
      pattern: 'Independent',
      rows: 2,
      columns: 1,
    },
    subplots:[['x','y'], ['x2','y2']],
    margin: { l: 50, r: 50, t: 50, b: 50 },
    paper_bgcolor: '#1e1e1e',
    plot_bgcolor: '#222222',
    showlegend: false,
    bordercolor: '#FFFFFF',
    borderwidth: 2,
  };

  const lightThemeLayout = {
    title: {
      text: `${isSymbolScrambled ? scrambledSymbol : symbol} Candlestick Chart`,
      font: { color: '#000000' },
    },
    xaxis: {
      color: '#000000',
      domain: [0,1],
      anchor: 'y',
      tickfont: { color: '#000000' },
      gridcolor: '#e0e0e0',
      rangeslider: { visible: false },
    },
    yaxis: {
      title: 'Price',
      color: '#000000',
      domain: [0.25,1],
      anchor: 'x',
      tickfont: { color: '#000000' },
      gridcolor: '#e0e0e0',
    },
    xaxis2: {
      title: 'Date',
      color: '#000000',
      domain: [0,1],
      anchor: 'y2',
      tickfont: { color: '#000000' },
      gridcolor: '#e0e0e0',
      rangeslider: { visible: false },
    },
    yaxis2: {
      title: 'Volume',
      color: '#000000',
      domain: [0,0.2],
      anchor: 'x2',
      tickfont: { color: '#000000' },
      gridcolor: '#e0e0e0',
    },
    grid: {
      pattern: 'Independent',
      rows: 2,
      columns: 1,
    },
    subplots:[['x','y'], ['x2','y2']],
    margin: { l: 50, r: 50, t: 50, b: 50 },
    paper_bgcolor: '#f4f4f4',
    plot_bgcolor: '#ffffff',
    showlegend: false,
    bordercolor: '#000000',
    borderwidth: 2,
  };

  // Styles
  const styles = {
    edge: {
      margin: '0px',
      padding: '0px',
    },
    headerText: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      position: 'relative',
      overflow: 'hidden',
    },
    chart: {
      width: '90%',
      display: 'flex',
      height: '60%',
      maxHeight: '700px'
    },
  };

  // Helper functions
  function generateSymbol() {
    const randLetters = ['A', 'B', 'X', 'D', 'O', 'F', 'G', 'H', 'V', 'J'];
    return Array(3).fill(0).map(() => 
      randLetters[Math.floor(Math.random() * 10)]).join('');
  }

  const filterTradingDays = (data) => {
    if (!data || !data.dates) return data;
    
    const filtered = {
        dates: [],
        open: [],
        high: [],
        low: [],
        close: [],
        volume: []
    };
    
    data.dates.forEach((date, i) => {
        const dayOfWeek = new Date(date).getDay();
        // Skip weekends (0 = Sunday, 6 = Saturday)
        if (dayOfWeek !== 0 && dayOfWeek !== 6 && 
            data.open[i] && data.high[i] && 
            data.low[i] && data.close[i]) {
            filtered.dates.push(date);
            filtered.open.push(data.open[i]);
            filtered.high.push(data.high[i]);
            filtered.low.push(data.low[i]);
            filtered.close.push(data.close[i]);
            filtered.volume.push(data.volume[i] || 0);
        }
    });
    return filtered;
};

  // Trading functions
  const enterPosition = (multiplier = 1) => {
    if (currentIndex > 1 && displayData.close.length > currentIndex - 1) {
      const entryPrice = displayData.close[currentIndex - 1];
      tradingDispatch({
        type: 'ENTER_POSITION',
        payload: { shares: multiplier, price: entryPrice }
      });
    }
  };

  const shortPosition = (multiplier = 1) => {
    if (currentIndex > 1 && displayData.close.length > currentIndex - 1) {
      const entryPrice = displayData.close[currentIndex - 1];
      tradingDispatch({
        type: 'SHORT_POSITION',
        payload: { shares: multiplier, price: entryPrice }
      });
    }
  };

  const exitPosition = () => {
    if (currentIndex > 1 && displayData.close.length > currentIndex - 1) {
      const currentPrice = displayData.close[currentIndex - 1];
      tradingDispatch({
        type: 'EXIT_POSITION',
        payload: { price: currentPrice }
      });
    }
  };

  // UI functions
  const toggleTheme = () => setIsDarkTheme(prev => !prev);
  const toggleSymbolDisplay = () => {
    setIsSymbolScrambled(prev => !prev);
    if (!isSymbolScrambled) {
      setScrambledSymbol(generateSymbol());
    }
  };

  // Data fetching - Using optimized v2 API
  const fetchPatternData = async () => {
    try {
      playbackControls.reset();
      
      // Determine pattern string
      let pattern = patternType;
      let targetSymbol = 'any'; // Dynamic - backend picks any symbol with matches
      
      if (patternType === 'sequence') {
        // Use the sequence text directly
        pattern = sequenceText;
      }
      
      // Fetch pattern data using v2 API
      console.log(`🔍 Requesting: pattern=${pattern}, symbol=${targetSymbol}, timeframe=${timeframe}, lookback=${LOOKBACK_BARS}`);
      
      const result = await fetchPatternDataOptimized(
        pattern,
        targetSymbol,
        timeframe,
        LOOKBACK_BARS,
        FORWARD_BARS
      );
      
      console.log('📦 API Response:', result);
      
      // Check if we have data
      if (!result.data || result.data.length === 0) {
        throw new Error('No OHLCV data returned from API');
      }
      
      // Transform data from array of objects to separate arrays (for compatibility)
      const transformedData = {
        dates: result.data.map(d => d.date),
        open: result.data.map(d => d.open),
        high: result.data.map(d => d.high),
        low: result.data.map(d => d.low),
        close: result.data.map(d => d.close),
        volume: result.data.map(d => d.volume)
      };
      
      // Sequence position: LOOKBACK_BARS from start (bars 0-11 lookback, 12-14 sequence, 15+ forward)
      const totalBars = result.data.length;
      if (totalBars < 3) {
        throw new Error(`Not enough bars returned: ${totalBars} (need at least 3)`);
      }
      
      const sequenceStart = LOOKBACK_BARS;
      setSequenceStartIndex(sequenceStart);
      
      setSymbol(result.symbol || targetSymbol);
      setStockData(transformedData);
      
      console.log(`✓ V2 API SUCCESS: Loaded ${result.data.length} bars (${result.totalMatches} total matches found)`);
      console.log(`📍 Sequence at bars ${sequenceStart}-${sequenceStart + 2} (${LOOKBACK_BARS} lookback + 3 sequence + ${FORWARD_BARS} forward = ${totalBars} total)`);
      
    } catch (error) {
      console.error("❌ V2 API FAILED:", error.message);
      console.error("Full error:", error);
      
      // Fallback to old API if v2 fails
      console.warn("⚠️ Falling back to old API (v1)...");
      setSequenceStartIndex(null); // Clear sequence marker
      try {
        const singleCandlePatterns = new Set(['green', 'hammer']);
        let req = patternType;

        if (patternType === 'sequence') {
          req = {
            type: 'sequence',
            seq: sequenceText
              .split(',')
              .map(s => s.trim())
              .filter(Boolean),
            timeframe
          };
        } else if (timeframe !== '1D' && singleCandlePatterns.has(patternType)) {
          req = {
            type: 'sequence',
            seq: [patternType],
            timeframe
          };
        }

        const { symbol, timestamp } = await API.fetchPatternData(req);
        setSymbol(symbol);
        await fetchStockDataOld(symbol, timestamp);
      } catch (fallbackError) {
        console.error("Fallback also failed:", fallbackError);
      }
    }
  };

  // Old fetch function kept as fallback
  const fetchStockDataOld = async (symbol, timestamp) => {
    try {
      const data = await API.fetchStockData(symbol, timestamp, { timeframe, lookback: LOOKBACK_BARS });
      setStockData(data);
    } catch (error) {
      console.error("Error fetching stock data:", error);
    }
  };

  // Update portfolio value
  useEffect(() => {
    if (currentIndex > 0 && displayData.close) {
      const currentPrice = displayData.close[currentIndex - 1];
      tradingDispatch({
        type: 'UPDATE_PORTFOLIO',
        payload: { currentPrice }
      });
    }
  }, [currentIndex, displayData.close]);

  useEffect(() => {
    if (displayData.close && displayData.close[currentIndex] !== undefined) {
      const currentPrice = displayData.close[currentIndex];
      tradingDispatch({ 
        type: 'UPDATE_PRICE', 
        payload: { price: currentPrice }
      });
    }
  }, [currentIndex, displayData.close, tradingDispatch]);

  useEffect(() => {
    if (stockData.close && stockData.close.length > 0) {
      const lastPrice = stockData.close[stockData.close.length - 1];
      tradingDispatch({ 
        type: 'UPDATE_PRICE', 
        payload: { price: lastPrice }
      });
    }
  }, [stockData.close, tradingDispatch]);

  useEffect(() => {
    setScrambledSymbol(generateSymbol());
  }, []);

  const playbackStyle = {
    width: '90vw',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center'
}

const tradingStyle = {
  width: '90vw',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  color: 'green'
}

  const handlePatternChange = (newPattern) => {
    setPatternType(newPattern);
    tradingDispatch({ type: 'SET_PATTERN', payload: newPattern });
  };

  const addSequenceStep = () => {
    const next = String(sequenceDraft || '').trim();
    if (!next) return;

    const current = sequenceText
      .split(',')
      .map(s => s.trim())
      .filter(Boolean);
    current.push(next);
    setSequenceText(current.join(','));
  };

  const clearSequence = () => {
    setSequenceText('');
  };

  const capitalizePattern = (pattern) => {
    return pattern
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const getCurrentProfit = () => {
    const profit = selectedProfitView === 'total' 
      ? (tradingState.patternProfits?.total || 0)
      : (tradingState.patternProfits?.[selectedProfitView] || 0);
    return isNaN(profit) ? 0 : profit;
  };

  const formatNumber = (value) => {
    const num = Number(value);
    return isNaN(num) ? 0 : num;
  };

  const copyWalletToClipboard = async () => {
    const walletAddress = '0x73B61c903Cab90D5C251E58FEa6D90cC3d006a68';
    try {
      await navigator.clipboard.writeText(walletAddress);
      setWalletCopied(true);
      setTimeout(() => setWalletCopied(false), 2000); // Reset after 2 seconds
    } catch (err) {
      console.error('Failed to copy wallet address:', err);
    }
  };

  return (
    <div style={{ padding: '1rem', minHeight: 'calc(100vh - 4rem)', overflow: 'auto' }}>
      {/* Two Column Layout */}
      <div className="dashboard-main-grid">
        
        {/* LEFT COLUMN - Chart */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', minHeight: 0 }}>
          {/* Chart Card */}
          <Card 
            title={`${isSymbolScrambled ? scrambledSymbol : symbol} Chart`} 
            subtitle={`${timeframe} | Bar ${currentIndex} of ${displayData.dates.length}`}
            style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}
          >
            {displayData.dates.length > 0 ? (
              <div style={{ width: '100%', height: '350px' }}>
                <Plot
                  data={[
                    {
                      type: 'candlestick',
                      x: displayData.dates,
                      open: displayData.open,
                      high: displayData.high,
                      low: displayData.low,
                      close: displayData.close,
                      xaxis: 'x',
                      yaxis: 'y',
                      increasing: { line: { color: '#10b981' } },
                      decreasing: { line: { color: '#ef4444' } }
                    },
                    {
                      type: 'bar',
                      x: displayData.dates,
                      y: displayData.volume,
                      xaxis: 'x2',
                      yaxis: 'y2',
                      marker: { color: '#7F7F7F', opacity: 0.5 }
                    }
                  ]}
                  layout={{
                    dragmode: 'zoom',
                    showlegend: false,
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    grid: { rows: 2, columns: 1, pattern: 'independent', roworder: 'top to bottom' },
                    xaxis: {
                      rangeslider: { visible: false },
                      type: 'date',
                      domain: [0, 1],
                      gridcolor: 'rgba(255,255,255,0.1)',
                      color: '#9ca3af'
                    },
                    yaxis: {
                      title: 'Price',
                      domain: [0.2, 1],
                      gridcolor: 'rgba(255,255,255,0.1)',
                      color: '#9ca3af'
                    },
                    xaxis2: {
                      rangeslider: { visible: false },
                      type: 'date',
                      domain: [0, 1],
                      gridcolor: 'rgba(255,255,255,0.1)',
                      color: '#9ca3af'
                    },
                    yaxis2: {
                      title: 'Volume',
                      domain: [0, 0.15],
                      gridcolor: 'rgba(255,255,255,0.1)',
                      color: '#9ca3af'
                    },
                    margin: { l: 50, r: 20, b: 40, t: 10 },
                    // Highlight the 3-candle sequence if we know where it is
                    shapes: sequenceStartIndex !== null && displayData.dates.length > sequenceStartIndex + 2 ? [
                      {
                        type: 'rect',
                        xref: 'x',
                        yref: 'paper',
                        x0: displayData.dates[sequenceStartIndex],
                        x1: displayData.dates[sequenceStartIndex + 2],
                        y0: 0.2,
                        y1: 1,
                        fillcolor: 'rgba(59, 130, 246, 0.1)',
                        line: {
                          color: 'rgba(59, 130, 246, 0.5)',
                          width: 2,
                          dash: 'dot'
                        }
                      }
                    ] : [],
                    annotations: sequenceStartIndex !== null && displayData.dates.length > sequenceStartIndex + 2 ? [
                      {
                        x: displayData.dates[sequenceStartIndex + 1],
                        y: 0.95,
                        xref: 'x',
                        yref: 'paper',
                        text: '🎯 SEQUENCE',
                        showarrow: false,
                        font: {
                          size: 14,
                          color: '#3b82f6',
                          family: 'monospace',
                          weight: 'bold'
                        },
                        bgcolor: 'rgba(59, 130, 246, 0.2)',
                        bordercolor: '#3b82f6',
                        borderwidth: 2,
                        borderpad: 4
                      }
                    ] : []
                  }}
                  config={{ displayModeBar: false, scrollZoom: true, responsive: true }}
                  style={{ width: '100%', height: '100%' }}
                  useResizeHandler={true}
                />
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', flex: 1, textAlign: 'center' }}>
                <BarChart3 size={64} style={{ color: '#6b7280', marginBottom: '1rem' }} />
                <p style={{ color: '#9ca3af', fontSize: '1.125rem', marginBottom: '0.5rem' }}>No chart data loaded</p>
                <p style={{ color: '#6b7280', fontSize: '0.875rem' }}>Select a pattern and click "Fetch" to load data</p>
              </div>
            )}
          </Card>

          {/* Playback Controls Bar */}
          <Card style={{ padding: '0.75rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
              <Button variant={isPlaying ? 'secondary' : 'success'} onClick={playbackControls.start} disabled={isPlaying} icon={<Play size={14} />} size="sm">Play</Button>
              <Button variant="secondary" onClick={playbackControls.stop} disabled={!isPlaying} icon={<Pause size={14} />} size="sm">Pause</Button>
              <Button variant="ghost" onClick={playbackControls.reset} icon={<RotateCcw size={14} />} size="sm">Reset</Button>
              <Button variant="ghost" onClick={playbackControls.stepForward} icon={<SkipForward size={14} />} size="sm">Next</Button>
              <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ fontSize: '0.75rem', color: '#9ca3af' }}>Speed:</span>
                <Button variant="ghost" onClick={playbackControls.speedUp} size="sm">Faster</Button>
                <span style={{ fontSize: '0.75rem', color: '#f3f4f6', fontWeight: '600' }}>{playSpeed}ms</span>
                <Button variant="ghost" onClick={playbackControls.slowDown} size="sm">Slower</Button>
              </div>
            </div>
          </Card>
        </div>

        {/* RIGHT SIDEBAR - Controls & Stats */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', overflowY: 'auto', overflowX: 'hidden', paddingRight: '0.5rem' }}>
          
          {/* Portfolio Stats - Compact 2x2 Grid */}
          <div className="stats-grid">
        {/* Buying Power */}
        <Card hover={false} style={{ background: 'linear-gradient(to bottom right, rgba(14, 165, 233, 0.2), rgba(14, 165, 233, 0.05))', borderColor: 'rgba(14, 165, 233, 0.3)', padding: '1rem' }}>
          <div style={{ display: 'flex', flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <p style={{ fontSize: '0.75rem', marginBottom: '0.25rem', color: '#9ca3af' }}>Buying Power</p>
              <h3 style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#38bdf8' }}>{formatCurrency(tradingState.accountValue)}</h3>
            </div>
            <div style={{ width: '3rem', height: '3rem', borderRadius: '0.5rem', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(14, 165, 233, 0.2)' }}>
              <DollarSign style={{ color: '#38bdf8' }} size={20} />
            </div>
          </div>
        </Card>

            {/* Current Price */}
            <Card hover={false} style={{ background: 'linear-gradient(to bottom right, rgba(59, 130, 246, 0.2), rgba(59, 130, 246, 0.05))', borderColor: 'rgba(59, 130, 246, 0.3)', padding: '0.75rem' }}>
              <div>
                <p style={{ fontSize: '0.625rem', marginBottom: '0.25rem', color: '#9ca3af' }}>Current Price</p>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#60a5fa' }}>{formatCurrency(displayData.close?.[currentIndex - 1] || 0)}</h3>
              </div>
            </Card>

            {/* Total Portfolio */}
            <Card hover={false} style={{ 
              background: tradingState.totalPortfolio >= tradingState.accountValue 
                ? 'linear-gradient(to bottom right, rgba(16, 185, 129, 0.2), rgba(16, 185, 129, 0.05))' 
                : 'linear-gradient(to bottom right, rgba(239, 68, 68, 0.2), rgba(239, 68, 68, 0.05))',
              borderColor: tradingState.totalPortfolio >= tradingState.accountValue ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)',
              padding: '0.75rem'
            }}>
              <div>
                <p style={{ fontSize: '0.625rem', marginBottom: '0.25rem', color: '#9ca3af' }}>Portfolio</p>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 'bold', color: tradingState.totalPortfolio >= tradingState.accountValue ? '#10b981' : '#ef4444' }}>
                  {formatCurrency(tradingState.totalPortfolio)}
                </h3>
              </div>
            </Card>

            {/* Position Info - Full width */}
            <Card hover={false} style={{ background: 'linear-gradient(to bottom right, rgba(139, 92, 246, 0.2), rgba(139, 92, 246, 0.05))', borderColor: 'rgba(139, 92, 246, 0.3)', padding: '0.75rem', gridColumn: '1 / -1' }}>
              <div>
                <p style={{ fontSize: '0.625rem', marginBottom: '0.5rem', color: '#9ca3af' }}>Positions</p>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                  <div>
                    <span style={{ color: '#9ca3af' }}>Long: </span>
                    <span style={{ fontWeight: '600', color: '#10b981' }}>{formatNumber(tradingState.sharesOwned)}</span>
                    <span style={{ color: '#6b7280', fontSize: '0.625rem' }}> @ {formatCurrency(tradingState.averageEntryPrice)}</span>
                  </div>
                  <div>
                    <span style={{ color: '#9ca3af' }}>Short: </span>
                    <span style={{ fontWeight: '600', color: '#ef4444' }}>{formatNumber(tradingState.shortedShares)}</span>
                    <span style={{ color: '#6b7280', fontSize: '0.625rem' }}> @ {formatCurrency(tradingState.averageShortPrice)}</span>
                  </div>
                </div>
              </div>
            </Card>
          </div>

          {/* Pattern Controls Card */}
          <Card title="Pattern Controls" style={{ padding: '1rem' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.5rem' }}>Pattern Type</label>
                <select 
                  style={{ width: '100%', backgroundColor: 'rgba(255, 255, 255, 0.05)', border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: '0.5rem', padding: '0.5rem', color: '#f3f4f6', fontSize: '0.875rem' }} 
                value={patternType} 
                onChange={(e) => handlePatternChange(e.target.value)}
              >
                <option value="random">Random Data</option>
                <option value="double_bottom">Double Bottom</option>
                <option value="volatility">High Volatility</option>
                <option value="green">Solid Green</option>
                <option value="hammer">Hammer</option>
                <option value="sequence">Stacked Sequence</option>
                </select>
              </div>

              <div className="controls-grid">
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.5rem' }}>Timeframe</label>
                  <select 
                    style={{ width: '100%', backgroundColor: 'rgba(255, 255, 255, 0.05)', border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: '0.5rem', padding: '0.5rem', color: '#f3f4f6', fontSize: '0.875rem' }} 
                    value={timeframe} 
                    onChange={(e) => setTimeframe(e.target.value)}
                  >
                    {/* Intraday options hidden - backend infrastructure kept for future use */}
                    {/* <option value="5m">5m</option>
                    <option value="10m">10m</option>
                    <option value="15m">15m</option>
                    <option value="1h">1h</option> */}
                    <option value="1D">Daily (1D)</option>
                  </select>
                </div>
                <div style={{ display: 'flex', alignItems: 'flex-end' }}>
                  <Button variant="primary" onClick={fetchPatternData} style={{ width: '100%' }} icon={<Zap size={16} />} size="md">
                    Fetch
                  </Button>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={toggleSymbolDisplay}
                  icon={isSymbolScrambled ? <EyeOff size={14} /> : <Eye size={14} />}
                >
                  {isSymbolScrambled ? 'Show' : 'Hide'} Ticker
                </Button>
              </div>

              {patternType === 'sequence' && (
                <div style={{ padding: '0.75rem', backgroundColor: 'rgba(255, 255, 255, 0.05)', borderRadius: '0.5rem', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
                  <p style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.5rem' }}>Sequence Builder</p>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    <input
                      type="text"
                      style={{ width: '100%', backgroundColor: 'rgba(255, 255, 255, 0.05)', border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: '0.5rem', padding: '0.5rem', color: '#f3f4f6', fontSize: '0.75rem' }}
                    value={sequenceText}
                    onChange={(e) => setSequenceText(e.target.value)}
                    placeholder="e.g. green,hammer,red_doji"
                    />
                    <select style={{ width: '100%', backgroundColor: 'rgba(255, 255, 255, 0.05)', border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: '0.5rem', padding: '0.5rem', color: '#f3f4f6', fontSize: '0.75rem' }} value={sequenceDraft} onChange={(e) => setSequenceDraft(e.target.value)}>
                    <option value="green">Solid Green</option>
                    <option value="hammer">Hammer</option>
                    <option value="doji">Doji</option>
                    <option value="red_doji">Red Doji</option>
                    <option value="red">Red Candle</option>
                    <option value="green_any">Green Candle</option>
                    </select>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <Button variant="outline" size="sm" onClick={addSequenceStep}>Add</Button>
                      <Button variant="ghost" size="sm" onClick={clearSequence}>Clear</Button>
                    </div>
                    <p style={{ fontSize: '0.625rem', color: '#6b7280', marginTop: '0.25rem' }}>
                      Available patterns: green, hammer, doji, red_doji, red, green_any
                    </p>
                  </div>
                </div>
              )}

              {/* Profit/Loss Display */}
              <div style={{ 
                padding: '0.75rem', 
                borderRadius: '0.5rem', 
                textAlign: 'center',
                backgroundColor: getCurrentProfit() >= 0 ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                border: `1px solid ${getCurrentProfit() >= 0 ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`
              }}>
                <p style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.25rem' }}>
                  {selectedProfitView === 'total' ? 'Total' : capitalizePattern(selectedProfitView)} P/L
                </p>
                <p style={{ fontSize: '1.5rem', fontWeight: 'bold', color: getCurrentProfit() >= 0 ? '#10b981' : '#ef4444' }}>
                  ${formatNumber(getCurrentProfit()).toFixed(2)}
                </p>
              </div>
            </div>
          </Card>

          {/* Trading Actions Card */}
          <Card title="Trading Actions" style={{ padding: '1rem' }}>
            <div className="stats-grid">
              <Button 
                variant="success" 
                onClick={() => enterPosition(1)}
                icon={<TrendingUp size={14} />}
                size="sm" 
              >
                Buy 1x
              </Button>
              <Button 
                variant="success" 
                onClick={() => enterPosition(5)}
                size="sm"
              >
                Buy 5x
              </Button>
              <Button 
                variant="danger" 
                onClick={() => shortPosition(1)}
                icon={<TrendingDown size={14} />}
                size="sm"
              >
                Short 1x
              </Button>
              <Button 
                variant="danger" 
                onClick={() => shortPosition(5)}
                size="sm"
              >
                Short 5x
              </Button>
              <Button 
                variant="secondary" 
                onClick={exitPosition}
                size="sm"
                style={{ gridColumn: '1 / -1' }}
              >
                Close Position
              </Button>
            </div>
          </Card>

          {/* Webull Link */}
          <a 
            href='https://a.webull.com/NwcK53BxT9BKOwjEn5'
            target="_blank"
            rel="noopener noreferrer"
            style={{ 
              display: 'block',
              padding: '0.75rem',
              backgroundColor: '#0284c7',
              color: '#ffffff',
              borderRadius: '0.5rem',
              textAlign: 'center',
              textDecoration: 'none',
              fontSize: '0.875rem',
              fontWeight: '500'
            }}
          >
            Get Started with Webull
          </a>

          {/* Bitcoin Donation */}
          <Card style={{ padding: '1rem', background: 'linear-gradient(to bottom right, rgba(247, 147, 26, 0.1), rgba(247, 147, 26, 0.05))', borderColor: 'rgba(247, 147, 26, 0.3)' }}>
            <div style={{ marginBottom: '0.5rem' }}>
              <p style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.25rem' }}>Support Development</p>
              <p style={{ fontSize: '0.875rem', fontWeight: '500', color: '#f59e0b' }}>Bitcoin Donations</p>
            </div>
            <button
              onClick={copyWalletToClipboard}
              style={{
                width: '100%',
                padding: '0.75rem',
                backgroundColor: walletCopied ? '#10b981' : 'rgba(247, 147, 26, 0.2)',
                border: `1px solid ${walletCopied ? '#10b981' : '#f59e0b'}`,
                borderRadius: '0.5rem',
                color: walletCopied ? '#ffffff' : '#f59e0b',
                fontSize: '0.75rem',
                fontWeight: '500',
                cursor: 'pointer',
                transition: 'all 0.2s',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.5rem',
                fontFamily: 'monospace'
              }}
              onMouseEnter={(e) => {
                if (!walletCopied) {
                  e.target.style.backgroundColor = 'rgba(247, 147, 26, 0.3)';
                }
              }}
              onMouseLeave={(e) => {
                if (!walletCopied) {
                  e.target.style.backgroundColor = 'rgba(247, 147, 26, 0.2)';
                }
              }}
            >
              {walletCopied ? (
                <>
                  <Check size={16} />
                  Copied!
                </>
              ) : (
                <>
                  <Copy size={16} />
                  Copy BTC Address
                </>
              )}
            </button>
            <p style={{ fontSize: '0.625rem', color: '#6b7280', marginTop: '0.5rem', textAlign: 'center', wordBreak: 'break-all' }}>
              0x73B61c903Cab90D5C251E58FEa6D90cC3d006a68
            </p>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
