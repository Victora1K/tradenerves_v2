import React, { useState } from 'react';
import DatePicker from 'react-datepicker';
import "react-datepicker/dist/react-datepicker.css";
import Plot from 'react-plotly.js';
import { usePlayback } from '../hooks/usePlayback';
import API from '../services/api';
import { useTrading } from '../context/TradingContext';
import Card from './ui/Card';
import Button from './ui/Button';
import { motion } from 'framer-motion';
import { 
  Play, 
  Pause, 
  RotateCcw, 
  FastForward, 
  Rewind,
  Calendar as CalendarIcon,
  Shuffle,
  Download,
  Eye,
  EyeOff,
  AlertCircle
} from 'lucide-react';

const Events = () => {
    const [selectedDate, setSelectedDate] = useState(new Date());
    const [symbol, setSymbol] = useState('');
    const [stockData, setStockData] = useState({ dates: [], open: [], high: [], low: [], close: [], volume: [] });
    const [isDarkTheme, setIsDarkTheme] = useState(false);
    const [error, setError] = useState('');
    const [showAllData, setShowAllData] = useState(false);

    const popularStocks = [
        { symbol: 'AAPL', name: 'Apple Inc.' },
        { symbol: 'MSFT', name: 'Microsoft Corp.' },
        { symbol: 'GOOGL', name: 'Alphabet Inc.' },
        { symbol: 'AMZN', name: 'Amazon.com Inc.' },
        { symbol: 'NVDA', name: 'NVIDIA Corp.' },
        { symbol: 'META', name: 'Meta Platforms Inc.' },
        { symbol: 'TSLA', name: 'Tesla Inc.' },
        { symbol: 'JPM', name: 'JPMorgan Chase' },
        { symbol: 'V', name: 'Visa Inc.' },
        { symbol: 'WMT', name: 'Walmart Inc.' },
    ];

    const { 
        displayData, 
        currentIndex,
        isPlaying,
        playSpeed,
        controls: playbackControls 
    } = usePlayback(stockData);

    const { state: tradingState, dispatch: tradingDispatch } = useTrading();

    // Theme configurations
    const chartLayout = {
        title: {
            text: `${symbol} Historical Data`,
            font: { color: isDarkTheme ? '#FFFFFF' : '#000000' },
        },
        xaxis: {
            title: 'Date',
            color: isDarkTheme ? '#FFFFFF' : '#000000',
            domain: [0,1],
            anchor: 'y',
            tickfont: { color: isDarkTheme ? '#FFFFFF' : '#000000' },
            gridcolor: isDarkTheme ? '#444444' : '#e0e0e0',
            rangeslider: { visible: false },
        },
        yaxis: {
            title: 'Price',
            color: isDarkTheme ? '#FFFFFF' : '#000000',
            domain: [0.24,1],
            tickfont: { color: isDarkTheme ? '#FFFFFF' : '#000000' },
            gridcolor: isDarkTheme ? '#444444' : '#e0e0e0',
        },
        xaxis2: {
            title: 'Date',
            color: isDarkTheme ? '#FFFFFF' : '#000000',
            domain: [0,1],
            anchor: 'y2',
            tickfont: { color: isDarkTheme ? '#FFFFFF' : '#000000' },
            gridcolor: isDarkTheme ? '#444444' : '#e0e0e0',
        },
        yaxis2: {
            title: 'Volume',
            color: isDarkTheme ? '#FFFFFF' : '#000000',
            domain: [0,0.18],
            anchor: 'x2',
            tickfont: { color: isDarkTheme ? '#FFFFFF' : '#000000' },
            gridcolor: isDarkTheme ? '#444444' : '#e0e0e0',
        },
        grid: {
            pattern: 'Independent',
            rows: 2,
            columns: 1,
        },
        paper_bgcolor: isDarkTheme ? '#1e1e1e' : '#ffffff',
        plot_bgcolor: isDarkTheme ? '#222222' : '#ffffff',
        margin: { l: 50, r: 50, t: 50, b: 50 },
    };

    const fetchHistoricalData = async () => {
        if (!symbol) {
            setError('Please enter a stock symbol');
            return;
        }

        try {
            setError('');
            // Calculate first and last day of selected month
            const firstDay = new Date(selectedDate.getFullYear(), selectedDate.getMonth(), 1);
            const lastDay = new Date(selectedDate.getFullYear(), selectedDate.getMonth() + 1, 0);
            
            const data = await API.fetchHistoricalData(symbol, firstDay, lastDay);
            setStockData(data);
            playbackControls.reset();
        } catch (error) {
            setError('Error fetching data: ' + error.message);
        }
    };

    const getRandomMonthData = async () => {
        try {
            // Get random stock
            const randomStock = popularStocks[Math.floor(Math.random() * popularStocks.length)];
            
            // Get random date from last 4 years
            const now = new Date();
            const fourYearsAgo = new Date(now.getFullYear() - 4, now.getMonth(), 1);
            const monthsDiff = (now.getFullYear() - fourYearsAgo.getFullYear()) * 12 + 
                             (now.getMonth() - fourYearsAgo.getMonth());
            
            const randomMonthsToAdd = Math.floor(Math.random() * monthsDiff);
            const randomDate = new Date(fourYearsAgo);
            randomDate.setMonth(fourYearsAgo.getMonth() + randomMonthsToAdd);
            
            // Update state
            setSymbol(randomStock.symbol);
            setSelectedDate(randomDate);
            
            // Calculate first and last day of random month
            const firstDay = new Date(randomDate.getFullYear(), randomDate.getMonth(), 1);
            const lastDay = new Date(randomDate.getFullYear(), randomDate.getMonth() + 1, 0);
            
            // Fetch data
            setError('');
            const data = await API.fetchHistoricalData(randomStock.symbol, firstDay, lastDay);
            setStockData(data);
            playbackControls.reset();
        } catch (error) {
            setError('Error fetching random data: ' + error.message);
        }
    };

    const toggleShowAllData = () => {
        setShowAllData(!showAllData);
    };

    // Use displayData for incremental display or full stockData for showing all
    const chartData = showAllData ? stockData : displayData;

    const styles = {
        container: {
            padding: '20px',
            maxWidth: '1200px',
            margin: '0 auto',
        },
        header: {
            marginBottom: '20px',
        },
        inputGroup: {
            display: 'flex',
            gap: '20px',
            marginBottom: '20px',
            alignItems: 'center',
        },
        input: {
            padding: '8px',
            borderRadius: '4px',
            border: '1px solid #ccc',
        },
        button: {
            padding: '8px 16px',
            borderRadius: '4px',
            border: 'none',
            backgroundColor: '#007bff',
            color: 'white',
            cursor: 'pointer',
        },
        error: {
            color: 'red',
            marginBottom: '10px',
        },
        chart: {
            width: '100%',
            height: '600px',
        },
    };

    const darkThemeLayout = {
        title: {
            text: `${symbol} Candlestick Chart`,
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

    const handleSymbolSelect = (selectedSymbol) => {
        setSymbol(selectedSymbol);
    };

    return (
        <div className="container mx-auto px-4 py-6 space-y-6">
            {/* Header */}
            <motion.div 
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
            >
                <h1 className="text-3xl font-bold text-gradient mb-2">Historical Playback</h1>
                <p className="text-gray-400 text-sm">
                    Review historical market data with incremental playback
                </p>
            </motion.div>

            {/* Controls Card */}
            <Card title="Data Selection" subtitle="Choose a stock and time period to analyze">
                <div className="space-y-4">
                    {/* Stock and Date Selection */}
                    <div className="grid grid-cols-1 md:grid-cols-12 gap-3">
                        <div className="md:col-span-5">
                            <label className="block text-sm text-gray-400 mb-2">Stock Symbol</label>
                            <select 
                                value={symbol} 
                                onChange={(e) => setSymbol(e.target.value)}
                                className="select-modern w-full"
                            >
                                <option value="">Select a stock</option>
                                {popularStocks.map(stock => (
                                    <option key={stock.symbol} value={stock.symbol}>
                                        {stock.symbol} - {stock.name}
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div className="md:col-span-3">
                            <label className="block text-sm text-gray-400 mb-2">Month/Year</label>
                            <DatePicker
                                selected={selectedDate}
                                onChange={date => setSelectedDate(date)}
                                dateFormat="MM/yyyy"
                                showMonthYearPicker
                                className="input-modern w-full"
                            />
                        </div>

                        <div className="md:col-span-4 flex items-end gap-2">
                            <Button 
                                variant="primary" 
                                onClick={fetchHistoricalData}
                                icon={<Download size={16} />}
                                className="flex-1"
                            >
                                Fetch Data
                            </Button>
                            <Button 
                                variant="outline" 
                                onClick={getRandomMonthData}
                                icon={<Shuffle size={16} />}
                            >
                                Random
                            </Button>
                        </div>
                    </div>

                    {/* Display Options */}
                    <div className="flex gap-2 justify-end">
                        <Button 
                            variant="ghost" 
                            size="sm"
                            onClick={toggleShowAllData}
                            icon={showAllData ? <EyeOff size={16} /> : <Eye size={16} />}
                        >
                            {showAllData ? 'Incremental' : 'Show All'}
                        </Button>
                    </div>

                    {/* Error Display */}
                    {error && (
                        <motion.div 
                            initial={{ opacity: 0, y: -10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg flex items-center gap-2 text-red-400"
                        >
                            <AlertCircle size={16} />
                            <span className="text-sm">{error}</span>
                        </motion.div>
                    )}
                </div>
            </Card>

            {/* Playback Controls */}
            {!showAllData && chartData.dates.length > 0 && (
                <Card 
                    title="Playback Controls" 
                    subtitle={`Speed: ${playSpeed}ms | Bar ${currentIndex} of ${chartData.dates.length}`}
                >
                    <div className="flex flex-wrap gap-2">
                        <Button 
                            variant={isPlaying ? 'secondary' : 'success'} 
                            onClick={playbackControls.start} 
                            disabled={isPlaying}
                            icon={<Play size={16} />}
                        >
                            Play
                        </Button>
                        <Button 
                            variant="secondary" 
                            onClick={playbackControls.stop} 
                            disabled={!isPlaying}
                            icon={<Pause size={16} />}
                        >
                            Pause
                        </Button>
                        <Button 
                            variant="ghost" 
                            onClick={playbackControls.reset}
                            icon={<RotateCcw size={16} />}
                        >
                            Reset
                        </Button>
                        <Button 
                            variant="outline" 
                            onClick={playbackControls.speedUp}
                            icon={<FastForward size={16} />}
                        >
                            Speed Up
                        </Button>
                        <Button 
                            variant="outline" 
                            onClick={playbackControls.slowDown}
                            icon={<Rewind size={16} />}
                        >
                            Slow Down
                        </Button>
                    </div>
                </Card>
            )}

            {/* Chart */}
            {chartData.dates.length > 0 ? (
                <Card 
                    title={`${symbol} Historical Chart`}
                    subtitle={showAllData ? 'Showing all data' : 'Incremental playback mode'}
                >
                    <Plot
                        data={[
                            {
                                x: chartData.dates,
                                open: chartData.open,
                                high: chartData.high,
                                low: chartData.low,
                                close: chartData.close,
                                type: 'candlestick',
                                xaxis: 'x',
                                yaxis: 'y',
                                increasing: { line: { color: '#10b981' } },
                                decreasing: { line: { color: '#ef4444' } }
                            },
                            {
                                type: 'bar',
                                x: chartData.dates,
                                y: chartData.volume,
                                xaxis: 'x2',
                                yaxis: 'y2',
                                marker: { color: '#64748b', opacity: 0.5 }
                            }
                        ]}
                        layout={chartLayout}
                        style={{ width: '100%', height: '600px' }}
                        config={{
                            displayModeBar: false,
                            responsive: true
                        }}
                    />
                </Card>
            ) : (
                <Card>
                    <div className="flex flex-col items-center justify-center py-16 text-center">
                        <CalendarIcon size={64} className="text-gray-600 mb-4" />
                        <p className="text-gray-400 text-lg mb-2">No historical data loaded</p>
                        <p className="text-gray-500 text-sm">Select a stock and date, then click "Fetch Data"</p>
                    </div>
                </Card>
            )}
        </div>
    );
};

export default Events;
