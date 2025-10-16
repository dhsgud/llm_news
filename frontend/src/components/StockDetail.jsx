import React, { useState, useEffect } from 'react';
import { getStockInfo, getStockSentiment } from '../services/api';

const StockDetail = ({ symbol }) => {
  const [stockInfo, setStockInfo] = useState(null);
  const [sentiment, setSentiment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('info'); // 'info' or 'news'

  useEffect(() => {
    if (symbol) {
      fetchStockData();
    }
  }, [symbol]);

  const fetchStockData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const [infoData, sentimentData] = await Promise.all([
        getStockInfo(symbol),
        getStockSentiment(symbol)
      ]);
      
      setStockInfo(infoData);
      setSentiment(sentimentData);
    } catch (err) {
      setError(err.message || '데이터를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  if (!symbol) {
    return (
      <div className="bg-white rounded-lg shadow-md p-8 text-center">
        <p className="text-gray-500">종목을 선택해주세요</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
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
            onClick={fetchStockData}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            다시 시도
          </button>
        </div>
      </div>
    );
  }

  const getSentimentColor = (score) => {
    if (score > 0.3) return 'text-green-600';
    if (score < -0.3) return 'text-red-600';
    return 'text-gray-600';
  };

  const getSentimentBgColor = (score) => {
    if (score > 0.3) return 'bg-green-100';
    if (score < -0.3) return 'bg-red-100';
    return 'bg-gray-100';
  };

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-6">
        <h2 className="text-3xl font-bold mb-2">{stockInfo?.name || symbol}</h2>
        <p className="text-blue-100">종목 코드: {symbol}</p>
      </div>

      {/* Price Info */}
      <div className="p-6 border-b">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-500 mb-1">현재가</p>
            <p className="text-2xl font-bold text-gray-800">
              {stockInfo?.current_price?.toLocaleString() || 'N/A'}원
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500 mb-1">거래량</p>
            <p className="text-xl font-semibold text-gray-700">
              {stockInfo?.volume?.toLocaleString() || 'N/A'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500 mb-1">시가총액</p>
            <p className="text-xl font-semibold text-gray-700">
              {stockInfo?.market_cap ? `${(stockInfo.market_cap / 1000000000000).toFixed(2)}조` : 'N/A'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500 mb-1">업데이트</p>
            <p className="text-sm text-gray-600">
              {stockInfo?.last_updated ? new Date(stockInfo.last_updated).toLocaleString('ko-KR') : 'N/A'}
            </p>
          </div>
        </div>
      </div>

      {/* Sentiment Analysis */}
      {sentiment && (
        <div className="p-6 border-b">
          <h3 className="text-lg font-bold text-gray-800 mb-4">감성 분석</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className={`p-4 rounded-lg ${getSentimentBgColor(sentiment.sentiment_score)}`}>
              <p className="text-sm text-gray-600 mb-1">감성 점수</p>
              <p className={`text-3xl font-bold ${getSentimentColor(sentiment.sentiment_score)}`}>
                {sentiment.sentiment_score?.toFixed(2) || 'N/A'}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {sentiment.sentiment_score > 0.3 ? '긍정적' : sentiment.sentiment_score < -0.3 ? '부정적' : '중립적'}
              </p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600 mb-1">관련 뉴스</p>
              <p className="text-3xl font-bold text-gray-800">
                {sentiment.news_count || 0}
              </p>
              <p className="text-xs text-gray-500 mt-1">최근 7일</p>
            </div>
          </div>
          {sentiment.summary && (
            <div className="mt-4 p-4 bg-blue-50 rounded-lg">
              <p className="text-sm font-semibold text-gray-700 mb-2">분석 요약</p>
              <p className="text-sm text-gray-600">{sentiment.summary}</p>
            </div>
          )}
        </div>
      )}

      {/* Tabs */}
      <div className="border-b">
        <div className="flex">
          <button
            onClick={() => setActiveTab('info')}
            className={`flex-1 px-6 py-3 font-medium transition-colors ${
              activeTab === 'info'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            기본 정보
          </button>
          <button
            onClick={() => setActiveTab('news')}
            className={`flex-1 px-6 py-3 font-medium transition-colors ${
              activeTab === 'news'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            관련 뉴스
          </button>
        </div>
      </div>

      {/* Tab Content */}
      <div className="p-6">
        {activeTab === 'info' && (
          <div className="space-y-3">
            <div className="flex justify-between py-2 border-b">
              <span className="text-gray-600">종목명</span>
              <span className="font-semibold">{stockInfo?.name || 'N/A'}</span>
            </div>
            <div className="flex justify-between py-2 border-b">
              <span className="text-gray-600">종목 코드</span>
              <span className="font-semibold">{symbol}</span>
            </div>
            <div className="flex justify-between py-2 border-b">
              <span className="text-gray-600">현재가</span>
              <span className="font-semibold">{stockInfo?.current_price?.toLocaleString() || 'N/A'}원</span>
            </div>
            <div className="flex justify-between py-2 border-b">
              <span className="text-gray-600">거래량</span>
              <span className="font-semibold">{stockInfo?.volume?.toLocaleString() || 'N/A'}</span>
            </div>
          </div>
        )}

        {activeTab === 'news' && (
          <div className="space-y-4">
            {stockInfo?.related_news && stockInfo.related_news.length > 0 ? (
              stockInfo.related_news.map((news, index) => (
                <div key={index} className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                  <h4 className="font-semibold text-gray-800 mb-2">{news.title}</h4>
                  <p className="text-sm text-gray-600 mb-2">{news.summary}</p>
                  <div className="flex justify-between items-center text-xs text-gray-500">
                    <span>{new Date(news.published_at).toLocaleDateString('ko-KR')}</span>
                    {news.sentiment && (
                      <span className={`px-2 py-1 rounded ${
                        news.sentiment === 'Positive' ? 'bg-green-100 text-green-700' :
                        news.sentiment === 'Negative' ? 'bg-red-100 text-red-700' :
                        'bg-gray-100 text-gray-700'
                      }`}>
                        {news.sentiment}
                      </span>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <p className="text-center text-gray-500 py-8">관련 뉴스가 없습니다</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default StockDetail;
