import './App.css';
import Dashboard from './components/Dashboard';
import Events from './components/Events';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import PatternsInfo from './components/PatternsInfo';
import Navbar from './components/Navbar';
import React, { useState } from 'react';
import { TradingProvider } from './context/TradingContext';
import Practice from './components/Practice';

function App() {
  const [totalAccountValue, setTotalAccountValue] = useState(10000);
  
  return (
    <TradingProvider>
      <Router>
        <div className="min-h-screen">
          <Navbar totalAccountValue={totalAccountValue} />
          <main className="pt-16">
            <Routes>
              <Route 
                path="/" 
                element={
                  <Dashboard 
                    setTotalAccountValue={setTotalAccountValue} 
                    totalAccountValue={totalAccountValue} 
                  />
                } 
              />
              <Route path="/events" element={<Events />} />
              <Route path="/patterns" element={<PatternsInfo />} />
              <Route 
                path="/practice" 
                element={
                  <Practice 
                    setTotalAccountValue={setTotalAccountValue} 
                    totalAccountValue={totalAccountValue} 
                  />
                } 
              />
            </Routes>
          </main>
        </div>
      </Router>
    </TradingProvider>
  );
}

export default App;
