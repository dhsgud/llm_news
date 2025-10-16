import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging and adding auth tokens (future use)
apiClient.interceptors.request.use(
  (config) => {
    // Log request in development
    if (import.meta.env.DEV) {
      console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`);
    }
    return config;
  },
  (error) => {
    console.error('[API Request Error]', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    // Log response in development
    if (import.meta.env.DEV) {
      console.log(`[API Response] ${response.config.method?.toUpperCase()} ${response.config.url}`, response.data);
    }
    return response;
  },
  (error) => {
    // Handle different error types
    const errorResponse = handleApiError(error);
    return Promise.reject(errorResponse);
  }
);

/**
 * Centralized error handler for API requests
 * @param {Error} error - Axios error object
 * @returns {Object} Formatted error object
 */
const handleApiError = (error) => {
  if (error.response) {
    // Server responded with error status
    const { status, data } = error.response;
    
    switch (status) {
      case 400:
        return {
          message: data?.error || data?.detail || 'Invalid request. Please check your input.',
          status,
          type: 'validation',
        };
      case 401:
        return {
          message: 'Unauthorized. Please log in again.',
          status,
          type: 'auth',
        };
      case 403:
        return {
          message: 'Access denied. You do not have permission to perform this action.',
          status,
          type: 'auth',
        };
      case 404:
        return {
          message: data?.error || 'Resource not found.',
          status,
          type: 'not_found',
        };
      case 429:
        return {
          message: 'Too many requests. Please try again later.',
          status,
          type: 'rate_limit',
        };
      case 500:
        return {
          message: data?.error || 'Server error. Please try again later.',
          status,
          type: 'server',
        };
      case 503:
        return {
          message: 'Service temporarily unavailable. Please try again later.',
          status,
          type: 'server',
        };
      default:
        return {
          message: data?.error || data?.detail || 'An unexpected error occurred.',
          status,
          type: 'unknown',
        };
    }
  } else if (error.request) {
    // Request made but no response received
    return {
      message: 'Unable to connect to the server. Please check your internet connection.',
      status: 0,
      type: 'network',
    };
  } else {
    // Error in request setup
    return {
      message: error.message || 'An unexpected error occurred.',
      status: 0,
      type: 'client',
    };
  }
};

// ============================================================================
// Market Analysis API
// ============================================================================

/**
 * Analyze market sentiment based on recent news
 * @param {string} assetType - Type of asset to analyze ('general', 'stock', 'crypto')
 * @returns {Promise<Object>} Analysis result with buy/sell ratio and trend summary
 */
export const analyzeMarket = async (assetType = 'general') => {
  try {
    const response = await apiClient.post('/api/analyze', { asset_type: assetType });
    return response.data;
  } catch (error) {
    throw error;
  }
};

/**
 * Get recent news articles
 * @param {number} days - Number of days to look back (default: 7)
 * @param {string|null} sentiment - Filter by sentiment ('Positive', 'Negative', 'Neutral')
 * @returns {Promise<Array>} List of news articles
 */
export const getRecentNews = async (days = 7, sentiment = null) => {
  try {
    const params = { days };
    if (sentiment) params.sentiment = sentiment;
    const response = await apiClient.get('/api/news', { params });
    return response.data;
  } catch (error) {
    throw error;
  }
};

/**
 * Get daily sentiment scores for the past N days
 * @param {number} days - Number of days to retrieve (default: 7)
 * @returns {Promise<Array>} Daily sentiment scores
 */
export const getDailySentiment = async (days = 7) => {
  try {
    const response = await apiClient.get('/api/sentiment/daily', { params: { days } });
    return response.data;
  } catch (error) {
    throw error;
  }
};

// ============================================================================
// Stock API
// ============================================================================

/**
 * Get detailed information about a specific stock
 * @param {string} symbol - Stock symbol (e.g., 'AAPL', '005930')
 * @returns {Promise<Object>} Stock information including price and related news
 */
export const getStockInfo = async (symbol) => {
  try {
    const response = await apiClient.get(`/api/stocks/${symbol}`);
    return response.data;
  } catch (error) {
    throw error;
  }
};

/**
 * Get sentiment analysis for a specific stock
 * @param {string} symbol - Stock symbol
 * @returns {Promise<Object>} Stock-specific sentiment analysis
 */
export const getStockSentiment = async (symbol) => {
  try {
    const response = await apiClient.get(`/api/stocks/${symbol}/sentiment`);
    return response.data;
  } catch (error) {
    throw error;
  }
};

/**
 * Get current account holdings
 * @returns {Promise<Array>} List of holdings with quantities and prices
 */
export const getAccountHoldings = async () => {
  try {
    const response = await apiClient.get('/api/account/holdings');
    return response.data;
  } catch (error) {
    throw error;
  }
};

// ============================================================================
// Auto Trading API
// ============================================================================

/**
 * Update auto trading configuration
 * @param {Object} config - Trading configuration
 * @param {number} config.max_investment - Maximum investment amount
 * @param {string} config.risk_level - Risk level ('low', 'medium', 'high')
 * @param {number} config.stop_loss_threshold - Stop loss threshold percentage
 * @returns {Promise<Object>} Updated configuration
 */
export const updateTradingConfig = async (config) => {
  try {
    // Transform frontend config to backend schema
    const backendConfig = {
      max_investment_amount: config.max_investment || config.max_investment_amount,
      max_position_size: config.max_position_size || (config.max_investment || config.max_investment_amount) * 0.2,
      risk_level: (config.risk_level || 'medium').toUpperCase(),
      stop_loss_percentage: config.stop_loss_threshold || config.stop_loss_percentage || 5.0,
      trading_start_time: config.trading_start_time || '09:00',
      trading_end_time: config.trading_end_time || '15:30',
    };
    
    const response = await apiClient.post('/api/auto-trade/config', backendConfig);
    return response.data;
  } catch (error) {
    throw error;
  }
};

/**
 * Start auto trading
 * @returns {Promise<Object>} Status of auto trading activation
 */
export const startAutoTrading = async () => {
  try {
    const response = await apiClient.post('/api/auto-trade/start');
    return response.data;
  } catch (error) {
    throw error;
  }
};

/**
 * Stop auto trading
 * @returns {Promise<Object>} Status of auto trading deactivation
 */
export const stopAutoTrading = async () => {
  try {
    const response = await apiClient.post('/api/auto-trade/stop');
    return response.data;
  } catch (error) {
    throw error;
  }
};

/**
 * Get trade history
 * @param {number} limit - Maximum number of trades to retrieve (default: 50)
 * @returns {Promise<Array>} List of past trades
 */
export const getTradeHistory = async (limit = 50) => {
  try {
    const response = await apiClient.get('/api/trades/history', { params: { limit } });
    return response.data;
  } catch (error) {
    throw error;
  }
};

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Check if the API server is reachable
 * @returns {Promise<boolean>} True if server is reachable
 */
export const checkServerHealth = async () => {
  try {
    const response = await apiClient.get('/health', { timeout: 5000 });
    return response.status === 200;
  } catch (error) {
    return false;
  }
};

export default apiClient;
