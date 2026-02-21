// File: /webfront/src/components/TradingControls.js

import React from 'react';

const TradingControls = ({ enterPosition, exitPosition, shortPosition }) => {
    return (
      <div>
        <button onClick={enterPosition}>Enter Buy Position</button>
        <button onClick={shortPosition}>Short</button>  {/* New short button */}
        <button onClick={exitPosition}>Exit Position</button>
      </div>
    );
  };
  

export default TradingControls;
