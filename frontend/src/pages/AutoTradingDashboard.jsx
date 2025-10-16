import React, { useState, useEffect } from 'react';
import TradingConfigPanel from '../components/TradingConfigPanel';
import TradingControlPanel from '../components/TradingControlPanel';
import TradeHistoryTable from '../components/TradeHistoryTable';
import TradingPerformance from '../components/TradingPerformance';
import NotificationSettings from '../components/NotificationSettings';
import SuccessNotification from '../components/SuccessNotification';
import ErrorNotification from '../components/ErrorNotification';
import {
  updateTradingConfig,
  startAutoTrading,
  stopAutoTrading,
  getTradeHistory,
  getAccountHoldings
} from '../services/api';

const AutoTradingDashboard = () => {
  const [config, setConfig] = useState(null);
  const [notificationSettings, setNotificationSettings] = useState(null);
  const [isActive, setIsActive] = useState(false);
  const [trades, setTrades] = useState([]);
  const [holdings, setHoldings] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingTrades, setIsLoadingTrades] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [activeTab, setActiveTab] = useState('control');

  useEffect(() => {
    loadTradeHistory();
    loadHoldings();
    
    const interval = setInterval(() => {
      if (isActive) {
        loadTradeHistory();
        loadHoldings();
      }
    }, 30000);

    return () => clearInterval(interval);
  }, [isActive]);

  const loadTradeHistory = async () => {
    try {
      setIsLoadingTrades(true);
      const data = await getTradeHistory(50);
      setTrades(data);
    } catch (error) {
      console.error('Failed to load trade history:', error);
    } finally {
      setIsLoadingTrades(false);
    }
  };

  const loadHoldings = async () => {
    try {
      const data = await getAccountHoldings();
      setHoldings(data);
    } catch (error) {
      console.error('Failed to load holdings:', error);
    }
  };

  const handleSaveConfig = async (newConfig) => {
    try {
      setIsLoading(true);
      const result = await updateTradingConfig(newConfig);
      setConfig(result);
      setSuccessMessage('설정이 저장되었습니다');
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (error) {
      setErrorMessage(error.message || '설정 저장에 실패했습니다');
      setTimeout(() => setErrorMessage(''), 5000);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStart = async () => {
    try {
      setIsLoading(true);
      await startAutoTrading();
      setIsActive(true);
      setSuccessMessage('자동 매매가 시작되었습니다');
      setTimeout(() => setSuccessMessage(''), 3000);
      loadTradeHistory();
    } catch (error) {
      setErrorMessage(error.message || '자동 매매 시작에 실패했습니다');
      setTimeout(() => setErrorMessage(''), 5000);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStop = async () => {
    try {
      setIsLoading(true);
      await stopAutoTrading();
      setIsActive(false);
      setSuccessMessage('자동 매매가 중지되었습니다');
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (error) {
      setErrorMessage(error.message || '자동 매매 중지에 실패했습니다');
      setTimeout(() => setErrorMessage(''), 5000);
    } finally {
      setIsLoading(false);
    }
  };

  const handleEmergencyStop = async () => {
    if (!window.confirm('긴급 중지하시겠습니까? 모든 거래가 즉시 중단됩니다.')) {
      return;
    }
    
    try {
      setIsLoading(true);
      await stopAutoTrading();
      setIsActive(false);
      setSuccessMessage('긴급 중지되었습니다');
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (error) {
      setErrorMessage(error.message || '긴급 중지에 실패했습니다');
      setTimeout(() => setErrorMessage(''), 5000);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveNotificationSettings = (newSettings) => {
    setNotificationSettings(newSettings);
    setSuccessMessage('알림 설정이 저장되었습니다');
    setTimeout(() => setSuccessMessage(''), 3000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-green-50 to-emerald-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl flex items-center justify-center shadow-lg">
              <span className="text-2xl">🤖</span>
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">자동 매매</h1>
              <p className="text-sm text-gray-600">AI 기반 자동 매매 시스템</p>
            </div>
          </div>

          {/* Status Badge */}
          {isActive && (
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-green-100 text-green-700 rounded-2xl font-semibold animate-pulse">
              <span className="w-2 h-2 bg-green-500 rounded-full"></span>
              자동 매매 실행 중
            </div>
          )}
        </div>

        {/* Notifications */}
        {successMessage && (
          <div className="mb-6">
            <SuccessNotification message={successMessage} />
          </div>
        )}
        {errorMessage && (
          <div className="mb-6">
            <ErrorNotification message={errorMessage} />
          </div>
        )}

        {/* Tab Navigation */}
        <div className="mb-6 flex gap-3 overflow-x-auto">
          <button
            onClick={() => setActiveTab('control')}
            className={`px-6 py-3 rounded-2xl font-bold transition-all transform flex items-center gap-2 whitespace-nowrap ${
              activeTab === 'control'
                ? 'bg-gradient-to-r from-green-500 to-emerald-600 text-white shadow-lg scale-105'
                : 'bg-white text-gray-700 hover:bg-gray-50 shadow-sm border border-gray-100'
            }`}
          >
            <span className="text-lg">⚙️</span>
            제어 및 설정
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`px-6 py-3 rounded-2xl font-bold transition-all transform flex items-center gap-2 whitespace-nowrap ${
              activeTab === 'history'
                ? 'bg-gradient-to-r from-green-500 to-emerald-600 text-white shadow-lg scale-105'
                : 'bg-white text-gray-700 hover:bg-gray-50 shadow-sm border border-gray-100'
            }`}
          >
            <span className="text-lg">📊</span>
            거래 내역
          </button>
          <button
            onClick={() => setActiveTab('settings')}
            className={`px-6 py-3 rounded-2xl font-bold transition-all transform flex items-center gap-2 whitespace-nowrap ${
              activeTab === 'settings'
                ? 'bg-gradient-to-r from-green-500 to-emerald-600 text-white shadow-lg scale-105'
                : 'bg-white text-gray-700 hover:bg-gray-50 shadow-sm border border-gray-100'
            }`}
          >
            <span className="text-lg">🔔</span>
            알림 설정
          </button>
        </div>

        {/* Main Content */}
        {activeTab === 'control' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="space-y-6">
              <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-6">
                <TradingConfigPanel
                  config={config}
                  onSave={handleSaveConfig}
                  isLoading={isLoading}
                />
              </div>
              <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-6">
                <TradingControlPanel
                  isActive={isActive}
                  onStart={handleStart}
                  onStop={handleStop}
                  onEmergencyStop={handleEmergencyStop}
                  isLoading={isLoading}
                />
              </div>
            </div>

            <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-6">
              <TradingPerformance trades={trades} holdings={holdings} />
            </div>
          </div>
        )}

        {activeTab === 'history' && (
          <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-6">
            <TradeHistoryTable trades={trades} isLoading={isLoadingTrades} />
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="max-w-2xl mx-auto">
            <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-6">
              <NotificationSettings
                settings={notificationSettings}
                onSave={handleSaveNotificationSettings}
                isLoading={isLoading}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AutoTradingDashboard;
