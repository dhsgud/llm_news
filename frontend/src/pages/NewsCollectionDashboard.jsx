import { useState, useEffect, useRef } from 'react';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export default function NewsCollectionDashboard() {
  const [isCollecting, setIsCollecting] = useState(false);
  const [logs, setLogs] = useState([]);
  const [articles, setArticles] = useState([]);
  const [stats, setStats] = useState(null);
  const [showLogs, setShowLogs] = useState(false);
  const [config, setConfig] = useState({
    days: 7,
    query: 'finance OR stock OR market OR economy',
    language: 'en'
  });
  
  const logsEndRef = useRef(null);
  const logIntervalRef = useRef(null);

  // Auto-scroll logs to bottom
  const scrollToBottom = () => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [logs]);

  // Fetch logs periodically when collecting
  useEffect(() => {
    if (isCollecting) {
      logIntervalRef.current = setInterval(fetchLogs, 1000);
    } else {
      if (logIntervalRef.current) {
        clearInterval(logIntervalRef.current);
      }
    }
    
    return () => {
      if (logIntervalRef.current) {
        clearInterval(logIntervalRef.current);
      }
    };
  }, [isCollecting]);

  // Load initial data
  useEffect(() => {
    fetchArticles();
    fetchStats();
  }, []);

  const fetchLogs = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/news/logs`, {
        params: { limit: 200 }
      });
      setLogs(response.data.logs || []);
    } catch (error) {
      console.error('Failed to fetch logs:', error);
    }
  };

  const fetchArticles = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/news/articles`, {
        params: { limit: 50, days: config.days }
      });
      setArticles(response.data.articles || []);
    } catch (error) {
      console.error('Failed to fetch articles:', error);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/news/stats`, {
        params: { days: config.days }
      });
      setStats(response.data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const startCollection = async () => {
    setIsCollecting(true);
    setLogs([]);
    
    try {
      const response = await axios.post(`${API_BASE_URL}/api/news/collect`, null, {
        params: config
      });
      
      // Collection completed
      setIsCollecting(false);
      
      // Refresh data
      await fetchArticles();
      await fetchStats();
      await fetchLogs();
      
      alert(`뉴스 수집 완료!\n저장: ${response.data.saved}개\n분석: ${response.data.analyzed}개`);
    } catch (error) {
      setIsCollecting(false);
      console.error('Failed to collect news:', error);
      alert('뉴스 수집 중 오류가 발생했습니다: ' + error.message);
    }
  };

  const getSentimentEmoji = (sentiment) => {
    const emojis = {
      Positive: '😊',
      Negative: '😟',
      Neutral: '😐'
    };
    return emojis[sentiment] || '📰';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl flex items-center justify-center shadow-lg">
              <span className="text-2xl">📰</span>
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">뉴스 수집</h1>
              <p className="text-sm text-gray-600">실시간으로 금융 뉴스를 수집하고 분석해요</p>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between mb-3">
                <span className="text-3xl">📊</span>
                <div className="px-3 py-1 bg-blue-50 text-blue-600 rounded-full text-xs font-semibold">
                  전체
                </div>
              </div>
              <p className="text-sm text-gray-600 mb-1">총 뉴스 기사</p>
              <p className="text-4xl font-bold text-gray-900">{stats.total_articles.toLocaleString()}</p>
            </div>
            
            <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between mb-3">
                <span className="text-3xl">🤖</span>
                <div className="px-3 py-1 bg-purple-50 text-purple-600 rounded-full text-xs font-semibold">
                  AI 분석
                </div>
              </div>
              <p className="text-sm text-gray-600 mb-1">감성 분석 완료</p>
              <p className="text-4xl font-bold text-gray-900">{stats.articles_with_sentiment.toLocaleString()}</p>
            </div>
            
            <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between mb-3">
                <span className="text-3xl">💭</span>
                <div className="px-3 py-1 bg-green-50 text-green-600 rounded-full text-xs font-semibold">
                  감성
                </div>
              </div>
              <p className="text-sm text-gray-600 mb-2">감성 분포</p>
              <div className="space-y-2">
                {Object.entries(stats.sentiment_distribution || {}).map(([sentiment, count]) => (
                  <div key={sentiment} className="flex items-center justify-between">
                    <span className="text-xs text-gray-600 flex items-center gap-1">
                      {getSentimentEmoji(sentiment)} {sentiment}
                    </span>
                    <span className="text-sm font-bold text-gray-900">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Collection Controls */}
        <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-8 mb-6">
          <div className="flex items-center gap-2 mb-6">
            <span className="text-2xl">⚙️</span>
            <h2 className="text-xl font-bold text-gray-900">수집 설정</h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                📅 수집 기간
              </label>
              <input
                type="number"
                value={config.days}
                onChange={(e) => setConfig({ ...config, days: parseInt(e.target.value) })}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-2xl focus:border-blue-500 focus:outline-none transition-colors"
                disabled={isCollecting}
                min="1"
                max="30"
              />
              <p className="text-xs text-gray-500 mt-1">{config.days}일 전부터 오늘까지</p>
            </div>
            
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                🔍 검색 쿼리
              </label>
              <input
                type="text"
                value={config.query}
                onChange={(e) => setConfig({ ...config, query: e.target.value })}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-2xl focus:border-blue-500 focus:outline-none transition-colors"
                disabled={isCollecting}
              />
              <p className="text-xs text-gray-500 mt-1">OR로 여러 키워드 검색</p>
            </div>
            
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                🌐 언어
              </label>
              <select
                value={config.language}
                onChange={(e) => setConfig({ ...config, language: e.target.value })}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-2xl focus:border-blue-500 focus:outline-none transition-colors appearance-none bg-white"
                disabled={isCollecting}
              >
                <option value="en">🇺🇸 English</option>
                <option value="ko">🇰🇷 한국어</option>
              </select>
            </div>
          </div>

          <button
            onClick={startCollection}
            disabled={isCollecting}
            className={`w-full py-4 px-6 rounded-2xl font-bold text-white text-lg transition-all transform ${
              isCollecting
                ? 'bg-gray-300 cursor-not-allowed'
                : 'bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 hover:shadow-lg hover:scale-[1.02] active:scale-[0.98]'
            }`}
          >
            {isCollecting ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                수집 중...
              </span>
            ) : (
              '🚀 뉴스 수집 시작'
            )}
          </button>
        </div>

        {/* Logs Section */}
        {logs.length > 0 && (
          <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <span className="text-2xl">📡</span>
                <h2 className="text-xl font-bold text-gray-900">실시간 로그</h2>
                <span className="px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs font-semibold animate-pulse">
                  LIVE
                </span>
              </div>
              <button
                onClick={() => setShowLogs(!showLogs)}
                className="px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-100 rounded-xl transition-colors"
              >
                {showLogs ? '숨기기' : '보기'}
              </button>
            </div>
            
            {showLogs && (
              <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-4 h-80 overflow-y-auto font-mono text-sm shadow-inner">
                {logs.map((log, index) => (
                  <div key={index} className="mb-1 hover:bg-gray-800/50 px-2 py-1 rounded transition-colors">
                    <span className="text-gray-500 text-xs">
                      [{new Date(log.timestamp).toLocaleTimeString()}]
                    </span>
                    {' '}
                    <span className={`font-bold ${
                      log.level === 'error' ? 'text-red-400' :
                      log.level === 'warning' ? 'text-yellow-400' :
                      'text-emerald-400'
                    }`}>
                      {log.level === 'error' ? '❌' : log.level === 'warning' ? '⚠️' : '✅'}
                    </span>
                    {' '}
                    <span className="text-gray-300">{log.message}</span>
                  </div>
                ))}
                <div ref={logsEndRef} />
              </div>
            )}
          </div>
        )}

        {/* Articles List */}
        <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <span className="text-2xl">📰</span>
              <h2 className="text-xl font-bold text-gray-900">최근 뉴스</h2>
              <span className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-xs font-semibold">
                {articles.length}개
              </span>
            </div>
            <button
              onClick={fetchArticles}
              className="px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-100 rounded-xl transition-colors flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              새로고침
            </button>
          </div>

          {articles.length === 0 ? (
            <div className="text-center py-16">
              <div className="text-6xl mb-4">📭</div>
              <p className="text-gray-500 text-lg font-medium">아직 수집된 뉴스가 없어요</p>
              <p className="text-gray-400 text-sm mt-2">위에서 뉴스 수집을 시작해보세요</p>
            </div>
          ) : (
            <div className="space-y-4">
              {articles.map((article, index) => (
                <div 
                  key={article.id} 
                  className="group border-2 border-gray-100 rounded-2xl p-5 hover:border-blue-200 hover:shadow-md transition-all"
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  <div className="flex justify-between items-start gap-4">
                    <div className="flex-1">
                      <div className="flex items-start gap-3 mb-3">
                        <div className="w-10 h-10 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-xl flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
                          <span className="text-lg">📄</span>
                        </div>
                        <div className="flex-1">
                          <h3 className="font-bold text-lg text-gray-900 mb-2 group-hover:text-blue-600 transition-colors leading-snug">
                            {article.title}
                          </h3>
                          {article.description && (
                            <p className="text-sm text-gray-600 leading-relaxed line-clamp-2">
                              {article.description}
                            </p>
                          )}
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-3 text-xs text-gray-500 ml-13">
                        <span className="px-2 py-1 bg-gray-100 rounded-lg font-medium">
                          {article.source}
                        </span>
                        {article.author && (
                          <span className="flex items-center gap-1">
                            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                            </svg>
                            {article.author}
                          </span>
                        )}
                        <span className="flex items-center gap-1">
                          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
                          </svg>
                          {new Date(article.published_date).toLocaleDateString('ko-KR')}
                        </span>
                      </div>
                    </div>
                    
                    <a
                      href={article.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-4 py-2 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-xl text-sm font-semibold hover:shadow-lg hover:scale-105 transition-all flex items-center gap-2 whitespace-nowrap"
                    >
                      원문 보기
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    </a>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
