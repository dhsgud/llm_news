import { useState } from 'react';
import { analyzeMarket } from '../services/api';
import AnalysisResults from '../components/AnalysisResults';
import AdditionalInfoPanel from '../components/AdditionalInfoPanel';
import ErrorNotification from '../components/ErrorNotification';

const MarketDashboard = () => {
  const [lastUpdated, setLastUpdated] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await analyzeMarket('general');
      setAnalysisResult(result);
      setLastUpdated(result.last_updated || new Date().toISOString());
    } catch (err) {
      setError(err);
      console.error('Analysis error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Header */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl flex items-center justify-center shadow-lg">
              <span className="text-2xl">📊</span>
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">시장 분석</h1>
              <p className="text-sm text-gray-600">AI 기반 실시간 시장 감성 분석</p>
            </div>
          </div>
          
          {lastUpdated && (
            <div className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-white rounded-2xl shadow-sm border border-gray-100">
              <svg className="w-4 h-4 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
              </svg>
              <span className="text-sm text-gray-600">마지막 업데이트:</span>
              <span className="text-sm font-semibold text-gray-900">
                {new Date(lastUpdated).toLocaleString('ko-KR', {
                  year: 'numeric',
                  month: '2-digit',
                  day: '2-digit',
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </span>
            </div>
          )}
        </div>

        {/* Analysis Button */}
        <div className="flex justify-center mb-8">
          <button
            onClick={handleAnalyze}
            disabled={loading}
            className={`
              px-8 py-4 rounded-2xl font-bold text-lg shadow-lg
              transition-all transform flex items-center gap-3
              ${loading 
                ? 'bg-gray-300 cursor-not-allowed' 
                : 'bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 hover:shadow-xl hover:scale-105 active:scale-95'
              }
              text-white
            `}
          >
            {loading ? (
              <>
                <svg 
                  className="animate-spin h-5 w-5" 
                  viewBox="0 0 24 24"
                >
                  <circle 
                    className="opacity-25" 
                    cx="12" 
                    cy="12" 
                    r="10" 
                    stroke="currentColor" 
                    strokeWidth="4"
                    fill="none"
                  />
                  <path 
                    className="opacity-75" 
                    fill="currentColor" 
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                분석 중...
              </>
            ) : (
              <>
                <span className="text-xl">🔍</span>
                시장 분석 시작
              </>
            )}
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6">
            <ErrorNotification 
              error={error} 
              onDismiss={() => setError(null)}
              autoDismiss={true}
              dismissAfter={8000}
            />
          </div>
        )}

        {/* Analysis Results */}
        {analysisResult && (
          <div className="space-y-6">
            <AnalysisResults result={analysisResult} />
            <AdditionalInfoPanel />
          </div>
        )}

        {/* Empty State */}
        {!analysisResult && !loading && !error && (
          <div className="text-center py-16">
            <div className="text-6xl mb-4">📈</div>
            <p className="text-gray-500 text-lg font-medium">시장 분석을 시작해보세요</p>
            <p className="text-gray-400 text-sm mt-2">AI가 실시간 뉴스와 데이터를 분석합니다</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default MarketDashboard;
