# API Service Documentation

This directory contains the API client and related utilities for communicating with the backend server.

## Overview

The API service provides a centralized interface for all backend communication, with built-in error handling, request/response interceptors, and comprehensive logging.

## Files

- `api.js` - Main API client with all endpoint functions

## Configuration

The API client is configured via environment variables in the `.env` file:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

## Features

### 1. Axios Instance with Interceptors

The API client uses axios with custom interceptors for:
- Request logging (development mode)
- Response logging (development mode)
- Centralized error handling
- Timeout configuration (30 seconds)

### 2. Error Handling

All API errors are transformed into a consistent format:

```javascript
{
  message: "User-friendly error message",
  status: 500,  // HTTP status code
  type: "server" // Error type: 'validation', 'auth', 'network', 'server', etc.
}
```

Error types:
- `validation` (400) - Invalid request data
- `auth` (401, 403) - Authentication/authorization errors
- `not_found` (404) - Resource not found
- `rate_limit` (429) - Too many requests
- `server` (500, 503) - Server errors
- `network` - No response from server
- `client` - Request setup error

### 3. API Functions

#### Market Analysis

```javascript
import { analyzeMarket, getRecentNews, getDailySentiment } from './services/api';

// Analyze market sentiment
const result = await analyzeMarket('general');
// Returns: { buy_sell_ratio, trend_summary, last_updated, vix }

// Get recent news
const news = await getRecentNews(7, 'Positive');
// Returns: Array of news articles

// Get daily sentiment scores
const sentiment = await getDailySentiment(7);
// Returns: Array of daily scores
```

#### Stock Data

```javascript
import { getStockInfo, getStockSentiment, getAccountHoldings } from './services/api';

// Get stock information
const stock = await getStockInfo('AAPL');

// Get stock sentiment
const sentiment = await getStockSentiment('AAPL');

// Get account holdings
const holdings = await getAccountHoldings();
```

#### Auto Trading

```javascript
import { 
  updateTradingConfig, 
  startAutoTrading, 
  stopAutoTrading, 
  getTradeHistory 
} from './services/api';

// Update trading configuration
await updateTradingConfig({
  max_investment: 10000,
  risk_level: 'low',
  stop_loss_threshold: 0.05
});

// Start auto trading
await startAutoTrading();

// Stop auto trading
await stopAutoTrading();

// Get trade history
const trades = await getTradeHistory(50);
```

#### Utility Functions

```javascript
import { checkServerHealth } from './services/api';

// Check if server is reachable
const isHealthy = await checkServerHealth();
```

## Usage Examples

### Basic Usage

```javascript
import { analyzeMarket } from '../services/api';

const handleAnalyze = async () => {
  try {
    const result = await analyzeMarket('general');
    console.log('Analysis result:', result);
  } catch (error) {
    console.error('Error:', error.message);
    // error.type can be used for specific error handling
  }
};
```

### With Custom Hook

```javascript
import { useApi } from '../hooks/useApi';
import { analyzeMarket } from '../services/api';

const MyComponent = () => {
  const { data, loading, error, execute } = useApi(analyzeMarket);

  const handleClick = () => {
    execute('general');
  };

  return (
    <div>
      {loading && <p>Loading...</p>}
      {error && <p>Error: {error.message}</p>}
      {data && <p>Result: {data.buy_sell_ratio}</p>}
      <button onClick={handleClick}>Analyze</button>
    </div>
  );
};
```

### Error Handling with Notification Component

```javascript
import { useState } from 'react';
import { analyzeMarket } from '../services/api';
import ErrorNotification from '../components/ErrorNotification';

const MyComponent = () => {
  const [error, setError] = useState(null);

  const handleAnalyze = async () => {
    try {
      const result = await analyzeMarket('general');
      // Handle success
    } catch (err) {
      setError(err);
    }
  };

  return (
    <div>
      <ErrorNotification 
        error={error} 
        onDismiss={() => setError(null)}
        autoDismiss={true}
        dismissAfter={5000}
      />
      <button onClick={handleAnalyze}>Analyze</button>
    </div>
  );
};
```

## Development

### Adding New Endpoints

1. Add the function to `api.js`:

```javascript
export const myNewEndpoint = async (param) => {
  try {
    const response = await apiClient.get(`/api/my-endpoint/${param}`);
    return response.data;
  } catch (error) {
    throw error;
  }
};
```

2. Add JSDoc comments for better IDE support:

```javascript
/**
 * Description of what this endpoint does
 * @param {string} param - Description of parameter
 * @returns {Promise<Object>} Description of return value
 */
export const myNewEndpoint = async (param) => {
  // ...
};
```

### Testing API Calls

Use the browser console or React DevTools to test API calls:

```javascript
import * as api from './services/api';

// Test in console
api.analyzeMarket('general').then(console.log).catch(console.error);
```

## Troubleshooting

### CORS Issues

If you encounter CORS errors, ensure the backend server has CORS enabled for your frontend domain:

```python
# Backend (FastAPI)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Network Errors

If you get "Unable to connect to the server" errors:
1. Check if the backend server is running
2. Verify the `VITE_API_BASE_URL` in `.env`
3. Check your network connection
4. Use `checkServerHealth()` to test connectivity

### Timeout Errors

If requests are timing out:
1. Increase the timeout in `api.js` (default: 30 seconds)
2. Check if the backend operation is taking too long
3. Consider implementing pagination for large data sets

## Best Practices

1. **Always handle errors**: Use try-catch blocks or error states
2. **Show user feedback**: Display loading states and error messages
3. **Use TypeScript**: Consider adding TypeScript for better type safety
4. **Cache responses**: Implement caching for frequently accessed data
5. **Retry logic**: Add retry logic for transient failures
6. **Rate limiting**: Respect API rate limits and implement client-side throttling

## Future Enhancements

- [ ] Add request cancellation support
- [ ] Implement request retry logic
- [ ] Add request/response caching
- [ ] Support for file uploads
- [ ] WebSocket support for real-time updates
- [ ] Request batching for multiple simultaneous calls
- [ ] Offline support with service workers
