import React, { useState, useEffect } from 'react';
import { getAccountHoldings } from '../services/api';

const PortfolioView = ({ onSelectStock }) => {
  const [holdings, setHoldings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchHoldings();
  }, []);

  const fetchHoldings = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await getAccountHoldings();
      setHoldings(data.holdings || []);
    } catch (err) {
      setError(err.message || '보유 종목을 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const calculateProfitLoss = (holding) => {
    if (!holding.current_price || !holding.average_price) return null;
    const profitLoss = (holding.current_price - holding.average_price) * holding.quantity;
    const profitLossPercent = ((holding.current_price - holding.average_price) / holding.average_price) * 100;
    return { profitLoss, profitLossPercent };
  };

  const getTotalValue = () => {
    return holdings.reduce((sum, holding) => {
      return sum + (holding.current_price || 0) * holding.quantity;
    }, 0);
  };

  const getTotalProfitLoss = () => {
    return holdings.reduce((sum, holding) => {
      const pl = calculateProfitLoss(holding);
      return sum + (pl?.profitLoss || 0);
    }, 0);
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/4"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-md p-8">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={fetchHoldings}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            다시 시도
          </button>
        </div>
      </div>
    );
  }

  const totalValue = getTotalValue();
  const totalProfitLoss = getTotalProfitLoss();

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-purple-700 text-white p-6">
        <h2 className="text-2xl font-bold mb-4">보유 종목 포트폴리오</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-purple-100 text-sm mb-1">총 평가액</p>
            <p className="text-3xl font-bold">{totalValue.toLocaleString()}원</p>
          </div>
          <div>
            <p className="text-purple-100 text-sm mb-1">총 손익</p>
            <p className={`text-3xl font-bold ${totalProfitLoss >= 0 ? 'text-green-300' : 'text-red-300'}`}>
              {totalProfitLoss >= 0 ? '+' : ''}{totalProfitLoss.toLocaleString()}원
            </p>
          </div>
        </div>
      </div>

      {/* Holdings Table */}
      <div className="p-6">
        {holdings.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500 mb-4">보유 종목이 없습니다</p>
            <p className="text-sm text-gray-400">종목을 검색하여 분석을 시작하세요</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b-2 border-gray-200">
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">종목명</th>
                  <th className="text-right py-3 px-4 font-semibold text-gray-700">보유수량</th>
                  <th className="text-right py-3 px-4 font-semibold text-gray-700">평균단가</th>
                  <th className="text-right py-3 px-4 font-semibold text-gray-700">현재가</th>
                  <th className="text-right py-3 px-4 font-semibold text-gray-700">평가액</th>
                  <th className="text-right py-3 px-4 font-semibold text-gray-700">손익</th>
                  <th className="text-right py-3 px-4 font-semibold text-gray-700">수익률</th>
                  <th className="text-center py-3 px-4 font-semibold text-gray-700">액션</th>
                </tr>
              </thead>
              <tbody>
                {holdings.map((holding, index) => {
                  const pl = calculateProfitLoss(holding);
                  const evaluationValue = (holding.current_price || 0) * holding.quantity;
                  
                  return (
                    <tr 
                      key={index} 
                      className="border-b border-gray-100 hover:bg-gray-50 transition-colors"
                    >
                      <td className="py-4 px-4">
                        <div>
                          <p className="font-semibold text-gray-800">{holding.stock_name || holding.symbol}</p>
                          <p className="text-xs text-gray-500">{holding.symbol}</p>
                        </div>
                      </td>
                      <td className="text-right py-4 px-4 text-gray-700">
                        {holding.quantity.toLocaleString()}
                      </td>
                      <td className="text-right py-4 px-4 text-gray-700">
                        {holding.average_price?.toLocaleString() || 'N/A'}원
                      </td>
                      <td className="text-right py-4 px-4 font-semibold text-gray-800">
                        {holding.current_price?.toLocaleString() || 'N/A'}원
                      </td>
                      <td className="text-right py-4 px-4 font-semibold text-gray-800">
                        {evaluationValue.toLocaleString()}원
                      </td>
                      <td className={`text-right py-4 px-4 font-semibold ${
                        pl && pl.profitLoss >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {pl ? `${pl.profitLoss >= 0 ? '+' : ''}${pl.profitLoss.toLocaleString()}원` : 'N/A'}
                      </td>
                      <td className={`text-right py-4 px-4 font-semibold ${
                        pl && pl.profitLossPercent >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {pl ? `${pl.profitLossPercent >= 0 ? '+' : ''}${pl.profitLossPercent.toFixed(2)}%` : 'N/A'}
                      </td>
                      <td className="text-center py-4 px-4">
                        <button
                          onClick={() => onSelectStock(holding.symbol)}
                          className="px-3 py-1 bg-blue-100 text-blue-600 rounded hover:bg-blue-200 transition-colors text-sm font-medium"
                        >
                          상세보기
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Refresh Button */}
      <div className="px-6 pb-6">
        <button
          onClick={fetchHoldings}
          className="w-full py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium"
        >
          새로고침
        </button>
      </div>
    </div>
  );
};

export default PortfolioView;
