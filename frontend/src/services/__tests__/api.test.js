import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import axios from 'axios';

// Mock axios before importing the API module
vi.mock('axios', () => {
  const mockAxiosInstance = {
    get: vi.fn(),
    post: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  };
  
  return {
    default: {
      create: vi.fn(() => mockAxiosInstance),
    },
  };
});

// Import after mocking
const mockAxiosInstance = axios.create();

import {
  analyzeMarket,
  getRecentNews,
  getDailySentiment,
  getStockInfo,
  getStockSentiment,
  getAccountHoldings,
  updateTradingConfig,
  startAutoTrading,
  stopAutoTrading,
  getTradeHistory,
  checkServerHealth,
} from '../api';

describe('API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Market Analysis API', () => {
    it('should analyze market successfully', async () => {
      const mockResponse = {
        data: {
          buy_sell_ratio: 75,
          trend_summary: 'Positive market sentiment',
          last_updated: '2025-10-07T12:00:00Z',
          vix: 15.5,
        },
      };

      mockAxiosInstance.post.mockResolvedValueOnce(mockResponse);

      const result = await analyzeMarket('general');

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/api/analyze', {
        asset_type: 'general',
      });
      expect(result).toEqual(mockResponse.data);
    });

    it('should get recent news successfully', async () => {
      const mockResponse = {
        data: [
          { id: 1, title: 'News 1', sentiment: 'Positive' },
          { id: 2, title: 'News 2', sentiment: 'Negative' },
        ],
      };

      mockAxiosInstance.get.mockResolvedValue(mockResponse);

      const result = await getRecentNews(7, 'Positive');

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/news', {
        params: { days: 7, sentiment: 'Positive' },
      });
      expect(result).toEqual(mockResponse.data);
    });

    it('should get daily sentiment successfully', async () => {
      const mockResponse = {
        data: [
          { date: '2025-10-01', score: 0.5 },
          { date: '2025-10-02', score: -0.3 },
        ],
      };

      mockAxiosInstance.get.mockResolvedValue(mockResponse);

      const result = await getDailySentiment(7);

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/sentiment/daily', {
        params: { days: 7 },
      });
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('Stock API', () => {
    it('should get stock info successfully', async () => {
      const mockResponse = {
        data: {
          symbol: 'AAPL',
          price: 150.25,
          volume: 1000000,
        },
      };

      mockAxiosInstance.get.mockResolvedValue(mockResponse);

      const result = await getStockInfo('AAPL');

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/stocks/AAPL');
      expect(result).toEqual(mockResponse.data);
    });

    it('should get stock sentiment successfully', async () => {
      const mockResponse = {
        data: {
          symbol: 'AAPL',
          sentiment: 'Positive',
          score: 0.8,
        },
      };

      mockAxiosInstance.get.mockResolvedValue(mockResponse);

      const result = await getStockSentiment('AAPL');

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/stocks/AAPL/sentiment');
      expect(result).toEqual(mockResponse.data);
    });

    it('should get account holdings successfully', async () => {
      const mockResponse = {
        data: [
          { symbol: 'AAPL', quantity: 10, average_price: 145.0 },
          { symbol: 'GOOGL', quantity: 5, average_price: 2800.0 },
        ],
      };

      mockAxiosInstance.get.mockResolvedValue(mockResponse);

      const result = await getAccountHoldings();

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/account/holdings');
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('Auto Trading API', () => {
    it('should update trading config successfully', async () => {
      const config = {
        max_investment: 10000,
        risk_level: 'low',
        stop_loss_threshold: 0.05,
      };

      const mockResponse = { data: { ...config, id: 1 } };

      mockAxiosInstance.post.mockResolvedValue(mockResponse);

      const result = await updateTradingConfig(config);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/api/auto-trade/config', config);
      expect(result).toEqual(mockResponse.data);
    });

    it('should start auto trading successfully', async () => {
      const mockResponse = { data: { status: 'started' } };

      mockAxiosInstance.post.mockResolvedValue(mockResponse);

      const result = await startAutoTrading();

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/api/auto-trade/start');
      expect(result).toEqual(mockResponse.data);
    });

    it('should stop auto trading successfully', async () => {
      const mockResponse = { data: { status: 'stopped' } };

      mockAxiosInstance.post.mockResolvedValue(mockResponse);

      const result = await stopAutoTrading();

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/api/auto-trade/stop');
      expect(result).toEqual(mockResponse.data);
    });

    it('should get trade history successfully', async () => {
      const mockResponse = {
        data: [
          { id: 1, symbol: 'AAPL', type: 'BUY', quantity: 10 },
          { id: 2, symbol: 'GOOGL', type: 'SELL', quantity: 5 },
        ],
      };

      mockAxiosInstance.get.mockResolvedValue(mockResponse);

      const result = await getTradeHistory(50);

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/trades/history', {
        params: { limit: 50 },
      });
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('Error Handling', () => {
    it('should handle 400 validation errors', async () => {
      const mockError = {
        response: {
          status: 400,
          data: { error: 'Invalid input' },
        },
      };

      mockAxiosInstance.post.mockRejectedValue(mockError);

      await expect(analyzeMarket('invalid')).rejects.toThrow();
    });

    it('should handle 500 server errors', async () => {
      const mockError = {
        response: {
          status: 500,
          data: { error: 'Internal server error' },
        },
      };

      mockAxiosInstance.get.mockRejectedValue(mockError);

      await expect(getRecentNews()).rejects.toThrow();
    });

    it('should handle network errors', async () => {
      const mockError = {
        request: {},
        message: 'Network Error',
      };

      mockAxiosInstance.post.mockRejectedValue(mockError);

      await expect(analyzeMarket()).rejects.toThrow();
    });
  });

  describe('Utility Functions', () => {
    it('should check server health successfully', async () => {
      mockAxiosInstance.get.mockResolvedValue({ status: 200 });

      const result = await checkServerHealth();

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/health', { timeout: 5000 });
      expect(result).toBe(true);
    });

    it('should return false when server is unreachable', async () => {
      mockAxiosInstance.get.mockRejectedValue(new Error('Network error'));

      const result = await checkServerHealth();

      expect(result).toBe(false);
    });
  });
});
