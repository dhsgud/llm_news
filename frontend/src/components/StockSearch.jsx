import React, { useState } from 'react';

const StockSearch = ({ onSelectStock }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [isSearching, setIsSearching] = useState(false);

  // Popular Korean stocks for quick access
  const popularStocks = [
    { symbol: '005930', name: '삼성전자' },
    { symbol: '000660', name: 'SK하이닉스' },
    { symbol: '035420', name: 'NAVER' },
    { symbol: '005380', name: '현대차' },
    { symbol: '051910', name: 'LG화학' },
    { symbol: '006400', name: '삼성SDI' },
    { symbol: '035720', name: '카카오' },
    { symbol: '068270', name: '셀트리온' },
  ];

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchTerm.trim()) {
      setIsSearching(true);
      onSelectStock(searchTerm.trim());
      setTimeout(() => setIsSearching(false), 500);
    }
  };

  const handleQuickSelect = (symbol) => {
    setSearchTerm(symbol);
    onSelectStock(symbol);
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">종목 검색</h2>
      
      {/* Search Form */}
      <form onSubmit={handleSearch} className="mb-6">
        <div className="flex gap-2">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="종목 코드 입력 (예: 005930)"
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            disabled={isSearching || !searchTerm.trim()}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {isSearching ? '검색 중...' : '검색'}
          </button>
        </div>
      </form>

      {/* Popular Stocks */}
      <div>
        <h3 className="text-sm font-semibold text-gray-600 mb-3">인기 종목</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          {popularStocks.map((stock) => (
            <button
              key={stock.symbol}
              onClick={() => handleQuickSelect(stock.symbol)}
              className="px-3 py-2 bg-gray-100 hover:bg-blue-50 hover:text-blue-600 rounded-lg text-sm font-medium transition-colors text-left"
            >
              <div className="font-semibold">{stock.name}</div>
              <div className="text-xs text-gray-500">{stock.symbol}</div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default StockSearch;
