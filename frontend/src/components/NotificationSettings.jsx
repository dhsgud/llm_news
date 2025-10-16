import React, { useState } from 'react';

const NotificationSettings = ({ settings, onSave, isLoading }) => {
  const [formData, setFormData] = useState({
    email_enabled: settings?.email_enabled || false,
    email_address: settings?.email_address || '',
    sms_enabled: settings?.sms_enabled || false,
    phone_number: settings?.phone_number || '',
    notify_on_trade: settings?.notify_on_trade !== false,
    notify_on_stop_loss: settings?.notify_on_stop_loss !== false,
    notify_on_error: settings?.notify_on_error !== false,
  });

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">알림 설정</h2>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* 이메일 알림 */}
        <div className="border-b border-gray-200 pb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-medium text-gray-800">이메일 알림</h3>
              <p className="text-sm text-gray-600">거래 및 시스템 알림을 이메일로 받습니다</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                name="email_enabled"
                checked={formData.email_enabled}
                onChange={handleChange}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>
          
          {formData.email_enabled && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                이메일 주소
              </label>
              <input
                type="email"
                name="email_address"
                value={formData.email_address}
                onChange={handleChange}
                placeholder="example@email.com"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required={formData.email_enabled}
              />
            </div>
          )}
        </div>

        {/* SMS 알림 */}
        <div className="border-b border-gray-200 pb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-medium text-gray-800">SMS 알림</h3>
              <p className="text-sm text-gray-600">중요한 알림을 문자로 받습니다</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                name="sms_enabled"
                checked={formData.sms_enabled}
                onChange={handleChange}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>
          
          {formData.sms_enabled && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                휴대폰 번호
              </label>
              <input
                type="tel"
                name="phone_number"
                value={formData.phone_number}
                onChange={handleChange}
                placeholder="010-1234-5678"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required={formData.sms_enabled}
              />
            </div>
          )}
        </div>

        {/* 알림 조건 */}
        <div>
          <h3 className="text-lg font-medium text-gray-800 mb-4">알림 조건</h3>
          <div className="space-y-3">
            <label className="flex items-center">
              <input
                type="checkbox"
                name="notify_on_trade"
                checked={formData.notify_on_trade}
                onChange={handleChange}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="ml-3 text-sm text-gray-700">거래 체결 시</span>
            </label>

            <label className="flex items-center">
              <input
                type="checkbox"
                name="notify_on_stop_loss"
                checked={formData.notify_on_stop_loss}
                onChange={handleChange}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="ml-3 text-sm text-gray-700">손절매 실행 시</span>
            </label>

            <label className="flex items-center">
              <input
                type="checkbox"
                name="notify_on_error"
                checked={formData.notify_on_error}
                onChange={handleChange}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="ml-3 text-sm text-gray-700">시스템 오류 발생 시</span>
            </label>
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

export default NotificationSettings;
