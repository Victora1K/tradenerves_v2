// File: /webfront/src/components/InterfaceControls.js

import React from 'react';

const InterfaceControls = ({ setSymbol }) => {
  return (
    <div>
      <button onClick={() => setSymbol('AAPL')}>Load AAPL Data</button>
      <button onClick={() => setSymbol('MSFT')}>Load MSFT Data</button>
      <button onClick={() => setSymbol('GOOGL')}>Load GOOGL Data</button>
    </div>
  );
};

export default InterfaceControls;
