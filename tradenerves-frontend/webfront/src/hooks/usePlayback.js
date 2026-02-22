import { useState, useEffect, useRef } from 'react';

export function usePlayback(stockData, initialSpeed = 500, initialBars = null) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [intervalId, setIntervalId] = useState(null);
  const [playSpeed, setPlaySpeed] = useState(initialSpeed);
  const [maxRange, setMaxRange] = useState(1750)
  const [displayData, setDisplayData] = useState({ 
    dates: [], open: [], high: [], low: [], close: [], volume: [] 
  });
  
  const dataRef = useRef(stockData);
  const initialBarsRef = useRef(initialBars);

  useEffect(() => {
    dataRef.current = stockData;
    if (stockData.dates.length > 0) {
      // Use initialBars if provided (for v2 API), otherwise calculate dynamically
      const initialDisplay = initialBars !== null 
        ? Math.min(initialBars, stockData.dates.length)
        : Math.min(250, Math.max(1, stockData.dates.length - 10));
      
      setDisplayData({
        dates: stockData.dates.slice(0, initialDisplay),
        open: stockData.open.slice(0, initialDisplay),
        high: stockData.high.slice(0, initialDisplay),
        low: stockData.low.slice(0, initialDisplay),
        close: stockData.close.slice(0, initialDisplay),
        volume: stockData.volume.slice(0, initialDisplay),
      });
      setCurrentIndex(initialDisplay);
      setMaxRange(stockData.dates.length); // Set max to actual data length
      
    }
    return () => stopPlayback();
  }, [stockData, initialBars]);

  useEffect(() => {
    if (intervalId) {
      stopPlayback();
      startPlayback();
    }
  }, [playSpeed]);

  const startPlayback = () => {
    if (intervalId) {
      clearInterval(intervalId);
    }
    
    const id = setInterval(() => {
      setCurrentIndex((prevIndex) => {
        const nextIndex = prevIndex + 1;
        if (dataRef.current.dates.length < maxRange) {
          setMaxRange(1200)
      
        }
        if (nextIndex <= maxRange) {
          setDisplayData({
            dates: dataRef.current.dates.slice(0, nextIndex),
            open: dataRef.current.open.slice(0, nextIndex),
            high: dataRef.current.high.slice(0, nextIndex),
            low: dataRef.current.low.slice(0, nextIndex),
            close: dataRef.current.close.slice(0, nextIndex),
            volume: dataRef.current.volume.slice(0, nextIndex),
          });
          return nextIndex;
        } else {
          clearInterval(id);
          return prevIndex;
        }
      });
    }, playSpeed);
    
    setIntervalId(id);
  };

  const stopPlayback = () => {
    if (intervalId) {
      clearInterval(intervalId);
      setIntervalId(null);
    }
  };

  const resetPlayback = () => {
    stopPlayback();
    // Use initialBarsRef if provided, otherwise calculate dynamically
    const initialDisplay = initialBarsRef.current !== null
      ? Math.min(initialBarsRef.current, dataRef.current.dates.length)
      : Math.min(250, Math.max(1, dataRef.current.dates.length - 10));
    setCurrentIndex(initialDisplay);
    setDisplayData({ 
      dates: dataRef.current.dates.slice(0, initialDisplay),
      open: dataRef.current.open.slice(0, initialDisplay),
      high: dataRef.current.high.slice(0, initialDisplay),
      low: dataRef.current.low.slice(0, initialDisplay),
      close: dataRef.current.close.slice(0, initialDisplay),
      volume: dataRef.current.volume.slice(0, initialDisplay),
    });
  };

  const adjustSpeed = (faster) => {
    setPlaySpeed(prev => {
      const newSpeed = faster ? prev / 2 : prev * 2;
      return Math.max(Math.min(newSpeed, 2000), 50);
    });
  };

  // Provide both old and new control interfaces for backward compatibility
  const controls = {
    start: startPlayback,
    stop: stopPlayback,
    reset: resetPlayback,
    speedUp: () => adjustSpeed(true),
    slowDown: () => adjustSpeed(false),
    // New interface
    togglePlay: () => intervalId ? stopPlayback() : startPlayback(),
    setPlaySpeed: (speed) => setPlaySpeed(speed)
  };

  return {
    currentIndex,
    displayData,
    playSpeed,
    isPlaying: !!intervalId,
    controls
  };
}
