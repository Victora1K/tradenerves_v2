// TradingLogic.js

export const enterPosition = (previousIndex, displayData, setSharesOwned, setEntryPrice, setAccountValue) => {
    if (previousIndex < 0 || previousIndex >= displayData.close.length) {
      console.log("Previous index is out of bounds.");
      return;
    }
  
    const currentPrice = parseFloat(displayData.close[previousIndex]);  // Use the previous index price
    if (!isNaN(currentPrice)) {
      setSharesOwned(prevShares => prevShares + 1);  // Increment shares owned
      setEntryPrice(currentPrice);  // Set entry price for profit/loss calculation
      setAccountValue(prevValue => prevValue - currentPrice);  // Deduct the share price from account value
      console.log(`Bought 1 share at: ${currentPrice}, total shares owned.`);
    } else {
      console.log("Invalid entry price, unable to buy shares.");
    }
  };
  
  export const shortPosition = (previousIndex, displayData, sharesOwned, setSharesOwned, setAccountValue, setShortedShares) => {
    if (previousIndex < 0 || previousIndex >= displayData.close.length) {
      console.log("Previous index is out of bounds.");
      return;
    }
  
    const currentPrice = parseFloat(displayData.close[previousIndex]);
    const shortRiskRequirement = currentPrice * 5;  // Short requires 5x the short amount
  
    if (sharesOwned > 0) {  // If the user owns shares, sell them
      setSharesOwned(prevShares => prevShares - 1);
      setAccountValue(prevValue => prevValue + currentPrice);  // Add the sold amount to account
      console.log(`Sold 1 share at: ${currentPrice}, total shares owned.`);
    } else if (setAccountValue >= shortRiskRequirement) {
      setAccountValue(prevValue => prevValue - shortRiskRequirement);  // Deduct risk requirement from account
      setShortedShares(prevShorted => prevShorted + 1);  // Increment shorted shares
      console.log(`Shorted 1 share at: ${currentPrice}.`);
    } else {
      console.log("Not enough account balance to enter a short position.");
    }
  };
  
  export const exitPosition = (previousIndex, displayData, entryPrice, sharesOwned, setSharesOwned, setAccountValue, shortedShares, setShortedShares, setProfitLoss) => {
    if (previousIndex < 0 || previousIndex >= displayData.close.length) {
      console.log("Previous index is out of bounds.");
      return;
    }
  
    const currentPrice = parseFloat(displayData.close[previousIndex]);
    let profitOrLoss = 0;
  
    if (sharesOwned > 0) {
      profitOrLoss = (currentPrice - entryPrice) * sharesOwned;  // Calculate profit/loss for owned shares
      setAccountValue(prevValue => prevValue + (sharesOwned * currentPrice));
      setSharesOwned(0);  // Reset shares
    } else if (shortedShares > 0) {
      const totalShortedValue = shortedShares * currentPrice * 5;
      profitOrLoss = (entryPrice - currentPrice) * shortedShares;
      setAccountValue(prevValue => prevValue + totalShortedValue);
      setShortedShares(0);  // Reset shorted shares
    }
  
    setProfitLoss(prevProfitLoss => prevProfitLoss + profitOrLoss);  // Update profit/loss
    console.log(`Exited position with profit/loss of: ${profitOrLoss}`);
  };
  