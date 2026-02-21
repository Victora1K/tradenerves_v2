import { useState, useEffect, useRef } from 'react';

export function usePracticePlayback(stockData) {
  const [currentIndex, setCurrentIndex] = useState(18);
  const [intervalId, setIntervalId] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [displayData, setDisplayData] = useState({ 
    dates: [], open: [], high: [], low: [], close: [], volume: [] 
  });
  
  const dataRef = useRef(stockData);

  useEffect(() => {
    dataRef.current = stockData;
    if (stockData.dates.length > 0) {
      // Initially display first 18 candles
      setDisplayData({
        dates: stockData.dates.slice(0, 18),
        open: stockData.open.slice(0, 18),
        high: stockData.high.slice(0, 18),
        low: stockData.low.slice(0, 18),
        close: stockData.close.slice(0, 18),
        volume: stockData.volume.slice(0, 18),
      });
      setCurrentIndex(18);
      setIsPlaying(false);
      if (intervalId) {
        clearInterval(intervalId);
        setIntervalId(null);
      }
    }
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [stockData]);

  const startPlayback = () => {
    if (intervalId) {
      clearInterval(intervalId);
    }
    
    setIsPlaying(true);
    const id = setInterval(() => {
      setCurrentIndex((prevIndex) => {
        const nextIndex = prevIndex + 1;
        if (nextIndex < dataRef.current.dates.length) {
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
          setIsPlaying(false);
          return prevIndex;
        }
      });
    }, 1000); // Fixed 1 second interval
    
    setIntervalId(id);
  };

  const stopPlayback = () => {
    if (intervalId) {
      clearInterval(intervalId);
      setIntervalId(null);
    }
    setIsPlaying(false);
  };

  const resetPlayback = () => {
    stopPlayback();
    setCurrentIndex(18);
    setDisplayData({
      dates: dataRef.current.dates.slice(0, 18),
      open: dataRef.current.open.slice(0, 18),
      high: dataRef.current.high.slice(0, 18),
      low: dataRef.current.low.slice(0, 18),
      close: dataRef.current.close.slice(0, 18),
      volume: dataRef.current.volume.slice(0, 18),
    });
  };

  const togglePlay = () => {
    if (isPlaying) {
      stopPlayback();
    } else {
      startPlayback();
    }
  };

  return { 
    displayData, 
    currentIndex,
    isPlaying,
    controls: {
      togglePlay,
      reset: resetPlayback
    }
  };
}
