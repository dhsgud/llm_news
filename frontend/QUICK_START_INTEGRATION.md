# Quick Start: Backend-Frontend Integration

## Overview

This guide provides a quick reference for using the backend-frontend integration in the Market Sentiment Analyzer.

## Making API Calls

### Method 1: Direct API Call (Simple)

```javascript
import { analyzeMarket } from '../services/api';
import { useState } from 'react';
import ErrorNotification from '../components/ErrorNotification';

function MyComponent() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await analyzeMarket('general');
      setData(result);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {error && <ErrorNotification error={error} onDismiss={() => setError(null)} />}
      {loading && <p>Loading...</p>}
      {data && <p>Buy/Sell Ratio: {data.buy_sell_ratio}</p>}
      <button onClick={handleAnalyze}>Analyze</button>
    </div>
  );
}
```

### Method 2: Using Custom Hook (Recommended)

```javascript
import { useApi } from '../hooks/useApi';
import { analyzeMarket } from '../services/api';
import ErrorNotification from '../components/ErrorNotification';

function MyComponent() {
  const { data, loading, error, execute, reset } = useApi(analyzeMarket);

  return (
    <div>
      {error && <ErrorNotification error={error} onDismiss={reset} />}
      {loading && <p>Loading...</p>}
      {data && <p>Buy/Sell Ratio: {data.buy_sell_ratio}</p>}
      <button onClick={() => execute('general')} disabled={loading}>
        Analyze
      </button>
    </div>
  );
}
```

## Available API Functions

### Market Analysis
```javascript
import { analyzeMarket, getRecentNews, getDailySentiment } from '../services/api';

// Analyze market
const analysis = await analyzeMarket('general');

// Get recent news
const news = await getRecentNews(7, 'Positive');

// Get daily sentiment
const sentiment = await getDailySentiment(7);
```

### Stock Data (Future Phase)
```javascript
import { getStockInfo, getStockSentiment, getAccountHoldings } from '../services/api';

// Get stock info
const stock = await getStockInfo('AAPL');

// Get stock sentiment
const sentiment = await getStockSentiment('AAPL');

// Get holdings
const holdings = await getAccountHoldings();
```

### Auto Trading (Future Phase)
```javascript
import { 
  updateTradingConfig, 
  startAutoTrading, 
  stopAutoTrading, 
  getTradeHistory 
} from '../services/api';

// Update config
await updateTradingConfig({
  max_investment: 10000,
  risk_level: 'low',
  stop_loss_threshold: 0.05
});

// Start/stop trading
await startAutoTrading();
await stopAutoTrading();

// Get history
const trades = await getTradeHistory(50);
```

## Error Handling

### Error Object Structure
```javascript
{
  message: "User-friendly error message",
  status: 500,  // HTTP status code (0 for network errors)
  type: "server" // Error type
}
```

### Error Types
- `validation` - Invalid input (400)
- `auth` - Authentication error (401, 403)
- `not_found` - Resource not found (404)
- `rate_limit` - Too many requests (429)
- `server` - Server error (500, 503)
- `network` - Network connection error
- `client` - Client-side error

### Handling Specific Error Types
```javascript
try {
  const result = await analyzeMarket('general');
} catch (error) {
  switch (error.type) {
    case 'network':
      console.log('Check your internet connection');
      break;
    case 'server':
      console.log('Server is experiencing issues');
      break;
    case 'auth':
      console.log('Please log in again');
      break;
    default:
      console.log(error.message);
  }
}
```

## Notifications

### Error Notification
```javascript
import ErrorNotification from '../components/ErrorNotification';

<ErrorNotification 
  error={error}                    // Error object
  onDismiss={() => setError(null)} // Dismiss handler
  autoDismiss={true}                // Auto-dismiss (default: true)
  dismissAfter={5000}               // Dismiss after ms (default: 5000)
/>
```

### Success Notification
```javascript
import SuccessNotification from '../components/SuccessNotification';

<SuccessNotification 
  message="Operation successful!"   // Success message
  onDismiss={() => setSuccess(null)} // Dismiss handler
  autoDismiss={true}                 // Auto-dismiss (default: true)
  dismissAfter={3000}                // Dismiss after ms (default: 3000)
/>
```

## Environment Configuration

### Development (.env)
```bash
VITE_API_BASE_URL=http://localhost:8000
```

### Production (.env.production)
```bash
VITE_API_BASE_URL=https://api.yourdomain.com
```

## Testing API Connectivity

```javascript
import { checkServerHealth } from '../services/api';

const isHealthy = await checkServerHealth();
if (isHealthy) {
  console.log('Backend is reachable');
} else {
  console.log('Backend is not reachable');
}
```

## Common Patterns

### Loading State with Spinner
```javascript
{loading && (
  <div className="flex items-center justify-center">
    <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
    </svg>
    <span className="ml-2">Loading...</span>
  </div>
)}
```

### Disabled Button During Loading
```javascript
<button 
  onClick={handleAnalyze}
  disabled={loading}
  className={`px-4 py-2 rounded ${loading ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'}`}
>
  {loading ? 'Analyzing...' : 'Analyze Market'}
</button>
```

### Multiple API Calls
```javascript
import { useApiMultiple } from '../hooks/useApi';
import { analyzeMarket, getRecentNews } from '../services/api';

function MyComponent() {
  const { loading, error, executeApi, clearError } = useApiMultiple();
  const [analysis, setAnalysis] = useState(null);
  const [news, setNews] = useState(null);

  const loadData = async () => {
    try {
      const [analysisResult, newsResult] = await Promise.all([
        executeApi(analyzeMarket, 'general'),
        executeApi(getRecentNews, 7)
      ]);
      setAnalysis(analysisResult);
      setNews(newsResult);
    } catch (err) {
      // Error is already set by the hook
    }
  };

  return (
    <div>
      {error && <ErrorNotification error={error} onDismiss={clearError} />}
      <button onClick={loadData} disabled={loading}>Load Data</button>
    </div>
  );
}
```

## Best Practices

1. **Always handle errors**: Use try-catch or error states
2. **Show loading states**: Provide visual feedback during API calls
3. **Disable buttons during loading**: Prevent duplicate requests
4. **Use auto-dismiss for notifications**: Don't clutter the UI
5. **Clear errors on retry**: Reset error state before new attempts
6. **Use custom hooks**: Simplify state management with useApi
7. **Check server health**: Verify connectivity before critical operations

## Troubleshooting

### "Unable to connect to the server"
- Check if backend is running: `http://localhost:8000`
- Verify VITE_API_BASE_URL in .env
- Check network connection

### CORS Errors
- Ensure backend has CORS middleware configured
- Check allowed origins include your frontend URL

### Timeout Errors
- Increase timeout in `src/services/api.js` (default: 30s)
- Check if backend operation is taking too long

### 401/403 Errors
- Authentication not yet implemented
- Will be added in future phases

## Next Steps

After completing the integration:
1. Test with actual backend server
2. Implement Phase 3: Stock Integration
3. Implement Phase 4: Auto Trading System
4. Add authentication and authorization
5. Implement real-time updates with WebSockets

## Support

For more detailed information, see:
- `frontend/src/services/README.md` - Comprehensive API documentation
- `frontend/INTEGRATION_SUMMARY.md` - Implementation summary
- Backend API documentation (when available)
