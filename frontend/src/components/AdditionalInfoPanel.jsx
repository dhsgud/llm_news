import { useState, useEffect } from 'react';
import { getDailySentiment } from '../services/api';
import DailySentimentChart from './DailySentimentChart';

const AdditionalInfoPanel = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [dailyData, setDailyData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen && !dailyData) {
      fetchDailyData();
    }
  }, [isOpen]);

  const fetchDailyData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await getDailySentiment(7);
      setDailyData(data);
    } catch (err) {
      setError('Failed to load daily sentiment data');
      console.error('Daily sentiment error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
      >
        <span className="text-lg font-semibold text-gray-900">
          Daily Sentiment Details
        </span>
        <svg
          className={`w-6 h-6 text-gray-600 transform transition-transform ${
            isOpen ? 'rotate-180' : ''
          }`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {/* Collapsible Content */}
      {isOpen && (
        <div className="px-6 py-4 border-t border-gray-200">
          {loading && (
            <div className="flex justify-center py-8">
              <svg
                className="animate-spin h-8 w-8 text-blue-600"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          {dailyData && !loading && (
            <div>
              <DailySentimentChart dailyData={dailyData} />
              
              {/* Data Table */}
              <div className="mt-6 overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Date
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Score
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Sentiment
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {dailyData.map((item, index) => {
                      const sentiment = item.score > 0 ? 'Positive' : item.score < 0 ? 'Negative' : 'Neutral';
                      const sentimentColor = item.score > 0 ? 'text-green-600' : item.score < 0 ? 'text-red-600' : 'text-gray-600';
                      
                      return (
                        <tr key={index}>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                            {new Date(item.date).toLocaleDateString('ko-KR')}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                            {item.score.toFixed(2)}
                          </td>
                          <td className={`px-4 py-3 whitespace-nowrap text-sm font-medium ${sentimentColor}`}>
                            {sentiment}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AdditionalInfoPanel;
