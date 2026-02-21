import React, { useState, useEffect } from 'react';
import PatternCarousel from './PatternCarousel';
import Plot from 'react-plotly.js';
import { usePracticePlayback } from '../hooks/usePracticePlayback';
import Card from './ui/Card';
import Button from './ui/Button';
import { motion } from 'framer-motion';
import { Play, Pause, RotateCcw, Shuffle, BarChart3 } from 'lucide-react';

const Practice = ({ totalAccountValue, setTotalAccountValue }) => {
  const [stockData, setStockData] = useState({ 
    dates: [], 
    open: [], 
    high: [], 
    low: [], 
    close: [], 
    volume: [] 
  });
  const [isDarkTheme, setIsDarkTheme] = useState(false);

  const { 
    displayData, 
    currentIndex,
    isPlaying,
    controls: playbackControls
  } = usePracticePlayback(stockData);

  // Theme and Layout
  const chartLayout = {
    paper_bgcolor: isDarkTheme ? '#333333' : 'white',
    plot_bgcolor: isDarkTheme ? '#333333' : 'white',
    font: { color: isDarkTheme ? '#FFFFFF' : '#000000' },
    xaxis: {
      title: 'Date',
      color: isDarkTheme ? '#FFFFFF' : '#000000',
      domain: [0, 1],
      anchor: 'y',
      tickfont: { color: isDarkTheme ? '#FFFFFF' : '#000000' },
      gridcolor: isDarkTheme ? '#444444' : '#e0e0e0',
      rangeslider: { visible: false },
    },
    yaxis: {
      title: 'Price',
      color: isDarkTheme ? '#FFFFFF' : '#000000',
      domain: [0.24, 1],
      tickfont: { color: isDarkTheme ? '#FFFFFF' : '#000000' },
      gridcolor: isDarkTheme ? '#444444' : '#e0e0e0',
    },
    xaxis2: {
      title: '',
      color: isDarkTheme ? '#FFFFFF' : '#000000',
      domain: [0, 1],
      anchor: 'y2',
      tickfont: { color: isDarkTheme ? '#FFFFFF' : '#000000' },
      gridcolor: isDarkTheme ? '#444444' : '#e0e0e0',
    },
    yaxis2: {
      title: 'Volume',
      color: isDarkTheme ? '#FFFFFF' : '#000000',
      domain: [0, 0.18],
      anchor: 'x2',
      tickfont: { color: isDarkTheme ? '#FFFFFF' : '#000000' },
      gridcolor: isDarkTheme ? '#444444' : '#e0e0e0',
    },
    grid: {
      pattern: 'Independent',
      rows: 2,
      columns: 1,
    },
    margin: { l: 50, r: 50, t: 50, b: 50 },
  };

  useEffect(() => {
    generateRandomData();
  }, []);

  const generateRandomData = () => {
    const dates = [];
    const open = [];
    const high = [];
    const low = [];
    const close = [];
    const volume = [];
    
    let basePrice = 100;
    const totalCandles = 100; // Generate 100 candles
    const startDate = new Date();
    
    for (let i = 0; i < totalCandles; i++) {
      // Generate date
      const currentDate = new Date(startDate);
      currentDate.setMinutes(startDate.getMinutes() + i * 5);
      dates.push(currentDate);

      // Generate OHLC data
      const volatility = basePrice * 0.02;
      const o = basePrice + (Math.random() - 0.5) * volatility;
      const h = o + Math.random() * volatility;
      const l = o - Math.random() * volatility;
      const c = l + Math.random() * (h - l);

      open.push(o);
      high.push(h);
      low.push(l);
      close.push(c);

      // Generate volume
      volume.push(Math.floor(Math.random() * 10000) + 1000);

      // Update base price for next candle
      basePrice = c;
    }

    setStockData({
      dates: dates,
      open: open,
      high: high,
      low: low,
      close: close,
      volume: volume
    });
  };

  const handleThemeToggle = () => {
    setIsDarkTheme(!isDarkTheme);
  };

  return (
    <div className="container mx-auto px-4 py-6 space-y-6">
      {/* Header */}
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-3xl font-bold text-gradient mb-2">Practice Mode</h1>
        <p className="text-gray-400 text-sm">
          Practice your trading skills with random market data
        </p>
      </motion.div>

      {/* Controls Card */}
      <Card title="Practice Controls" subtitle="Generate and playback random market data">
        <div className="flex flex-wrap gap-3">
          <Button 
            variant="primary" 
            onClick={generateRandomData}
            icon={<Shuffle size={16} />}
          >
            Generate New Data
          </Button>
          <Button 
            variant={isPlaying ? 'secondary' : 'success'} 
            onClick={playbackControls.togglePlay}
            icon={isPlaying ? <Pause size={16} /> : <Play size={16} />}
          >
            {isPlaying ? 'Pause' : 'Play'}
          </Button>
          <Button 
            variant="ghost" 
            onClick={playbackControls.reset}
            icon={<RotateCcw size={16} />}
          >
            Reset
          </Button>
        </div>
      </Card>

      {/* Chart */}
      {displayData.dates.length > 0 ? (
        <Card 
          title="Practice Chart" 
          subtitle={`Bar ${currentIndex} of ${displayData.dates.length}`}
        >
          <Plot
            data={[
              {
                type: 'candlestick',
                x: displayData.dates,
                open: displayData.open,
                high: displayData.high,
                low: displayData.low,
                close: displayData.close,
                yaxis: 'y',
                name: 'OHLC',
                increasing: { line: { color: '#10b981' } },
                decreasing: { line: { color: '#ef4444' } }
              },
              {
                type: 'bar',
                x: displayData.dates,
                y: displayData.volume,
                yaxis: 'y2',
                xaxis: 'x2',
                name: 'Volume',
                marker: {
                  color: displayData.close.map((close, i) => 
                    (i > 0 ? close >= displayData.close[i - 1] : true) ? '#10b981' : '#ef4444'
                  ),
                  opacity: 0.5
                }
              }
            ]}
            layout={chartLayout}
            style={{ width: '100%', height: '600px' }}
            config={{ 
              responsive: true,
              displayModeBar: false 
            }}
          />
        </Card>
      ) : (
        <Card>
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <BarChart3 size={64} className="text-gray-600 mb-4" />
            <p className="text-gray-400 text-lg mb-2">No practice data loaded</p>
            <p className="text-gray-500 text-sm">Click "Generate New Data" to start practicing</p>
          </div>
        </Card>
      )}

      {/* Pattern Carousel */}
      <PatternCarousel />
    </div>
  );
};

export default Practice;
