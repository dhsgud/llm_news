import React, { useState } from 'react';

const TradingConfigPanel = ({ config, onSave, isLoading }) => {
  const [formData, setFormData] = useState({
    max_investment: config?.max_investment || 1000000,
    risk_level: config?.risk_level || 'medium',
    stop_loss_threshold: config?.stop_loss_threshold || 5.0,
    trading_start_time: config?.trading_start_time || '09:00',
    trading_end_time: config?.trading_end_time || '15:30',
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'max_investment' || name === 'stop_loss_threshold' 
        ? parseFloat(value) 
        : value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">자동 매매 설정</h2>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* 최대 투자 금액 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            최대 투자 금액 (원)
          </label>
          <input
            type="number"
            name="max_investment"
            value={formData.max_investment}
            onChange={handleChange}
            min="100000"
            step="100000"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            required
          />
          <p className="mt-1 text-sm text-gray-500">
            한 번에 투자할 수 있는 최대 금액
          </p>
        </div>

        {/* 리스크 레벨 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            리스크 레벨
          </label>
          <select
            name="risk_level"
            value={formData.risk_level}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="low">낮음 (보수적)</option>
            <option value="medium">중간 (균형)</option>
            <option value="high">높음 (공격적)</option>
          </select>
          <p className="mt-1 text-sm text-gray-500">
            {formData.risk_level === 'low' && '안전한 투자를 선호합니다'}
            {formData.risk_level === 'medium' && '균형잡힌 투자를 선호합니다'}
            {formData.risk_level === 'high' && '높은 수익을 추구합니다'}
          </p>
        </div>

        {/* 손절매 임계값 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            손절매 임계값 (%)
          </label>
          <input
            type="number"
            name="stop_loss_threshold"
            value={formData.stop_loss_threshold}
            onChange={handleChange}
            min="1"
            max="20"
            step="0.5"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            required
          />
          <p className="mt-1 text-sm text-gray-500">
            손실이 이 비율을 초과하면 자동으로 매도합니다
          </p>
        </div>

        {/* 거래 시간대 */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              거래 시작 시간
            </label>
            <input
              type="time"
              name="trading_start_time"
              value={formData.trading_start_time}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              거래 종료 시간
            </label>
            <input
              type="time"
              name="trading_end_time"
              value={formData.trading_end_time}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
        </div>

        {/* 저장 버튼 */}
        <button
          type="submit"
          disabled={isLoading}
          className={`w-full py-3 px-4 rounded-lg font-medium text-white transition-colors ${
            isLoading
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700'
          }`}
        >
          {isLoading ? '저장 중...' : '설정 저장'}
        </button>
      </form>
    </div>
  );
};

export default TradingConfigPanel;
