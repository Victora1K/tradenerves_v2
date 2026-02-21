import React, { useState } from 'react';
import Plot from 'react-plotly.js';

const CandlestickChart = ({ displayData, symbol, startPlayback, stopPlayback, resetPlayback, speedUpPlayback, slowDownPlayback, enterPosition, exitPosition, shortPosition, enterFivePositions, shortFivePositions }) => {
    const [isDarkTheme, setIsDarkTheme] = useState(false);
    const [isSymbolScrambled, setIsSymbolScrambled] = useState(true);
    

    // Toggle theme function
    const toggleTheme = () => {
        setIsDarkTheme(prevTheme => !prevTheme);
    };

    const generateSymbol = () => {
        const randLetters = ['A', 'B', 'X', 'D', 'O', 'F', 'G', 'H', 'V', 'J'];
        let rand_symbol = '';
        for (let i = 0; i < 3; i++) {
            const letterIndex = Math.floor(Math.random() * 10);
            rand_symbol += randLetters[letterIndex]
        }
        return rand_symbol;

    };

    const toggleSymbolDisplay = () => {
        setIsSymbolScrambled(prev => !prev);
        if (!isSymbolScrambled) {
            setScrambledSymbol(generateSymbol());
        }
    };
    const [scrambledSymbol, setScrambledSymbol] = useState(generateSymbol())

    // Define the layout for dark and light themes
    const darkThemeLayout = {
        title: {
            text: `${isSymbolScrambled ? scrambledSymbol : symbol} Candlestick Chart`,
            font: { color: '#FFFFFF' },
        },
        xaxis: {
            title: 'Date',
            color: '#FFFFFF',
            tickfont: { color: '#FFFFFF' },
            gridcolor: '#444444',
        },
        yaxis: {
            title: 'Price',
            color: '#FFFFFF',
            tickfont: { color: '#FFFFFF' },
            gridcolor: '#444444',
        },
        margin: { l: 50, r: 50, t: 50, b: 50 },
        paper_bgcolor: '#1e1e1e',
        plot_bgcolor: '#222222',
        showlegend: false,
        bordercolor: '#FFFFFF',
        borderwidth: 2,
    };

    const lightThemeLayout = {
        title: {
            text: `${isSymbolScrambled ? scrambledSymbol : symbol} Candlestick Chart`,
            font: { color: '#000000' },
        },
        xaxis: {
            title: 'Date',
            color: '#000000',
            tickfont: { color: '#000000' },
            gridcolor: '#e0e0e0',
        },
        yaxis: {
            title: 'Price',
            color: '#000000',
            tickfont: { color: '#000000' },
            gridcolor: '#e0e0e0',
        },
        margin: { l: 50, r: 50, t: 50, b: 50 },
        paper_bgcolor: '#f4f4f4',
        plot_bgcolor: '#ffffff',
        showlegend: false,
        bordercolor: '#000000',
        borderwidth: 2,
    };

    return (
        <div>
            <p1>
            {/* Theme Toggle Button */}
            <button style={ThemeStyle} onClick={toggleTheme}>
                Switch to {isDarkTheme ? 'Light' : 'Dark'} Theme </button>

            <button style={ThemeStyle} onClick={toggleSymbolDisplay}>
                {isSymbolScrambled ? 'Un' : ''}scramble Ticker</button>
            </p1>
            {/* Plotly Candlestick Chart */}
            <div>
            <Plot
                data={[
                    {
                        x: displayData.dates,
                        open: displayData.open,
                        high: displayData.high,
                        low: displayData.low,
                        close: displayData.close,
                        type: 'candlestick',
                        xaxis: 'x',
                        yaxis: 'y',
                    },
                ]}
                layout={isDarkTheme ? darkThemeLayout : lightThemeLayout}
                //style={ChartStyle}
                config={{
                    displayModeBar: false, // Hide the plotly toolbar for a cleaner look
                }}
            />
            </div>
                <div style={buttonContainer}>
      <button style={buttonStyle} onClick={startPlayback}>Start</button>
      <button style={buttonStyle}  onClick={stopPlayback}>Pause</button>
      <button style={buttonStyle}  onClick={resetPlayback}>Reset</button>
      <button style={buttonStyle}  onClick={speedUpPlayback}>Speed Up</button>
      <button style={buttonStyle}  onClick={slowDownPlayback}>Slow Down</button>
    </div>
    <div style={buttonContainer}>
        <button style={buttonStyle}  onClick={enterPosition}> Buy </button>
        <button style={buttonStyle}  onClick={enterFivePositions}> Enter x5 </button>  {/* New short button */}
        <button style={buttonStyle}  onClick={exitPosition}> Exit </button>
        <button style={buttonStyle}  onClick={shortPosition}> Short </button>  {/* New short button */}
        <button style={buttonStyle}  onClick={shortFivePositions}> Short x5 </button>
      </div>
        </div>
    );
};

const ThemeStyle = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  position: 'relative',
  overflow: 'hidden',
  backgroundColor: '#f5f5f5',
  color: 'black',
};

const ChartStyle = {
    width: '100%',
    maxwidth: '800px',
    height: '60vh'
};

const buttonStyle = {
    margin: '4px',
    padding: '4px',
    fontSize: '10px',
    minWidth: '60px',
  };

const buttonContainer = {
    width: '90vw',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center'
}

export default CandlestickChart;
