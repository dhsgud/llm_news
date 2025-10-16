import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navigation from './components/Navigation';
import MarketDashboard from './pages/MarketDashboard';
import StockDashboard from './pages/StockDashboard';
import AutoTradingDashboard from './pages/AutoTradingDashboard';
import NewsCollectionDashboard from './pages/NewsCollectionDashboard';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <Routes>
          <Route path="/" element={<MarketDashboard />} />
          <Route path="/stocks" element={<StockDashboard />} />
          <Route path="/auto-trading" element={<AutoTradingDashboard />} />
          <Route path="/news" element={<NewsCollectionDashboard />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
