"""
Cryptocurrency data collection service
Uses CoinGecko API (free tier)
"""
import requests
import logging
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class CryptoDataCollector:
    """Collects cryptocurrency data from CoinGecko API"""
    
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json'
        })
    
    def get_supported_coins(self) -> List[Dict]:
        """Get list of supported cryptocurrencies"""
        try:
            response = self.session.get(
                f"{self.base_url}/coins/markets",
                params={
                    'vs_currency': 'usd',
                    'order': 'market_cap_desc',
                    'per_page': 100,
                    'page': 1,
                    'sparkline': False
                },
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch supported coins: {e}")
            return []
    
    def get_price_data(self, coin_id: str, vs_currency: str = 'usd') -> Optional[Dict]:
        """
        Get current price data for a cryptocurrency
        
        Args:
            coin_id: CoinGecko coin ID (e.g., 'bitcoin', 'ethereum')
            vs_currency: Quote currency (default: 'usd')
        
        Returns:
            Price data dictionary or None
        """
        try:
            response = self.session.get(
                f"{self.base_url}/coins/{coin_id}",
                params={
                    'localization': False,
                    'tickers': False,
                    'market_data': True,
                    'community_data': False,
                    'developer_data': False,
                    'sparkline': False
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            market_data = data.get('market_data', {})
            current_price = market_data.get('current_price', {}).get(vs_currency)
            
            if current_price is None:
                return None
            
            return {
                'symbol': data.get('symbol', '').upper(),
                'name': data.get('name', ''),
                'current_price': current_price,
                'market_cap': market_data.get('market_cap', {}).get(vs_currency),
                'total_volume': market_data.get('total_volume', {}).get(vs_currency),
                'high_24h': market_data.get('high_24h', {}).get(vs_currency),
                'low_24h': market_data.get('low_24h', {}).get(vs_currency),
                'price_change_24h': market_data.get('price_change_24h'),
                'price_change_percentage_24h': market_data.get('price_change_percentage_24h'),
                'timestamp': datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Failed to fetch price data for {coin_id}: {e}")
            return None
    
    def get_historical_data(
        self, 
        coin_id: str, 
        vs_currency: str = 'usd',
        days: int = 7
    ) -> List[Dict]:
        """
        Get historical price data
        
        Args:
            coin_id: CoinGecko coin ID
            vs_currency: Quote currency
            days: Number of days of historical data
        
        Returns:
            List of price data points
        """
        try:
            response = self.session.get(
                f"{self.base_url}/coins/{coin_id}/market_chart",
                params={
                    'vs_currency': vs_currency,
                    'days': days,
                    'interval': 'hourly' if days <= 7 else 'daily'
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            prices = data.get('prices', [])
            volumes = data.get('total_volumes', [])
            market_caps = data.get('market_caps', [])
            
            result = []
            for i, (timestamp, price) in enumerate(prices):
                result.append({
                    'timestamp': datetime.fromtimestamp(timestamp / 1000),
                    'close_price': price,
                    'volume': volumes[i][1] if i < len(volumes) else None,
                    'market_cap': market_caps[i][1] if i < len(market_caps) else None
                })
            
            return result
        except Exception as e:
            logger.error(f"Failed to fetch historical data for {coin_id}: {e}")
            return []
    
    def search_coin(self, query: str) -> List[Dict]:
        """
        Search for cryptocurrencies by name or symbol
        
        Args:
            query: Search query
        
        Returns:
            List of matching coins
        """
        try:
            response = self.session.get(
                f"{self.base_url}/search",
                params={'query': query},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return data.get('coins', [])
        except Exception as e:
            logger.error(f"Failed to search coins: {e}")
            return []
