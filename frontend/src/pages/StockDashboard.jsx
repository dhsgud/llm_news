import React, { useState } from 'react';
import StockSearch from '../components/StockSearch';
import StockDetail from '../components/StockDetail';
import PortfolioView from '../components/PortfolioView';

const StockDashboard = () => {
  const [selectedStock, setSelectedStock] = useState(null);
  const [activeView, setActiveView] = useState('search');

  const handleSelectStock = (symbol) => {
    setSelectedStock(symbol);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-purple-50 to-pink-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-600 rounded-2xl flex items-center justify-center shadow-lg">
              <span className="text-2xl">💹</span>
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">주식 대시보드</h1>
              <p className="text-sm text-gray-600">종목별 실시간 정보와 감성 분석</p>
            </div>
          </div>
        </div>

        {/* View Toggle */}
        <div className="mb-6 flex gap-3">
          <button
            onClick={() => setActiveView('search')}
            className={`px-6 py-3 rounded-2xl font-bold transition-all transform flex items-center gap-2 ${
              activeView === 'search'
                ? 'bg-gradient-to-r from-purple-500 to-pink-600 text-white shadow-lg scale-105'
                : 'bg-white text-gray-700 hover:bg-gray-50 shadow-sm border border-gray-100'
            }`}
          >
            <span className="text-lg">🔍</span>
            종목 검색
          </button>
          <button
            onClick={() => setActiveView('portfolio')}
            className={`px-6 py-3 rounded-2xl font-bold transition-all transform flex items-center gap-2 ${
              activeView === 'portfolio'
                ? 'bg-gradient-to-r from-purple-500 to-pink-600 text-white shadow-lg scale-105'
                : 'bg-white text-gray-700 hover:bg-gray-50 shadow-sm border border-gray-100'
            }`}
          >
            <span className="text-lg">💼</span>
            내 포트폴리오
          </button>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column */}
          <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-6">
            {activeView === 'search' ? (
              <StockSearch onSelectStock={handleSelectStock} />
            ) : (
              <PortfolioView onSelectStock={handleSelectStock} />
            )}
          </div>

          {/* Right Column */}
          <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-6">
            <StockDetail symbol={selectedStock} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default StockDashboard;
