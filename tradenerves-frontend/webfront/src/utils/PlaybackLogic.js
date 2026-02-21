// PlaybackLogic.js

export const startPlayback = (setDisplayData, setCurrentIndex, playSpeed, dataRef, setIntervalId) => {
    const id = setInterval(() => {
      setCurrentIndex(prevIndex => {
        if (prevIndex < dataRef.current.dates.length - 1) {
          const nextIndex = prevIndex + 1;
  
          setDisplayData({
            dates: dataRef.current.dates.slice(0, nextIndex),
            open: dataRef.current.open.slice(0, nextIndex),
            high: dataRef.current.high.slice(0, nextIndex),
            low: dataRef.current.low.slice(0, nextIndex),
            close: dataRef.current.close.slice(0, nextIndex),
          });
  
          return nextIndex;  // Move to the next candle
        } else {
          clearInterval(id);  // Stop when all data is played
          setIntervalId(null);
          return prevIndex;
        }
      });
    }, playSpeed);
  
    setIntervalId(id);  // Save intervalId to control the playback
  };
  
  export const stopPlayback = (intervalId, setIntervalId) => {
    clearInterval(intervalId);
    setIntervalId(null);
  };
  
  export const resetPlayback = (stopPlayback, setCurrentIndex, setDisplayData, setProfitLoss, setSharesOwned, setShortedShares, setEntryPrice, setAccountValue) => {
    stopPlayback();
    setCurrentIndex(0);
    setDisplayData({ dates: [], open: [], high: [], low: [], close: [] });
    setProfitLoss(0);
    setSharesOwned(0);
    setShortedShares(0);
    setEntryPrice(null);
    setAccountValue(10000);  // Reset account value to initial
  };
  