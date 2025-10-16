"""

Integration Tests for Brokerage API Connectors



This module provides comprehensive integration tests for brokerage APIs,

including both mock API tests and real API connection tests.



Requirements: 11.1, 11.7



Test Categories:

1. Mock API Integration Tests - Always runnable with mocked responses

2. Real API Integration Tests - Requires valid credentials (marked with @pytest.mark.integration)



Usage:

    # Run only mock tests (default)

    pytest tests/test_brokerage_integration.py -m "not integration"

    

    # Run all tests including real API tests

    pytest tests/test_brokerage_integration.py

    

    # Run only real API tests

    pytest tests/test_brokerage_integration.py -m integration

"""



import pytest

import os

from unittest.mock import Mock, patch, MagicMock

from datetime import datetime, timedelta

from decimal import Decimal

from typing import Dict, Any



from services.brokerage_connector import BrokerageAPIBase, AccountInfo, StockPrice

from services.korea_investment_api import KoreaInvestmentAPI

from models.trading_schemas import Order, TradeResult





# ============================================================================

# Test Fixtures

# ============================================================================



@pytest.fixture

def mock_korea_investment_credentials():

    """Provide mock credentials for testing"""

    return {

        "app_key": "mock_app_key_12345",

        "app_secret": "mock_app_secret_67890",

        "account_number": "12345678",

        "account_product_code": "01"

    }





@pytest.fixture

def real_korea_investment_credentials():

    """Provide real credentials from environment variables"""

    return {

        "app_key": os.getenv("KOREA_INVESTMENT_APP_KEY", ""),

        "app_secret": os.getenv("KOREA_INVESTMENT_APP_SECRET", ""),

        "account_number": os.getenv("KOREA_INVESTMENT_ACCOUNT_NUMBER", ""),

        "account_product_code": os.getenv("KOREA_INVESTMENT_ACCOUNT_PRODUCT_CODE", "01")

    }





@pytest.fixture

def mock_api_client(mock_korea_investment_credentials):

    """Create a Korea Investment API client with mock credentials"""

    return KoreaInvestmentAPI(

        app_key=mock_korea_investment_credentials["app_key"],

        app_secret=mock_korea_investment_credentials["app_secret"],

        account_number=mock_korea_investment_credentials["account_number"],

        use_virtual=True

    )





@pytest.fixture

def authenticated_mock_client(mock_api_client):

    """Create an authenticated mock client"""

    mock_api_client.is_authenticated = True

    mock_api_client.access_token = "mock_token_abc123"

    mock_api_client.token_expires_at = datetime.now() + timedelta(hours=1)

    return mock_api_client





# ============================================================================

# Mock API Integration Tests

# ============================================================================



class TestMockAPIIntegration:

    """

    Integration tests using mocked API responses

    These tests verify the complete flow without requiring real API access

    

    Requirements: 11.1, 11.7

    """

    

    @patch('services.korea_investment_api.requests.post')

    def test_complete_authentication_flow(self, mock_post, mock_api_client):

        """

        Test complete authentication flow with mock API

        

        Verifies:

        - Authentication request is properly formatted

        - Token is stored correctly

        - Expiration time is calculated

        """

        # Mock successful authentication response

        mock_response = Mock()

        mock_response.json.return_value = {

            "access_token": "mock_access_token_xyz789",

            "token_type": "Bearer",

            "expires_in": 86400

        }

        mock_response.raise_for_status = Mock()

        mock_post.return_value = mock_response

        

        # Execute authentication

        result = mock_api_client.authenticate()

        

        # Verify results

        assert result is True

        assert mock_api_client.is_authenticated is True

        assert mock_api_client.access_token == "mock_access_token_xyz789"

        assert mock_api_client.token_expires_at is not None

        

        # Verify token expiration is approximately 24 hours from now

        time_diff = mock_api_client.token_expires_at - datetime.now()

        assert 86300 < time_diff.total_seconds() < 86500  # Allow 100 second variance

        

        # Verify API call was made correctly

        mock_post.assert_called_once()

        call_args = mock_post.call_args

        assert "oauth2/tokenP" in call_args[0][0]

    

    @patch('services.korea_investment_api.requests.get')

    def test_stock_price_retrieval_flow(self, mock_get, authenticated_mock_client):

        """

        Test complete stock price retrieval flow

        

        Verifies:

        - Stock price request is properly formatted

        - Response is correctly parsed

        - StockPrice object is created with correct data

        """

        # Mock stock price response

        mock_response = Mock()

        mock_response.json.return_value = {

            "rt_cd": "0",

            "msg_cd": "MCA00000",

            "msg1": "?�상처리 ?�었?�니??",

            "output": {

                "stck_prpr": "75000",      # _재가"

                "acml_vol": "15234567",    # _적 거래"
                "stck_oprc": "74500",      # _�"
                "stck_hgpr": "75800",      # 고�?

                "stck_lwpr": "74200"       # _가"

            }

        }

        mock_response.raise_for_status = Mock()

        mock_get.return_value = mock_response

        

        # Execute stock price retrieval

        stock_price = authenticated_mock_client.get_stock_price("005930")

        

        # Verify results

        assert isinstance(stock_price, StockPrice)

        assert stock_price.symbol == "005930"

        assert stock_price.price == Decimal("75000")

        assert stock_price.volume == 15234567

        assert stock_price.open_price == Decimal("74500")

        assert stock_price.high_price == Decimal("75800")

        assert stock_price.low_price == Decimal("74200")

        assert isinstance(stock_price.timestamp, datetime)

        

        # Verify API call

        mock_get.assert_called_once()

        call_args = mock_get.call_args

        assert "inquire-price" in call_args[0][0]

    

    @patch('services.korea_investment_api.requests.get')

    def test_account_balance_retrieval_flow(self, mock_get, authenticated_mock_client):

        """

        Test complete account balance retrieval flow

        

        Verifies:

        - Account balance request is properly formatted

        - Response is correctly parsed

        - AccountInfo object is created with correct data

        """

        # Mock account balance response

        mock_response = Mock()

        mock_response.json.return_value = {

            "rt_cd": "0",

            "msg_cd": "MCA00000",

            "msg1": "?�상처리 ?�었?�니??",

            "output": {

                "dnca_tot_amt": "10000000",    # _수�"
                "ord_psbl_cash": "8500000",    # 주문 가??_금"

                "tot_evlu_amt": "15000000"     # �?_�"
        assert account_info.account_number == "12345678"

        assert account_info.balance == Decimal("10000000")

        assert account_info.available_cash == Decimal("8500000")

        assert account_info.total_assets == Decimal("15000000")

        

        # Verify API call

        mock_get.assert_called_once()

    

    @patch('services.korea_investment_api.requests.get')

    def test_account_holdings_retrieval_flow(self, mock_get, authenticated_mock_client):

        """

        Test complete account holdings retrieval flow

        

        Verifies:

        - Holdings request is properly formatted

        - Multiple holdings are correctly parsed

        - Profit/loss calculations are included

        """

        # Mock holdings response with multiple stocks

        mock_response = Mock()

        mock_response.json.return_value = {

            "rt_cd": "0",

            "msg_cd": "MCA00000",

            "msg1": "?�상처리 ?�었?�니??",

            "output1": [

                {

                    "pdno": "005930",              # _성"
                    "prdt_name": "?�성?�자",

                    "hldg_qty": "100",             # 보유 _량"

                    "pchs_avg_pric": "70000",      # 매입 _균가"

                    "prpr": "75000",               # _재가"

                    "evlu_amt": "7500000",         # _�"
                    "evlu_pfls_amt": "500000",     # _�"
                    "evlu_pfls_rt": "7.14"         # _익�"
                    "pdno": "000660",              # SK_이"
                    "prdt_name": "SK?�이?�스",

                    "hldg_qty": "50",

                    "pchs_avg_pric": "120000",

                    "prpr": "115000",

                    "evlu_amt": "5750000",

                    "evlu_pfls_amt": "-250000",

                    "evlu_pfls_rt": "-4.17"

                }

            ]

        }

        mock_response.raise_for_status = Mock()

        mock_get.return_value = mock_response

        

        # Execute holdings retrieval

        holdings = authenticated_mock_client.get_account_holdings()

        

        # Verify results

        assert isinstance(holdings, list)

        assert len(holdings) == 2

        

        # Verify first holding (Samsung Electronics)

        samsung = holdings[0]

        assert samsung["symbol"] == "005930"

        assert samsung["name"] == "?�성?�자"

        assert samsung["quantity"] == 100

        assert samsung["average_price"] == Decimal("70000")

        assert samsung["current_price"] == Decimal("75000")

        assert samsung["profit_loss"] == Decimal("500000")

        

        # Verify second holding (SK Hynix)

        sk = holdings[1]

        assert sk["symbol"] == "000660"

        assert sk["quantity"] == 50

        assert sk["profit_loss"] == Decimal("-250000")

    

    @patch('services.korea_investment_api.requests.post')

    def test_buy_order_placement_flow(self, mock_post, authenticated_mock_client):

        """

        Test complete buy order placement flow

        

        Verifies:

        - Buy order request is properly formatted

        - Order result is correctly parsed

        - Order ID is generated correctly

        """

        # Mock successful order response

        mock_response = Mock()

        mock_response.json.return_value = {

            "rt_cd": "0",

            "msg_cd": "MCA00000",

            "msg1": "주문???�상?�으�??�수?�었?�니??",

            "output": {

                "KRX_FWDG_ORD_ORGNO": "12345",

                "ODNO": "0000067890",

                "ORD_TMD": "153045"

            }

        }

        mock_response.raise_for_status = Mock()

        mock_post.return_value = mock_response

        

        # Create buy order

        order = Order(

            symbol="005930",

            trade_type="BUY",

            quantity=10,

            price=Decimal("75000"),

            order_type="LIMIT"

        )

        

        # Execute order placement

        result = authenticated_mock_client.place_order(order)

        

        # Verify results

        assert isinstance(result, TradeResult)

        assert result.status == "SUCCESS"

        assert result.symbol == "005930"

        assert result.trade_type == "BUY"

        assert result.quantity == 10

        assert result.executed_price == Decimal("75000")

        assert result.order_id == "123450000067890"

        

        # Verify API call

        mock_post.assert_called_once()

        call_args = mock_post.call_args

        assert "order-cash" in call_args[0][0]

    

    @patch('services.korea_investment_api.requests.post')

    def test_sell_order_placement_flow(self, mock_post, authenticated_mock_client):

        """

        Test complete sell order placement flow

        

        Verifies:

        - Sell order uses correct transaction ID

        - Limit order is handled correctly

        """

        # Mock successful sell order response

        mock_response = Mock()

        mock_response.json.return_value = {

            "rt_cd": "0",

            "msg_cd": "MCA00000",

            "msg1": "주문???�상?�으�??�수?�었?�니??",

            "output": {

                "KRX_FWDG_ORD_ORGNO": "54321",

                "ODNO": "0000098765"

            }

        }

        mock_response.raise_for_status = Mock()

        mock_post.return_value = mock_response

        

        # Create limit sell order with price

        order = Order(

            symbol="005930",

            trade_type="SELL",

            quantity=5,

            price=Decimal("76000"),

            order_type="LIMIT"

        )

        

        # Execute order placement

        result = authenticated_mock_client.place_order(order)

        

        # Verify results

        assert result.status == "SUCCESS"

        assert result.trade_type == "SELL"

        assert result.quantity == 5

        assert result.executed_price == Decimal("76000")

    

    @patch('services.korea_investment_api.requests.post')

    def test_order_placement_failure_handling(self, mock_post, authenticated_mock_client):

        """

        Test order placement failure handling

        

        Verifies:

        - Failed orders return appropriate status

        - Error messages are captured

        

        Note: For failed orders, we use a minimal valid price (0.01) to satisfy

        Pydantic validation while still representing a failed order

        """

        # Mock failed order response

        mock_response = Mock()

        mock_response.json.return_value = {

            "rt_cd": "1",

            "msg_cd": "40310000",

            "msg1": "주문가?�금?�을 초과?��??�니??"

        }

        mock_response.raise_for_status = Mock()

        mock_post.return_value = mock_response

        

        # Create order that will fail

        order = Order(

            symbol="005930",

            trade_type="BUY",

            quantity=1000,

            price=Decimal("75000"),

            order_type="LIMIT"

        )

        

        # Execute order placement

        result = authenticated_mock_client.place_order(order)

        

        # Verify failure is handled correctly

        assert result.status == "FAILED"

        assert "주문가_금"
        """

        Test order cancellation flow

        

        Verifies:

        - Order cancellation request is properly formatted

        - Cancellation result is correctly interpreted

        """

        # Mock successful cancellation response

        mock_response = Mock()

        mock_response.json.return_value = {

            "rt_cd": "0",

            "msg_cd": "MCA00000",

            "msg1": "주문???�상?�으�?취소?�었?�니??"

        }

        mock_response.raise_for_status = Mock()

        mock_post.return_value = mock_response

        

        # Execute order cancellation

        result = authenticated_mock_client.cancel_order("123450000067890")

        

        # Verify results

        assert result is True

        

        # Verify API call

        mock_post.assert_called_once()

        call_args = mock_post.call_args

        assert "order-rvsecncl" in call_args[0][0]

    

    @patch('services.korea_investment_api.requests.get')

    def test_order_status_query_flow(self, mock_get, authenticated_mock_client):

        """

        Test order status query flow

        

        Verifies:

        - Order status request is properly formatted

        - Status information is correctly parsed

        """

        # Mock order status response

        mock_response = Mock()

        mock_response.json.return_value = {

            "rt_cd": "0",

            "msg_cd": "MCA00000",

            "msg1": "?�상처리 ?�었?�니??",

            "output1": [

                {

                    "pdno": "005930",

                    "sll_buy_dvsn_cd_name": "매수",

                    "ord_qty": "10",

                    "tot_ccld_qty": "10",

                    "ord_unpr": "75000",

                    "avg_prvs": "75000",

                    "ord_dvsn_name": "지?��?",

                    "ord_tmd": "153045"

                }

            ]

        }

        mock_response.raise_for_status = Mock()

        mock_get.return_value = mock_response

        

        # Execute order status query

        status = authenticated_mock_client.get_order_status("123450000067890")

        

        # Verify results

        assert isinstance(status, dict)

        assert status["symbol"] == "005930"

        assert status["quantity"] == 10

        assert status["executed_quantity"] == 10

        assert status["order_price"] == Decimal("75000")

        assert status["status"] == "지?��?"

    

    @patch('services.korea_investment_api.requests.post')

    def test_token_refresh_on_expiration(self, mock_post, mock_api_client):

        """

        Test automatic token refresh when expired

        

        Verifies:

        - Expired tokens trigger re-authentication

        - New token is obtained automatically

        """

        # Set up expired token

        mock_api_client.is_authenticated = True

        mock_api_client.access_token = "old_expired_token"

        mock_api_client.token_expires_at = datetime.now() - timedelta(hours=1)

        

        # Mock re-authentication response

        mock_response = Mock()

        mock_response.json.return_value = {

            "access_token": "new_refreshed_token",

            "expires_in": 86400

        }

        mock_response.raise_for_status = Mock()

        mock_post.return_value = mock_response

        

        # Trigger token refresh

        mock_api_client._refresh_token_if_needed()

        

        # Verify new token was obtained

        assert mock_api_client.access_token == "new_refreshed_token"

        assert mock_api_client.token_expires_at > datetime.now()





# ============================================================================

# Real API Integration Tests

# ============================================================================



class TestRealAPIIntegration:

    """

    Integration tests with real API connections

    These tests require valid credentials and are marked with @pytest.mark.integration

    

    Requirements: 11.1, 11.7

    

    Note: These tests will be skipped if credentials are not available

    """

    

    @pytest.mark.integration

    def test_real_authentication(self, real_korea_investment_credentials):

        """

        Test authentication with real Korea Investment API

        

        Requires: Valid KOREA_INVESTMENT_APP_KEY and KOREA_INVESTMENT_APP_SECRET

        """

        # Skip if credentials not available

        if not real_korea_investment_credentials["app_key"]:

            pytest.skip("Real API credentials not available")

        

        # Create real API client

        api = KoreaInvestmentAPI(

            app_key=real_korea_investment_credentials["app_key"],

            app_secret=real_korea_investment_credentials["app_secret"],

            account_number=real_korea_investment_credentials["account_number"],

            use_virtual=True  # Use virtual trading for safety

        )

        

        # Attempt authentication

        result = api.authenticate()

        

        # Verify authentication succeeded

        assert result is True, "Real API authentication failed"

        assert api.is_authenticated is True

        assert api.access_token is not None

        assert len(api.access_token) > 0

        

        print(f"\n??Real API authentication successful")

        print(f"  Token expires at: {api.token_expires_at}")

    

    @pytest.mark.integration

    def test_real_stock_price_query(self, real_korea_investment_credentials):

        """

        Test stock price query with real API

        

        Requires: Valid credentials and authenticated session

        """

        if not real_korea_investment_credentials["app_key"]:

            pytest.skip("Real API credentials not available")

        

        # Create and authenticate API client

        api = KoreaInvestmentAPI(

            app_key=real_korea_investment_credentials["app_key"],

            app_secret=real_korea_investment_credentials["app_secret"],

            account_number=real_korea_investment_credentials["account_number"],

            use_virtual=True

        )

        

        auth_result = api.authenticate()

        assert auth_result is True, "Authentication failed"

        

        # Query Samsung Electronics stock price

        stock_price = api.get_stock_price("005930")

        

        # Verify response

        assert isinstance(stock_price, StockPrice)

        assert stock_price.symbol == "005930"

        assert stock_price.price > 0

        assert stock_price.volume >= 0

        

        print(f"\n??Real stock price query successful")

        print(f"  Symbol: {stock_price.symbol}")

        print(f"  Price: {stock_price.price:,} KRW")

        print(f"  Volume: {stock_price.volume:,}")

    

    @pytest.mark.integration

    def test_real_account_balance_query(self, real_korea_investment_credentials):

        """

        Test account balance query with real API

        

        Requires: Valid credentials and account number

        """

        if not real_korea_investment_credentials["app_key"]:

            pytest.skip("Real API credentials not available")

        

        # Create and authenticate API client

        api = KoreaInvestmentAPI(

            app_key=real_korea_investment_credentials["app_key"],

            app_secret=real_korea_investment_credentials["app_secret"],

            account_number=real_korea_investment_credentials["account_number"],

            use_virtual=True

        )

        

        auth_result = api.authenticate()

        assert auth_result is True, "Authentication failed"

        

        # Query account balance

        account_info = api.get_account_balance()

        

        # Verify response

        assert isinstance(account_info, AccountInfo)

        assert account_info.account_number == real_korea_investment_credentials["account_number"]

        assert account_info.balance >= 0

        assert account_info.available_cash >= 0

        

        print(f"\n??Real account balance query successful")

        print(f"  Account: {account_info.account_number}")

        print(f"  Balance: {account_info.balance:,} KRW")

        print(f"  Available: {account_info.available_cash:,} KRW")

    

    @pytest.mark.integration

    def test_real_account_holdings_query(self, real_korea_investment_credentials):

        """

        Test account holdings query with real API

        

        Requires: Valid credentials and account number

        """

        if not real_korea_investment_credentials["app_key"]:

            pytest.skip("Real API credentials not available")

        

        # Create and authenticate API client

        api = KoreaInvestmentAPI(

            app_key=real_korea_investment_credentials["app_key"],

            app_secret=real_korea_investment_credentials["app_secret"],

            account_number=real_korea_investment_credentials["account_number"],

            use_virtual=True

        )

        

        auth_result = api.authenticate()

        assert auth_result is True, "Authentication failed"

        

        # Query account holdings

        holdings = api.get_account_holdings()

        

        # Verify response

        assert isinstance(holdings, list)

        

        print(f"\n??Real account holdings query successful")

        print(f"  Number of holdings: {len(holdings)}")

        

        if holdings:

            for holding in holdings[:3]:  # Show first 3 holdings

                print(f"  - {holding['name']} ({holding['symbol']}): {holding['quantity']} shares")





# ============================================================================

# Error Handling and Edge Cases

# ============================================================================



class TestErrorHandling:

    """

    Test error handling and edge cases

    

    Requirements: 11.7

    """

    

    def test_unauthenticated_api_call_raises_error(self, mock_api_client):

        """Test that API calls without authentication raise appropriate errors"""

        with pytest.raises(RuntimeError, match="not authenticated"):

            mock_api_client.get_stock_price("005930")

    

    @patch('services.korea_investment_api.requests.post')

    def test_network_error_handling(self, mock_post, mock_api_client):

        """Test handling of network errors during authentication"""

        import requests

        mock_post.side_effect = requests.exceptions.ConnectionError("Network unreachable")

        

        result = mock_api_client.authenticate()

        

        assert result is False

        assert mock_api_client.is_authenticated is False

    

    @patch('services.korea_investment_api.requests.get')

    def test_api_error_response_handling(self, mock_get, authenticated_mock_client):

        """Test handling of API error responses"""

        # Mock API error response

        mock_response = Mock()

        mock_response.json.return_value = {

            "rt_cd": "1",

            "msg_cd": "EGW00123",

            "msg1": "조회?????�는 ?�이?��? ?�습?�다."

        }

        mock_response.raise_for_status = Mock()

        mock_get.return_value = mock_response

        

        # Should raise ValueError with error message

        with pytest.raises(ValueError, match="조회?????�는 ?�이?��? ?�습?�다"):

            authenticated_mock_client.get_stock_price("999999")

    

    @patch('services.korea_investment_api.requests.post')

    def test_timeout_handling(self, mock_post, mock_api_client):

        """Test handling of request timeouts"""

        import requests

        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

        

        result = mock_api_client.authenticate()

        

        assert result is False





if __name__ == "__main__":

    # Run tests with verbose output

    pytest.main([__file__, "-v", "-m", "not integration"])

