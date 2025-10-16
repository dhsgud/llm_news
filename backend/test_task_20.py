"""
Test Task 20: Auto Trading API Endpoints
Tests for auto-trading configuration and control endpoints
Requirements: 12.1, 12.5, 12.8
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta
from decimal import Decimal

from main import app
from app.database import Base, get_db
from models.auto_trade_config import AutoTradeConfig
from models.trade_history import TradeHistory

# Test database setup
import os

# Use in-memory database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Setup test database once for all tests"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function", autouse=True)
def clear_database():
    """Clear all tables before each test"""
    db = TestingSessionLocal()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
    finally:
        db.close()
    
    yield


class TestAutoTradingConfigEndpoints:
    """Test auto-trading configuration endpoints"""
    
    def test_update_trading_config(self):
        """Test POST /api/auto-trade/config - Update configuration"""
        config_data = {
            "max_investment_amount": 10000000.00,
            "max_position_size": 2000000.00,
            "risk_level": "MEDIUM",
            "buy_threshold": 80,
            "sell_threshold": 20,
            "stop_loss_percentage": 5.0,
            "daily_loss_limit": 500000.00,
            "trading_start_time": "09:00",
            "trading_end_time": "15:30",
            "allowed_symbols": ["005930", "000660"],
            "notification_email": "[email]"
        }
        
        response = client.post(
            "/api/auto-trade/config?user_id=test_user",
            json=config_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Configuration updated successfully"
        assert data["config"]["user_id"] == "test_user"
        assert data["config"]["max_investment_amount"] == 10000000.00
        assert data["config"]["risk_level"] == "MEDIUM"
        assert data["config"]["buy_threshold"] == 80
        assert data["config"]["sell_threshold"] == 20
    
    def test_get_trading_config(self):
        """Test GET /api/auto-trade/config - Get configuration"""
        # First create a config
        config_data = {
            "max_investment_amount": 5000000.00,
            "max_position_size": 1000000.00,
            "risk_level": "LOW",
            "buy_threshold": 85,
            "sell_threshold": 15,
            "stop_loss_percentage": 3.0,
            "trading_start_time": "09:00",
            "trading_end_time": "15:30"
        }
        
        client.post(
            "/api/auto-trade/config?user_id=test_user2",
            json=config_data
        )
        
        # Get the config
        response = client.get("/api/auto-trade/config?user_id=test_user2")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["config"]["user_id"] == "test_user2"
        assert data["config"]["max_investment_amount"] == 5000000.00
        assert data["config"]["risk_level"] == "LOW"
    
    def test_get_default_config(self):
        """Test GET /api/auto-trade/config - Get default config for new user"""
        response = client.get("/api/auto-trade/config?user_id=new_user")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["config"]["user_id"] == "new_user"
        assert data["config"]["is_enabled"] is False
        # Should have default values
        assert data["config"]["max_investment_amount"] == 10000000.00


class TestAutoTradingControlEndpoints:
    """Test auto-trading start/stop endpoints"""
    
    def test_start_auto_trading(self):
        """Test POST /api/auto-trade/start - Start auto-trading"""
        # First create a config
        config_data = {
            "max_investment_amount": 10000000.00,
            "max_position_size": 2000000.00,
            "risk_level": "MEDIUM",
            "buy_threshold": 80,
            "sell_threshold": 20,
            "stop_loss_percentage": 5.0,
            "trading_start_time": "09:00",
            "trading_end_time": "15:30"
        }
        
        client.post(
            "/api/auto-trade/config?user_id=test_user3",
            json=config_data
        )
        
        # Start auto-trading
        response = client.post("/api/auto-trade/start?user_id=test_user3")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Auto-trading started successfully"
        assert "status" in data
        assert data["status"]["is_enabled"] is True
    
    def test_stop_auto_trading(self):
        """Test POST /api/auto-trade/stop - Stop auto-trading"""
        # First start auto-trading
        config_data = {
            "max_investment_amount": 10000000.00,
            "max_position_size": 2000000.00,
            "risk_level": "MEDIUM",
            "buy_threshold": 80,
            "sell_threshold": 20,
            "stop_loss_percentage": 5.0,
            "trading_start_time": "09:00",
            "trading_end_time": "15:30"
        }
        
        client.post(
            "/api/auto-trade/config?user_id=test_user4",
            json=config_data
        )
        client.post("/api/auto-trade/start?user_id=test_user4")
        
        # Stop auto-trading
        response = client.post(
            "/api/auto-trade/stop?user_id=test_user4&reason=Testing"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "stopped" in data["message"].lower()
        assert data["reason"] == "Testing"
    
    def test_get_auto_trading_status(self):
        """Test GET /api/auto-trade/status - Get status"""
        # Create config and start
        config_data = {
            "max_investment_amount": 10000000.00,
            "max_position_size": 2000000.00,
            "risk_level": "MEDIUM",
            "buy_threshold": 80,
            "sell_threshold": 20,
            "stop_loss_percentage": 5.0,
            "trading_start_time": "09:00",
            "trading_end_time": "15:30"
        }
        
        client.post(
            "/api/auto-trade/config?user_id=test_user5",
            json=config_data
        )
        client.post("/api/auto-trade/start?user_id=test_user5")
        
        # Get status
        response = client.get("/api/auto-trade/status?user_id=test_user5")
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_enabled"] is True
        assert "total_trades_today" in data
        assert "daily_profit_loss" in data
        assert "message" in data


class TestTradeHistoryEndpoints:
    """Test trade history endpoints"""
    
    def test_get_trade_history_empty(self):
        """Test GET /api/trades/history - Empty history"""
        response = client.get("/api/trades/history?user_id=test_user6")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["summary"]["total_trades"] == 0
        assert len(data["trades"]) == 0
    
    def test_get_trade_history_with_data(self):
        """Test GET /api/trades/history - With trade data"""
        # Create some test trades
        db = TestingSessionLocal()
        
        trades = [
            TradeHistory(
                user_id="test_user7",
                order_id="ORDER001",
                symbol="005930",
                action="BUY",
                trade_type="BUY",
                quantity=10,
                price=Decimal("75000.00"),
                executed_price=Decimal("75000.00"),
                total_amount=Decimal("750000.00"),
                status="COMPLETED",
                signal_ratio=85,
                reasoning="Strong buy signal",
                executed_at=datetime.now()
            ),
            TradeHistory(
                user_id="test_user7",
                order_id="ORDER002",
                symbol="005930",
                action="SELL",
                trade_type="SELL",
                quantity=10,
                price=Decimal("76000.00"),
                executed_price=Decimal("76000.00"),
                total_amount=Decimal("760000.00"),
                profit_loss=Decimal("10000.00"),
                status="COMPLETED",
                signal_ratio=15,
                reasoning="Take profit",
                executed_at=datetime.now()
            )
        ]
        
        for trade in trades:
            db.add(trade)
        db.commit()
        db.close()
        
        # Get trade history
        response = client.get("/api/trades/history?user_id=test_user7")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["summary"]["total_trades"] == 2
        assert data["summary"]["buy_trades"] == 1
        assert data["summary"]["sell_trades"] == 1
        assert data["summary"]["total_profit_loss"] == 10000.00
        assert len(data["trades"]) == 2
    
    def test_get_trade_history_with_filters(self):
        """Test GET /api/trades/history - With filters"""
        # Create test trades
        db = TestingSessionLocal()
        
        trades = [
            TradeHistory(
                user_id="test_user8",
                order_id="ORDER003",
                symbol="005930",
                action="BUY",
                trade_type="BUY",
                quantity=10,
                price=Decimal("75000.00"),
                executed_price=Decimal("75000.00"),
                total_amount=Decimal("750000.00"),
                status="COMPLETED",
                signal_ratio=85,
                executed_at=datetime.now()
            ),
            TradeHistory(
                user_id="test_user8",
                order_id="ORDER004",
                symbol="000660",
                action="BUY",
                trade_type="BUY",
                quantity=5,
                price=Decimal("120000.00"),
                executed_price=Decimal("120000.00"),
                total_amount=Decimal("600000.00"),
                status="COMPLETED",
                signal_ratio=82,
                executed_at=datetime.now()
            )
        ]
        
        for trade in trades:
            db.add(trade)
        db.commit()
        db.close()
        
        # Filter by symbol
        response = client.get(
            "/api/trades/history?user_id=test_user8&symbol=005930"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["summary"]["total_trades"] == 1
        assert data["trades"][0]["symbol"] == "005930"
        
        # Filter by action
        response = client.get(
            "/api/trades/history?user_id=test_user8&action=BUY"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["summary"]["total_trades"] == 2
        assert all(t["action"] == "BUY" for t in data["trades"])
    
    def test_get_trade_history_with_limit(self):
        """Test GET /api/trades/history - With limit"""
        # Create multiple test trades
        db = TestingSessionLocal()
        
        for i in range(10):
            trade = TradeHistory(
                user_id="test_user9",
                order_id=f"ORDER{i:03d}",
                symbol="005930",
                action="BUY",
                trade_type="BUY",
                quantity=10,
                price=Decimal("75000.00"),
                executed_price=Decimal("75000.00"),
                total_amount=Decimal("750000.00"),
                status="COMPLETED",
                signal_ratio=85,
                executed_at=datetime.now() - timedelta(hours=i)
            )
            db.add(trade)
        
        db.commit()
        db.close()
        
        # Get with limit
        response = client.get(
            "/api/trades/history?user_id=test_user9&limit=5"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["trades"]) == 5


class TestManualTradeExecution:
    """Test manual trade execution endpoint"""
    
    def test_execute_manual_trade_buy(self):
        """Test POST /api/auto-trade/execute - Manual buy"""
        # Create config first
        config_data = {
            "max_investment_amount": 10000000.00,
            "max_position_size": 2000000.00,
            "risk_level": "MEDIUM",
            "buy_threshold": 80,
            "sell_threshold": 20,
            "stop_loss_percentage": 5.0,
            "trading_start_time": "09:00",
            "trading_end_time": "15:30"
        }
        
        client.post(
            "/api/auto-trade/config?user_id=test_user10",
            json=config_data
        )
        
        # Execute manual trade
        trade_request = {
            "symbol": "005930",
            "action": "BUY",
            "quantity": 10,
            "order_type": "MARKET"
        }
        
        response = client.post(
            "/api/auto-trade/execute?user_id=test_user10",
            json=trade_request
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "message" in data


class TestPositionMonitoring:
    """Test position monitoring endpoint"""
    
    def test_monitor_positions(self):
        """Test POST /api/auto-trade/monitor - Monitor positions"""
        # Create config
        config_data = {
            "max_investment_amount": 10000000.00,
            "max_position_size": 2000000.00,
            "risk_level": "MEDIUM",
            "buy_threshold": 80,
            "sell_threshold": 20,
            "stop_loss_percentage": 5.0,
            "trading_start_time": "09:00",
            "trading_end_time": "15:30"
        }
        
        client.post(
            "/api/auto-trade/config?user_id=test_user11",
            json=config_data
        )
        
        # Monitor positions
        response = client.post("/api/auto-trade/monitor?user_id=test_user11")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "actions" in data
        assert "checked_at" in data


def test_integration_flow():
    """Test complete auto-trading flow"""
    user_id = "integration_test_user"
    
    # 1. Create configuration
    config_data = {
        "max_investment_amount": 10000000.00,
        "max_position_size": 2000000.00,
        "risk_level": "MEDIUM",
        "buy_threshold": 80,
        "sell_threshold": 20,
        "stop_loss_percentage": 5.0,
        "daily_loss_limit": 500000.00,
        "trading_start_time": "09:00",
        "trading_end_time": "15:30",
        "notification_email": "[email]"
    }
    
    response = client.post(
        f"/api/auto-trade/config?user_id={user_id}",
        json=config_data
    )
    assert response.status_code == 200
    
    # 2. Get configuration
    response = client.get(f"/api/auto-trade/config?user_id={user_id}")
    assert response.status_code == 200
    assert response.json()["config"]["is_enabled"] is False
    
    # 3. Start auto-trading
    response = client.post(f"/api/auto-trade/start?user_id={user_id}")
    assert response.status_code == 200
    
    # 4. Check status
    response = client.get(f"/api/auto-trade/status?user_id={user_id}")
    assert response.status_code == 200
    assert response.json()["is_enabled"] is True
    
    # 5. Get trade history (should be empty)
    response = client.get(f"/api/trades/history?user_id={user_id}")
    assert response.status_code == 200
    assert response.json()["summary"]["total_trades"] == 0
    
    # 6. Stop auto-trading
    response = client.post(
        f"/api/auto-trade/stop?user_id={user_id}&reason=Test complete"
    )
    assert response.status_code == 200
    
    # 7. Verify stopped
    response = client.get(f"/api/auto-trade/config?user_id={user_id}")
    assert response.status_code == 200
    assert response.json()["config"]["is_enabled"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
