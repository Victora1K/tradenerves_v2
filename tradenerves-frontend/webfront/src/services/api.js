import axios from 'axios';

const BASE_URL = process.env.NODE_ENV === 'development' 
  ? 'http://127.0.0.1:5000' 
  : 'https://tradenerves.com';

const API = {
  async fetchPatternData(patternType) {
    const endpoints = {
      double_bottom: '/api/stocks/double_bottoms',
      volatility: '/api/stocks/high_volatility',
      hammer: '/api/stocks/hammer',
      green: '/api/stocks/green',
      green_five: '/api/stocks/green_five',
      random: '/api/random_stock'
    };

    if (patternType && typeof patternType === 'object' && patternType.type === 'sequence') {
      const seq = Array.isArray(patternType.seq) ? patternType.seq.join(',') : String(patternType.seq || '');
      const symbol = patternType.symbol ? String(patternType.symbol) : '';
      const timeframe = patternType.timeframe ? String(patternType.timeframe) : '';
      const qs = new URLSearchParams();
      qs.set('seq', seq);
      if (symbol) qs.set('symbol', symbol);
      if (timeframe) qs.set('timeframe', timeframe);
      const endpoint = '/api/stocks/sequence';

      try {
        const response = await axios.get(`${BASE_URL}${endpoint}?${qs.toString()}`);
        return response.data;
      } catch (error) {
        console.error('Error fetching pattern data:', error);
        throw error;
      }
    }

    const endpoint = endpoints[patternType] || endpoints.random;
    try {
      const response = await axios.get(`${BASE_URL}${endpoint}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching pattern data:', error);
      throw error;
    }
  },

  async fetchStockData(symbol, timestamp, options = {}) {
    if (typeof options === 'boolean') {
      const endpoint = options 
        ? `/api/stock_prices_intra/${symbol}/${timestamp}`
        : `/api/stock_prices/${symbol}/${timestamp}`;

      try {
        const response = await axios.get(`${BASE_URL}${endpoint}`);
        if (response.data.length > 0) {
          return {
            dates: response.data.map(item => item.date),
            open: response.data.map(item => parseFloat(item.open)),
            high: response.data.map(item => parseFloat(item.high)),
            low: response.data.map(item => parseFloat(item.low)),
            close: response.data.map(item => parseFloat(item.close)),
            volume: response.data.map(item => parseInt(item.volume)),
          };
        }
        throw new Error('No stock data found for the selected timestamp.');
      } catch (error) {
        console.error('Error fetching stock data:', error);
        throw error;
      }
    }

    const timeframe = options.timeframe || '1D';
    const lookback = options.lookback ?? 0;
    const endpoint = `/api/stock_prices_timeframe/${symbol}/${timestamp}`;
    const qs = new URLSearchParams();
    qs.set('timeframe', timeframe);
    if (Number.isFinite(lookback) && Number(lookback) > 0) {
      qs.set('lookback', String(lookback));
    }

    try {
      const response = await axios.get(`${BASE_URL}${endpoint}?${qs.toString()}`);
      if (response.data.length > 0) {
        return {
          dates: response.data.map(item => item.date),
          open: response.data.map(item => parseFloat(item.open)),
          high: response.data.map(item => parseFloat(item.high)),
          low: response.data.map(item => parseFloat(item.low)),
          close: response.data.map(item => parseFloat(item.close)),
          volume: response.data.map(item => parseInt(item.volume)),
        };
      }
      throw new Error('No stock data found for the selected timestamp.');
    } catch (error) {
      console.error('Error fetching stock data:', error);
      throw error;
    }
  },

  async fetchHistoricalData(symbol, startDate, endDate) {
    try {
      const formattedStartDate = startDate.toISOString().split('T')[0];
      const formattedEndDate = endDate.toISOString().split('T')[0];
      const response = await axios.get(
        `${BASE_URL}/api/historical/${symbol}/${formattedStartDate}/${formattedEndDate}`
      );

      if (response.data.length > 0) {
        return {
          dates: response.data.map(item => item.date),
          open: response.data.map(item => parseFloat(item.open)),
          high: response.data.map(item => parseFloat(item.high)),
          low: response.data.map(item => parseFloat(item.low)),
          close: response.data.map(item => parseFloat(item.close)),
          volume: response.data.map(item => parseInt(item.volume)),
        };
      }
      throw new Error('No historical data found for the specified date range.');
    } catch (error) {
      console.error('Error fetching historical data:', error);
      throw error;
    }
  }
};

export default API;
