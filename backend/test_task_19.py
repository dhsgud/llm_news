"""
Test suite for Task 19: Auto Trading Engine
Tests signal processing, order execution, position monitoring, and notifications
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import models and services
from app.database import Base
from models.auto_trade_config import AutoTradeConfig
from models.trade_history import TradeHistory
from models.account_holding import AccountHolding
from services.auto_trading_engine import AutoTradingEngine, TradeAction
from services.risk_manager import RiskManager
from services.signal_generator import SignalCalculator
from services.brokerage_connector import BrokerageAPIBase, StockPrice, AccountInfo
from models.trading_schemas import Order, TradeResult


# Test database setup
@pytest.fixture(scope="function")
def db_session():
    """Create test database session"""
    import tempfile
    import os
    
    # Use a temporary file database to avoid index conflicts
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()
    
    # Clean up
    try:
        os.unlink(db_path)
    except:
        pass


@pytest.fixture
def mock_brokerage():
    """Create mock brokerage API"""
    brokerage = Mock(spec=BrokerageAPIBase)
    
    # Mock stock price
    brokerage.get_stock_price.return_value = StockPrice(
        symbol="005930",
        price=Decimal("75000.00"),
        volume=1000000,
        open_price=Decimal("74500.00"),
        high_price=Decimal("75500.00"),
        low_price=Decimal("74000.00"),
        timestamp=datetime.now()
    )
    
    # Mock account info
    brokerage.get_account_balance.return_value = AccountInfo(
        account_number="12345678",
        balance=Decimal("10000000.00"),
        available_cash=Decimal("10000000.00"),
        total_assets=Decimal("10000000.00"),
        holdings=[]
    )
    
    # Mock holdings
    brokerage.get_account_holdings.return_value = [
        {
            "symbol": "005930",
            "quantity": 10,
            "average_price": Decimal("74000.00")
        }
    ]
    
    # Mock order execution - dynamically respond based on order
    def mock_place_order(order):
        return TradeResult(
            order_id="ORD123456",
            symbol=order.symbol,
            trade_type=order.trade_type,
            quantity=order.quantity,
            executed_price=Decimal("75000.00"),
            total_amount=Decimal("75000.00") * order.quantity,
            executed_at=datetime.now(),
            status="SUCCESS",
            message="Order executed successfully"
        )
    
    brokerage.place_order.side_effect = mock_place_order
    
    return brokerage


@pytest.fixture
def test_config(db_session):
    """Create test auto-trade configuration"""
    config = AutoTradeConfig(
        user_id="test_user",
        is_enabled=True,
        max_investment_amount=Decimal("10000000.00"),
        max_position_size=Decimal("2000000.00"),
        risk_level="MEDIUM",
        buy_threshold=80,
        sell_threshold=20,
        stop_loss_percentage=Decimal("5.0"),
        daily_loss_limit=Decimal("500000.00"),
        trading_start_time="09:00",
        trading_end_time="15:30",
        notification_enabled=True,
        notification_email="[email]"
    )
    db_session.add(config)
    db_session.flush()  # Use flush instead of commit to keep transaction open
    return config


@pytest.fixture
def trading_engine(db_session, mock_brokerage):
    """Create auto trading engine instance"""
    return AutoTradingEngine(
        db=db_session,
        brokerage_api=mock_brokerage
    )


class TestAutoTradingEngine:
    """Test auto trading engine functionality"""
    
    def test_engine_initialization(self, trading_engine):
        """Test engine initializes correctly"""
        assert trading_engine is not None
        assert trading_engine.is_running is False
        assert trading_engine.last_check_time is None
    
    def test_start_trading(self, trading_engine, test_config):
        """Test starting auto trading"""
        result = trading_engine.start(test_config)
        
        assert result["success"] is True
        assert "started" in result["message"].lower()
        assert trading_engine.is_running is True
    
    def test_start_trading_disabled_config(self, trading_engine, test_config):
        """Test starting with disabled configuration"""
        test_config.is_enabled = False
        result = trading_engine.start(test_config)
        
        assert result["success"] is False
        assert "disabled" in result["message"].lower()
    
    def test_stop_trading(self, trading_engine, test_config):
        """Test stopping auto trading"""
        trading_engine.start(test_config)
        result = trading_engine.stop(test_config, "Test stop")
        
        assert result["success"] is True
        assert "stopped" in result["message"].lower()
        assert trading_engine.is_running is False
        assert test_config.is_enabled is False
    
    def test_determine_action_buy(self, trading_engine, test_config):
        """Test action determination for buy signal"""
        action = trading_engine._determine_action(test_config, 85)
        assert action == TradeAction.BUY
    
    def test_determine_action_sell(self, trading_engine, test_config):
        """Test action determination for sell signal"""
        action = trading_engine._determine_action(test_config, 15)
        assert action == TradeAction.SELL
    
    def test_determine_action_hold(self, trading_engine, test_config):
        """Test action determination for hold signal"""
        action = trading_engine._determine_action(test_config, 50)
        assert action == TradeAction.HOLD
    
    def test_process_signal_hold(self, trading_engine, test_config):
        """Test processing signal that results in hold"""
        result = trading_engine.process_signal(
            test_config,
            "005930",
            50,
            "Neutral sentiment"
        )
        
        assert result["success"] is True
        assert result["action"] == "HOLD"
    
    def test_process_signal_buy(self, trading_engine, test_config, mock_brokerage):
        """Test processing buy signal"""
        result = trading_engine.process_signal(
            test_config,
            "005930",
            85,
            "Strong positive sentiment"
        )
        
        assert result["success"] is True
        assert result["action"] == "BUY"
        assert result["symbol"] == "005930"
        assert "order_id" in result
        
        # Verify brokerage API was called
        mock_brokerage.place_order.assert_called_once()
    
    def test_process_signal_sell(self, trading_engine, test_config, mock_brokerage):
        """Test processing sell signal"""
        result = trading_engine.process_signal(
            test_config,
            "005930",
            15,
            "Strong negative sentiment"
        )
        
        assert result["success"] is True
        assert result["action"] == "SELL"
        assert result["symbol"] == "005930"
        
        # Verify brokerage API was called
        mock_brokerage.place_order.assert_called()
    
    def test_process_signal_disabled(self, trading_engine, test_config):
        """Test processing signal when trading is disabled"""
        test_config.is_enabled = False
        
        result = trading_engine.process_signal(
            test_config,
            "005930",
            85,
            "Strong positive sentiment"
        )
        
        assert result["success"] is False
        assert "disabled" in result["message"].lower()
    
    def test_execute_buy_success(self, trading_engine, test_config, mock_brokerage, db_session):
        """Test successful buy execution"""
        holdings_info = {
            "cash_balance": Decimal("10000000.00"),
            "invested_amount": Decimal("0.00"),
            "holdings": []
        }
        
        result = trading_engine._execute_buy(
            test_config,
            "005930",
            85,
            Decimal("75000.00"),
            holdings_info,
            "Test buy"
        )
        
        assert result["success"] is True
        assert result["action"] == "BUY"
        assert result["quantity"] > 0
        
        # Verify trade was recorded
        trade = db_session.query(TradeHistory).filter_by(user_id="test_user").first()
        assert trade is not None
        assert trade.trade_type == "BUY"
    
    def test_execute_buy_insufficient_funds(self, trading_engine, test_config):
        """Test buy execution with insufficient funds"""
        holdings_info = {
            "cash_balance": Decimal("1000.00"),  # Not enough
            "invested_amount": Decimal("0.00"),
            "holdings": []
        }
        
        result = trading_engine._execute_buy(
            test_config,
            "005930",
            85,
            Decimal("75000.00"),
            holdings_info,
            "Test buy"
        )
        
        assert result["success"] is False
        assert ("validation failed" in result["message"].lower() or 
                "position size is 0" in result["message"].lower())
    
    def test_execute_sell_success(self, trading_engine, test_config, mock_brokerage, db_session):
        """Test successful sell execution"""
        holdings_info = {
            "cash_balance": Decimal("10000000.00"),
            "invested_amount": Decimal("740000.00"),
            "holdings": [
                {
                    "symbol": "005930",
                    "quantity": 10,
                    "average_price": Decimal("74000.00")
                }
            ]
        }
        
        result = trading_engine._execute_sell(
            test_config,
            "005930",
            15,
            Decimal("75000.00"),
            holdings_info,
            "Test sell"
        )
        
        assert result["success"] is True
        assert result["action"] == "SELL"
        assert result["quantity"] == 10
        assert "profit_loss" in result
        
        # Verify trade was recorded
        trade = db_session.query(TradeHistory).filter_by(user_id="test_user").first()
        assert trade is not None
        assert trade.trade_type == "SELL"
    
    def test_execute_sell_no_holdings(self, trading_engine, test_config):
        """Test sell execution with no holdings"""
        holdings_info = {
            "cash_balance": Decimal("10000000.00"),
            "invested_amount": Decimal("0.00"),
            "holdings": []
        }
        
        result = trading_engine._execute_sell(
            test_config,
            "005930",
            15,
            Decimal("75000.00"),
            holdings_info,
            "Test sell"
        )
        
        assert result["success"] is False
        assert "no holdings" in result["message"].lower()
    
    def test_monitor_positions_no_stop_loss(self, trading_engine, test_config, mock_brokerage):
        """Test position monitoring without stop-loss trigger"""
        actions = trading_engine.monitor_positions(test_config)
        
        # Should not trigger any actions if price is stable
        assert isinstance(actions, list)
        assert trading_engine.last_check_time is not None
    
    def test_monitor_positions_stop_loss_trigger(self, trading_engine, test_config, mock_brokerage):
        """Test position monitoring with stop-loss trigger"""
        # Set price to trigger stop-loss (5% loss)
        mock_brokerage.get_stock_price.return_value = StockPrice(
            symbol="005930",
            price=Decimal("70000.00"),  # 5.4% loss from 74000
            volume=1000000,
            open_price=Decimal("70500.00"),
            high_price=Decimal("71000.00"),
            low_price=Decimal("69500.00"),
            timestamp=datetime.now()
        )
        
        actions = trading_engine.monitor_positions(test_config)
        
        # Should trigger stop-loss sell
        assert len(actions) > 0
        assert actions[0]["action"] == "STOP_LOSS_SELL"
    
    def test_get_holdings_info(self, trading_engine, mock_brokerage):
        """Test getting holdings information"""
        holdings_info = trading_engine._get_holdings_info("test_user")
        
        assert "cash_balance" in holdings_info
        assert "invested_amount" in holdings_info
        assert "holdings" in holdings_info
        assert isinstance(holdings_info["holdings"], list)
    
    def test_record_trade(self, trading_engine, db_session):
        """Test recording trade in database"""
        trade_result = TradeResult(
            order_id="ORD123",
            symbol="005930",
            trade_type="BUY",
            quantity=10,
            executed_price=Decimal("75000.00"),
            total_amount=Decimal("750000.00"),
            executed_at=datetime.now(),
            status="SUCCESS",
            message="Test trade"
        )
        
        trading_engine._record_trade(
            "test_user",
            trade_result,
            85,
            "Test reasoning"
        )
        
        # Verify trade was recorded
        trade = db_session.query(TradeHistory).filter_by(order_id="ORD123").first()
        assert trade is not None
        assert trade.symbol == "005930"
        assert trade.quantity == 10
        assert trade.signal_ratio == 85
    
    def test_get_status(self, trading_engine, test_config, db_session):
        """Test getting auto-trading status"""
        trading_engine.start(test_config)
        status = trading_engine.get_status(test_config)
        
        assert "is_enabled" in status
        assert "is_running" in status
        assert "total_trades_today" in status
        assert "daily_profit_loss" in status
        assert status["is_enabled"] is True
        assert status["is_running"] is True
    
    def test_check_market_conditions_normal(self, trading_engine, test_config):
        """Test market conditions check under normal conditions"""
        is_safe, message = trading_engine.check_market_conditions(test_config)
        
        assert is_safe is True
        assert "normal" in message.lower()
    
    @patch('services.risk_manager.RiskManager.detect_abnormal_market')
    def test_check_market_conditions_abnormal(self, mock_detect, trading_engine, test_config):
        """Test market conditions check under abnormal conditions"""
        mock_detect.return_value = (True, "Extreme volatility detected")
        
        is_safe, message = trading_engine.check_market_conditions(test_config)
        
        assert is_safe is False
        assert "volatility" in message.lower()


class TestIntegration:
    """Integration tests for complete trading flow"""
    
    def test_complete_buy_flow(self, trading_engine, test_config, mock_brokerage, db_session):
        """Test complete buy flow from signal to execution"""
        # Start trading
        trading_engine.start(test_config)
        
        # Process buy signal
        result = trading_engine.process_signal(
            test_config,
            "005930",
            85,
            "Strong positive sentiment from AI analysis"
        )
        
        # Verify execution
        assert result["success"] is True
        assert result["action"] == "BUY"
        
        # Verify database record
        trade = db_session.query(TradeHistory).filter_by(user_id="test_user").first()
        assert trade is not None
        assert trade.trade_type == "BUY"
        assert trade.signal_ratio == 85
        
        # Verify status update
        status = trading_engine.get_status(test_config)
        assert status["total_trades_today"] == 1
    
    def test_complete_sell_flow(self, trading_engine, test_config, mock_brokerage, db_session):
        """Test complete sell flow from signal to execution"""
        # Start trading
        trading_engine.start(test_config)
        
        # Process sell signal
        result = trading_engine.process_signal(
            test_config,
            "005930",
            15,
            "Strong negative sentiment from AI analysis"
        )
        
        # Verify execution
        assert result["success"] is True
        assert result["action"] == "SELL"
        
        # Verify database record
        trade = db_session.query(TradeHistory).filter_by(user_id="test_user").first()
        assert trade is not None
        assert trade.trade_type == "SELL"
        assert trade.signal_ratio == 15


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
