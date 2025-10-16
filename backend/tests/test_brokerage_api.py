"""
Unit tests for Brokerage API connectors

Tests the abstract base class and concrete implementations
with mocked API responses.

Requirements: 11.1, 11.2, 11.6
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from decimal import Decimal

from services.brokerage_connector import BrokerageAPIBase, AccountInfo, StockPrice
from services.korea_investment_api import KoreaInvestmentAPI
from services.kiwoom_api import KiwoomAPI
from models.trading_schemas import Order, TradeResult


class TestBrokerageAPIBase:
    """Test abstract base class functionality"""
    
    def test_base_class_initialization(self):
        """Test base class can be initialized with credentials"""
        
        class MockBrokerage(BrokerageAPIBase):
            def authenticate(self): return True
            def get_stock_price(self, symbol): pass
            def get_account_balance(self): pass
            def get_account_holdings(self): pass
            def place_order(self, order): pass
            def cancel_order(self, order_id): pass
            def get_order_status(self, order_id): pass
        
        credentials = {"app_key": "test", "app_secret": "secret"}
        broker = MockBrokerage(credentials)
        
        assert broker.credentials == credentials
        assert broker.is_authenticated == False
        assert broker.access_token is None
    
    def test_ensure_authenticated_raises_error(self):
        """Test that _ensure_authenticated raises error when not authenticated"""
        
        class MockBrokerage(BrokerageAPIBase):
            def authenticate(self): return True
            def get_stock_price(self, symbol): pass
            def get_account_balance(self): pass
            def get_account_holdings(self): pass
            def place_order(self, order): pass
            def cancel_order(self, order_id): pass
            def get_order_status(self, order_id): pass
        
        broker = MockBrokerage({})
        
        with pytest.raises(RuntimeError, match="not authenticated"):
            broker._ensure_authenticated()
    
    def test_token_expiration_check(self):
        """Test token expiration checking"""
        
        class MockBrokerage(BrokerageAPIBase):
            def authenticate(self): return True
            def get_stock_price(self, symbol): pass
            def get_account_balance(self): pass
            def get_account_holdings(self): pass
            def place_order(self, order): pass
            def cancel_order(self, order_id): pass
            def get_order_status(self, order_id): pass
        
        broker = MockBrokerage({})
        
        # No token set - should be expired
        assert broker._is_token_expired() == True
        
        # Token expires in 10 minutes - should be considered expired (< 5 min buffer)
        broker.token_expires_at = datetime.now() + timedelta(minutes=3)
        assert broker._is_token_expired() == True
        
        # Token expires in 1 hour - should not be expired
        broker.token_expires_at = datetime.now() + timedelta(hours=1)
        assert broker._is_token_expired() == False


class TestKoreaInvestmentAPI:
    """Test Korea Investment API implementation"""
    
    def test_initialization(self):
        """Test API client initialization"""
        api = KoreaInvestmentAPI(
            app_key="test_key",
            app_secret="test_secret",
            account_number="12345678",
            use_virtual=True
        )
        
        assert api.credentials["app_key"] == "test_key"
        assert api.credentials["app_secret"] == "test_secret"
        assert api.credentials["account_number"] == "12345678"
        assert api.use_virtual == True
        assert api.base_url == KoreaInvestmentAPI.BASE_URL_VIRTUAL
    
    @patch('services.korea_investment_api.requests.post')
    def test_authenticate_success(self, mock_post):
        """Test successful authentication"""
        # Mock successful authentication response
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "test_token_123",
            "expires_in": 86400
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        api = KoreaInvestmentAPI(
            app_key="test_key",
            app_secret="test_secret",
            account_number="12345678"
        )
        
        result = api.authenticate()
        
        assert result == True
        assert api.is_authenticated == True
        assert api.access_token == "test_token_123"
        assert api.token_expires_at is not None
    
    @patch('services.korea_investment_api.requests.post')
    def test_authenticate_failure(self, mock_post):
        """Test authentication failure"""
        # Mock failed authentication with RequestException
        import requests
        mock_post.side_effect = requests.exceptions.RequestException("Connection error")
        
        api = KoreaInvestmentAPI(
            app_key="test_key",
            app_secret="test_secret",
            account_number="12345678"
        )
        
        result = api.authenticate()
        
        assert result == False
        assert api.is_authenticated == False
    
    @patch('services.korea_investment_api.requests.get')
    def test_get_stock_price(self, mock_get):
        """Test getting stock price"""
        # Mock stock price response
        mock_response = Mock()
        mock_response.json.return_value = {
            "rt_cd": "0",
            "output": {
                "stck_prpr": "75000",
                "acml_vol": "1000000",
                "stck_oprc": "74500",
                "stck_hgpr": "75500",
                "stck_lwpr": "74000"
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        api = KoreaInvestmentAPI(
            app_key="test_key",
            app_secret="test_secret",
            account_number="12345678"
        )
        api.is_authenticated = True
        api.access_token = "test_token"
        api.token_expires_at = datetime.now() + timedelta(hours=1)
        
        price = api.get_stock_price("005930")
        
        assert price.symbol == "005930"
        assert price.price == Decimal("75000")
        assert price.volume == 1000000
        assert price.open_price == Decimal("74500")
        assert price.high_price == Decimal("75500")
        assert price.low_price == Decimal("74000")
    
    @patch('services.korea_investment_api.requests.get')
    def test_get_account_balance(self, mock_get):
        """Test getting account balance"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "rt_cd": "0",
            "output": {
                "dnca_tot_amt": "10000000",
                "ord_psbl_cash": "5000000",
                "tot_evlu_amt": "15000000"
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        api = KoreaInvestmentAPI(
            app_key="test_key",
            app_secret="test_secret",
            account_number="12345678"
        )
        api.is_authenticated = True
        api.access_token = "test_token"
        api.token_expires_at = datetime.now() + timedelta(hours=1)
        
        balance = api.get_account_balance()
        
        assert balance.account_number == "12345678"
        assert balance.balance == Decimal("10000000")
        assert balance.available_cash == Decimal("5000000")
        assert balance.total_assets == Decimal("15000000")
    
    @patch('services.korea_investment_api.requests.post')
    def test_place_order_success(self, mock_post):
        """Test placing order successfully"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "rt_cd": "0",
            "msg1": "Order placed successfully",
            "output": {
                "KRX_FWDG_ORD_ORGNO": "12345",
                "ODNO": "67890"
            }
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        api = KoreaInvestmentAPI(
            app_key="test_key",
            app_secret="test_secret",
            account_number="12345678"
        )
        api.is_authenticated = True
        api.access_token = "test_token"
        api.token_expires_at = datetime.now() + timedelta(hours=1)
        
        order = Order(
            symbol="005930",
            trade_type="BUY",
            quantity=10,
            price=Decimal("75000"),
            order_type="LIMIT"
        )
        
        result = api.place_order(order)
        
        assert result.status == "SUCCESS"
        assert result.symbol == "005930"
        assert result.trade_type == "BUY"
        assert result.quantity == 10


class TestKiwoomAPI:
    """Test Kiwoom API placeholder implementation"""
    
    def test_initialization(self):
        """Test Kiwoom API initialization"""
        api = KiwoomAPI(
            account_number="12345678",
            user_id="test_user"
        )
        
        assert api.credentials["account_number"] == "12345678"
        assert api.credentials["user_id"] == "test_user"
    
    def test_authenticate_not_implemented(self):
        """Test that authenticate returns False (not implemented)"""
        api = KiwoomAPI(account_number="12345678")
        
        result = api.authenticate()
        
        assert result == False
        assert api.is_authenticated == False
    
    def test_methods_return_placeholder_values(self):
        """Test that methods return placeholder values"""
        api = KiwoomAPI(account_number="12345678")
        api.is_authenticated = True  # Bypass authentication check
        
        # get_stock_price should return placeholder
        price = api.get_stock_price("005930")
        assert price.price == Decimal("0")
        
        # get_account_balance should return placeholder
        balance = api.get_account_balance()
        assert balance.balance == Decimal("0")
        
        # get_account_holdings should return empty list
        holdings = api.get_account_holdings()
        assert holdings == []


class TestAccountInfo:
    """Test AccountInfo data class"""
    
    def test_account_info_creation(self):
        """Test creating AccountInfo object"""
        info = AccountInfo(
            account_number="12345678",
            balance=Decimal("10000000"),
            available_cash=Decimal("5000000"),
            total_assets=Decimal("15000000"),
            holdings=[{"symbol": "005930", "quantity": 10}]
        )
        
        assert info.account_number == "12345678"
        assert info.balance == Decimal("10000000")
        assert info.available_cash == Decimal("5000000")
        assert info.total_assets == Decimal("15000000")
        assert len(info.holdings) == 1
    
    def test_account_info_without_holdings(self):
        """Test creating AccountInfo without holdings"""
        info = AccountInfo(
            account_number="12345678",
            balance=Decimal("10000000"),
            available_cash=Decimal("5000000"),
            total_assets=Decimal("15000000")
        )
        
        assert info.holdings == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
