"""
Forex data collection service
Uses exchangerate-api.com (free tier)
"""
import requests
import logging
from datetime import datetime
from typing import Dict, Optional, List
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ForexDataCollector:
    """Collects forex exchange rate data"""
    
    def __init__(self, api_key: Optional[str] = None):
        # Free tier doesn't require API key, but has rate limits
        self.api_key = api_key
        if api_key:
            self.base_url = f"https://v6.exchangerate-api.com/v6/{api_key}"
        else:
            # Using free open exchange rates API as fallback
            self.base_url = "https://open.er-api.com/v6"
        
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json'
        })
    
    def get_supported_currencies(self) -> List[str]:
        """Get list of supported currency codes"""
        # Common forex pairs
        return [
            'USD', 'EUR', 'GBP', 'JPY', 'KRW', 'CNY',
            'AUD', 'CAD', 'CHF', 'HKD', 'SGD', 'NZD',
            'SEK', 'NOK', 'DKK', 'INR', 'BRL', 'ZAR'
        ]
    
    def get_exchange_rate(
        self, 
        base_currency: str, 
        quote_currency: str
    ) -> Optional[Dict]:
        """
        Get current exchange rate
        
        Args:
            base_currency: Base currency code (e.g., 'USD')
            quote_currency: Quote currency code (e.g., 'KRW')
        
        Returns:
            Exchange rate data or None
        """
        try:
            response = self.session.get(
                f"{self.base_url}/latest/{base_currency}",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('result') != 'success':
                logger.error(f"API returned error: {data.get('error-type')}")
                return None
            
            rates = data.get('rates', {})
            rate = rates.get(quote_currency)
            
            if rate is None:
                logger.warning(f"Rate not found for {base_currency}/{quote_currency}")
                return None
            
            return {
                'base_currency': base_currency,
                'quote_currency': quote_currency,
                'rate': rate,
                'timestamp': datetime.utcnow(),
                'last_update': datetime.fromtimestamp(data.get('time_last_update_unix', 0))
            }
        except Exception as e:
            logger.error(f"Failed to fetch exchange rate for {base_currency}/{quote_currency}: {e}")
            return None
    
    def get_multiple_rates(
        self, 
        base_currency: str, 
        quote_currencies: List[str]
    ) -> Dict[str, float]:
        """
        Get multiple exchange rates at once
        
        Args:
            base_currency: Base currency code
            quote_currencies: List of quote currency codes
        
        Returns:
            Dictionary mapping quote currency to rate
        """
        try:
            response = self.session.get(
                f"{self.base_url}/latest/{base_currency}",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('result') != 'success':
                return {}
            
            rates = data.get('rates', {})
            return {
                currency: rates.get(currency)
                for currency in quote_currencies
                if currency in rates
            }
        except Exception as e:
            logger.error(f"Failed to fetch multiple rates: {e}")
            return {}
    
    def get_historical_rate(
        self,
        base_currency: str,
        quote_currency: str,
        date: datetime
    ) -> Optional[float]:
        """
        Get historical exchange rate (requires paid API key)
        
        Args:
            base_currency: Base currency code
            quote_currency: Quote currency code
            date: Historical date
        
        Returns:
            Exchange rate or None
        """
        if not self.api_key:
            logger.warning("Historical data requires API key")
            return None
        
        try:
            date_str = date.strftime('%Y-%m-%d')
            response = self.session.get(
                f"https://v6.exchangerate-api.com/v6/{self.api_key}/history/{base_currency}/{date_str}",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('result') != 'success':
                return None
            
            rates = data.get('rates', {})
            return rates.get(quote_currency)
        except Exception as e:
            logger.error(f"Failed to fetch historical rate: {e}")
            return None
    
    def convert_amount(
        self,
        amount: float,
        from_currency: str,
        to_currency: str
    ) -> Optional[float]:
        """
        Convert amount from one currency to another
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code
        
        Returns:
            Converted amount or None
        """
        rate_data = self.get_exchange_rate(from_currency, to_currency)
        if rate_data:
            return amount * rate_data['rate']
        return None
