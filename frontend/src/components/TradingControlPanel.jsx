import React from 'react';

const TradingControlPanel = ({ 
  isActive, 
  onStart, 
  onStop, 
  onEmergencyStop,
  isLoading 
}) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">제어 패널</h2>
      
      {/* 현재 상태 */}
      <div className="mb-6 p-4 rounded-lg bg-gray-50">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">자동 매매 상태</span>
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${
              isActive ? 'bg-green-500 animate-pulse' : 'bg-gray-400'
            }`} />
            <span className={`font-bold ${
              isActive ? 'text-green-600' : 'text-gray-600'
            }`}>
              {isActive ? '활성화' : '비활성화'}
            </span>
          </div>
        </div>
      </div>

      {/* 제어 버튼 */}
      <div className="space-y-3">
        {!isActive ? (
          <button
            onClick={onStart}
            disabled={isLoading}
            className={`w-full py-3 px-4 rounded-lg font-medium text-white transition-colors ${
              isLoading
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-green-600 hover:bg-green-700'
            }`}
          >
            {isLoading ? '시작 중...' : '자동 매매 시작'}
          </button>
        ) : (
          <button
            onClick={onStop}
            disabled={isLoading}
            className={`w-full py-3 px-4 rounded-lg font-medium text-white transition-colors ${
              isLoading
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-yellow-600 hover:bg-yellow-700'
            }`}
          >
            {isLoading ? '중지 중...' : '자동 매매 중지'}
          </button>
        )}

        {/* 긴급 중지 버튼 */}
        <button
          onClick={onEmergencyStop}
          disabled={!isActive || isLoading}
          className={`w-full py-3 px-4 rounded-lg font-medium text-white transition-colors ${
            !isActive || isLoading
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-red-600 hover:bg-red-700'
          }`}
        >
          긴급 중지
        </button>
      </div>

      {/* 경고 메시지 */}
      <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <div className="flex items-start gap-2">
          <svg className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          <div className="text-sm text-yellow-800">
            <p className="font-medium mb-1">주의사항</p>
            <ul className="list-disc list-inside space-y-1 text-xs">
              <li>자동 매매는 실제 자금을 사용합니다</li>
              <li>시장 상황에 따라 손실이 발생할 수 있습니다</li>
              <li>정기적으로 거래 내역을 확인하세요</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TradingControlPanel;
