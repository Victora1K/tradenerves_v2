import React, { createContext, useReducer, useContext } from 'react';

const TradingContext = createContext();

const initialState = {
  sharesOwned: 0,
  shortedShares: 0,
  accountValue: 10000,
  profitLoss: 0,
  entryPrices: [],
  shortedPrices: [],
  averageEntryPrice: 0,
  averageShortPrice: 0,
  totalPortfolio: 10000,
  patternProfits: {
    random: 0,
    double_bottom: 0,
    volatility: 0,
    green: 0,
    hammer: 0,
    total: 0
  },
  currentPattern: 'random'
};

function ensureNumber(value) {
  const num = Number(value);
  return isNaN(num) ? 0 : num;

}

function calculateAveragePrice(prices) {
  if (!Array.isArray(prices) || prices.length === 0) return 0;
  const sum = prices.reduce((acc, price) => acc + ensureNumber(price), 0);
  return sum / prices.length;
}

function calculateTotalPortfolio(accountValue, sharesOwned, shortedShares, currentPrice) {
  const longValue = sharesOwned * (currentPrice || 0);
  const shortValue = shortedShares * (currentPrice || 0);
  //console.log("Total portfolio from calc.: "+ accountValue + longValue - shortValue)
  return ensureNumber(accountValue + longValue - shortValue);
}

function tradingReducer(state, action) {
  switch (action.type) {
    case 'SET_PATTERN': {
      return {
        ...state,
        currentPattern: action.payload
      };
    }

    case 'ENTER_POSITION': {
      const { price, shares = 1 } = action.payload;
      const numPrice = ensureNumber(price);
      const numShares = ensureNumber(shares);
      const cost = numPrice * numShares;
      
      if (state.accountValue >= cost) {
        const newEntryPrices = [...state.entryPrices, ...Array(numShares).fill(numPrice)];
        const newAccountValue = ensureNumber(state.accountValue - cost);
        const newSharesOwned = state.sharesOwned + numShares;
        
        return {
          ...state,
          sharesOwned: newSharesOwned,
          accountValue: newAccountValue,
          entryPrices: newEntryPrices,
          averageEntryPrice: calculateAveragePrice(newEntryPrices),
          totalPortfolio: calculateTotalPortfolio(newAccountValue, newSharesOwned, state.shortedShares, numPrice)
        };
      }
      return state;
    }

    case 'SHORT_POSITION': {
      const { price, shares = 1 } = action.payload;
      const numPrice = ensureNumber(price);
      const numShares = ensureNumber(shares);
      const marginRequired = numPrice * 5;
      
      if (state.accountValue >= marginRequired * numShares) {
        const newShortPrices = [...state.shortedPrices, ...Array(numShares).fill(numPrice)];
        const cost = numPrice * numShares;
        const newAccountValue = ensureNumber(state.accountValue - cost);
        const newShortedShares = state.shortedShares + numShares;
        
        return {
          ...state,
          shortedShares: newShortedShares,
          accountValue: newAccountValue,
          shortedPrices: newShortPrices,
          averageShortPrice: calculateAveragePrice(newShortPrices),
          totalPortfolio: calculateTotalPortfolio(newAccountValue, state.sharesOwned, newShortedShares, numPrice)
        };
      }
      return state;
    }

    case 'EXIT_POSITION': {
      const { price } = action.payload;
      const numPrice = ensureNumber(price);
      
      // Calculate profit/loss and costs for long positions
      const profitFromLong = state.sharesOwned > 0 
        ? ensureNumber((numPrice - state.averageEntryPrice) * state.sharesOwned)
        : 0;
      
      const longEntryCost = state.sharesOwned > 0 
        ? ensureNumber(state.averageEntryPrice * state.sharesOwned)
        : 0;

      // Calculate profit/loss and costs for short positions
      const profitFromShort = state.shortedShares > 0
        ? ensureNumber((state.averageShortPrice - numPrice) * state.shortedShares)
        : 0;
        
      const shortEntryCost = state.shortedShares > 0
        ? ensureNumber(state.averageShortPrice * state.shortedShares)
        : 0;

      const totalProfit = ensureNumber(profitFromLong + profitFromShort);
      
      // Add back both long and short entry costs when closing positions
      const newAccountValue = ensureNumber(state.accountValue + totalProfit + longEntryCost + shortEntryCost);

      const newPatternProfits = {
        ...state.patternProfits,
        [state.currentPattern]: ensureNumber(state.patternProfits[state.currentPattern] || 0) + totalProfit,
        total: ensureNumber(state.patternProfits.total || 0) + totalProfit
      };

      return {
        ...state,
        sharesOwned: 0,
        shortedShares: 0,
        accountValue: newAccountValue,
        profitLoss: ensureNumber(state.profitLoss + totalProfit),
        entryPrices: [],
        shortedPrices: [],
        averageEntryPrice: 0,
        averageShortPrice: 0,
        patternProfits: newPatternProfits,
        totalPortfolio: newAccountValue
      };
    }

    case 'UPDATE_PORTFOLIO': {
      const { currentPrice } = action.payload;
      return {
        ...state,
        totalPortfolio: calculateTotalPortfolio(
          state.accountValue,
          state.sharesOwned,
          state.shortedShares,
          currentPrice
        )
      };
    }

    default:
      return state;
  }
}

export const TradingProvider = ({ children }) => {
  const [state, dispatch] = useReducer(tradingReducer, initialState);
  return (
    <TradingContext.Provider value={{ state, dispatch }}>
      {children}
    </TradingContext.Provider>
  );
};

export const useTrading = () => {
  const context = useContext(TradingContext);
  if (!context) {
    throw new Error('useTrading must be used within a TradingProvider');
  }
  return context;
};
