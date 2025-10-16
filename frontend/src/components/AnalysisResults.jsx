import GaugeChart from './GaugeChart';

const AnalysisResults = ({ result }) => {
  const { buy_sell_ratio, trend_summary, vix } = result;

  // Determine recommendation text and color
  const getRecommendation = (ratio) => {
    if (ratio <= 30) return { text: '강력 매도', color: 'text-red-600', bg: 'bg-red-50' };
    if (ratio <= 70) return { text: '중립', color: 'text-yellow-600', bg: 'bg-yellow-50' };
    return { text: '강력 매수', color: 'text-green-600', bg: 'bg-green-50' };
  };

  const recommendation = getRecommendation(buy_sell_ratio);

  return (
    <div className="bg-white rounded-lg shadow-lg p-8">
      {/* Gauge Chart */}
      <div className="mb-8">
        <GaugeChart value={buy_sell_ratio} />
      </div>

      {/* Recommendation Badge */}
      <div className="flex justify-center mb-6">
        <div className={`${recommendation.bg} ${recommendation.color} px-6 py-3 rounded-full font-bold text-lg`}>
          {recommendation.text}
        </div>
      </div>

      {/* Trend Summary */}
      <div className="border-t border-gray-200 pt-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Market Trend Summary</h3>
        <p className="text-gray-700 leading-relaxed whitespace-pre-line">
          {trend_summary}
        </p>
      </div>

      {/* VIX Information */}
      {vix !== undefined && (
        <div className="mt-6 pt-6 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-600">VIX Index:</span>
            <span className="text-lg font-bold text-gray-900">{vix.toFixed(2)}</span>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Market volatility indicator
          </p>
        </div>
      )}
    </div>
  );
};

export default AnalysisResults;
