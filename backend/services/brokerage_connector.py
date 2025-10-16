"""
Brokerage API Connector Module

This module provides abstract base class and concrete implementations for
connecting to various brokerage APIs (Korean brokerages)

Requirements: 11.1, 11.2, 11.6
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime
from decimal import Decimal
import logging

from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal

from models.trading_schemas import Order, TradeResult


class StockPrice(BaseModel):
    """
    Stock price data transfer object
    Used for returning stock price information from brokerage APIs
    """
    symbol: str
    price: Decimal
    volume: int
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    timestamp: datetime

logger = logging.getLogger(__name__)


class AccountInfo:
    """
    Account information data class
    """
    def __init__(
        self,
        account_number: str,
        balance: Decimal,
        available_cash: Decimal,
        total_assets: Decimal,
        holdings: List[Dict] = None
    ):
        self.account_number = account_number
        self.balance = balance
        self.available_cash = available_cash
        self.total_assets = total_assets
        self.holdings = holdings or []


class BrokerageAPIBase(ABC):
    """
    Abstract base class for brokerage API implementations
    
    All brokerage connectors must implement these methods to ensure
    consistent interface across different brokerages.
    
    Requirements: 11.1
    """
    
    def __init__(self, credentials: Dict[str, str]):
        """
        Initialize brokerage API client
        
        Args:
            credentials: Dictionary containing API credentials
                        (app_key, app_secret, account_number, etc.)
        """
        self.credentials = credentials
        self.is_authenticated = False
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        
    @abstractmethod
    def authenticate(self) -> bool:
        """
        Authenticate with the brokerage API
        
        Returns:
            bool: True if authentication successful, False otherwise
            
        Requirements: 11.1
        """
        pass
    
    @abstractmethod
    def get_stock_price(self, symbol: str) -> StockPrice:
        """
        Get current stock price and trading information
        
        Args:
            symbol: Stock symbol/ticker code
            
        Returns:
            StockPrice: Current price information
            
        Requirements: 11.2
        """
        pass
    
    @abstractmethod
    def get_account_balance(self) -> AccountInfo:
        """
        Get account balance and available cash
        
        Returns:
            AccountInfo: Account information including balance and holdings
            
        Requirements: 11.6
        """
        pass
    
    @abstractmethod
    def get_account_holdings(self) -> List[Dict]:
        """
        Get list of currently held stocks
        
        Returns:
            List[Dict]: List of holdings with symbol, quantity, avg_price, etc.
            
        Requirements: 11.6
        """
        pass
    
    @abstractmethod
    def place_order(self, order: Order) -> TradeResult:
        """
        Place a buy or sell order
        
        Args:
            order: Order details (symbol, type, quantity, price, etc.)
            
        Returns:
            TradeResult: Result of order execution
            
        Requirements: 11.1
        """
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel a pending order
        
        Args:
            order_id: Order identifier to cancel
            
        Returns:
            bool: True if cancellation successful
        """
        pass
    
    @abstractmethod
    def get_order_status(self, order_id: str) -> Dict:
        """
        Get status of a specific order
        
        Args:
            order_id: Order identifier
            
        Returns:
            Dict: Order status information
        """
        pass
    
    def _ensure_authenticated(self) -> None:
        """
        Ensure the client is authenticated before making API calls
        
        Raises:
            RuntimeError: If not authenticated
        """
        if not self.is_authenticated:
            raise RuntimeError(
                f"{self.__class__.__name__} is not authenticated. "
                "Call authenticate() first."
            )
    
    def _is_token_expired(self) -> bool:
        """
        Check if access token has expired
        
        Returns:
            bool: True if token is expired or about to expire
        """
        if not self.token_expires_at:
            return True
        
        # Consider token expired if less than 5 minutes remaining
        from datetime import timedelta
        return datetime.now() >= (self.token_expires_at - timedelta(minutes=5))
    
    def _refresh_token_if_needed(self) -> None:
        """
        Refresh authentication token if expired
        """
        if self._is_token_expired():
            logger.info(f"Token expired for {self.__class__.__name__}, re-authenticating...")
            self.authenticate()


def get_brokerage_api() -> BrokerageAPIBase:
    """
    Factory function to get brokerage API instance
    
    Returns:
        BrokerageAPIBase: Configured brokerage API instance
    
    Note:
        In production, this should read from config/environment to determine
        which brokerage to use and load appropriate credentials.
        For now, returns a mock implementation for testing.
    """
    from services.mock_brokerage import MockBrokerageAPI
    
    # In production, load from config:
    # brokerage_type = os.getenv("BROKERAGE_TYPE", "mock")
    # if brokerage_type == "korea_investment":
    #     from services.korea_investment_api import KoreaInvestmentAPI
    #     return KoreaInvestmentAPI(credentials)
    # elif brokerage_type == "kiwoom":
    #     from services.kiwoom_api import KiwoomAPI
    #     return KiwoomAPI(credentials)
    
    # For testing, return mock
    return MockBrokerageAPI({})
