"""
Test Task 24: Monitoring and Logging
Tests for monitoring, metrics collection, structured logging, and alerting
"""

import pytest
import time
import json
from datetime import datetime
from pathlib import Path

from services.monitoring import MetricsCollector, get_metrics_collector
from services.structured_logger import StructuredLogger, get_structured_logger, JSONFormatter
from services.alert_service import AlertService, AlertType, AlertLevel, get_alert_service


class TestMetricsCollector:
    """Test metrics collection functionality"""
    
    def test_metrics_collector_initialization(self):
        """Test metrics collector can be initialized"""
        collector = MetricsCollector(window_size=100)
        assert collector is not None
        assert collector.window_size == 100
    
    def test_record_api_request(self):
        """Test recording API request metrics"""
        collector = MetricsCollector()
        
        # Record some requests
        collector.record_api_request("/api/analyze", 0.5, success=True)
        collector.record_api_request("/api/analyze", 0.7, success=True)
        collector.record_api_request("/api/analyze", 1.2, success=False)
        
        # Get metrics
        metrics = collector.get_api_metrics("/api/analyze")
        
        assert metrics["request_count"] == 3
        assert metrics["error_count"] == 1
        assert metrics["avg_response_time"] > 0
        assert metrics["max_response_time"] == 1.2
    
    def test_record_llm_inference(self):
        """Test recording LLM inference metrics"""
        collector = MetricsCollector()
        
        # Record some inferences
        collector.record_llm_inference(2.5, token_count=150, success=True)
        collector.record_llm_inference(3.0, token_count=200, success=True)
        collector.record_llm_inference(5.0, success=False)
        
        # Get metrics
        metrics = collector.get_llm_metrics()
        
        assert metrics["request_count"] == 3
        assert metrics["error_count"] == 1
        assert metrics["success_rate"] == pytest.approx(2/3, rel=0.01)
        assert metrics["avg_inference_time"] > 0
        assert metrics["avg_tokens"] == 175  # (150 + 200) / 2
    
    def test_record_trade(self):
        """Test recording trade metrics"""
        collector = MetricsCollector()
        
        # Record some trades
        collector.record_trade(1000000, profit=50000, success=True)
        collector.record_trade(500000, profit=-20000, success=True)
        collector.record_trade(750000, success=False)
        
        # Get metrics
        metrics = collector.get_trading_metrics()
        
        assert metrics["total_trades"] == 3
        assert metrics["success_count"] == 2
        assert metrics["failure_count"] == 1
        assert metrics["success_rate"] == pytest.approx(2/3, rel=0.01)
        assert metrics["total_profit"] == 30000  # 50000 - 20000
        assert metrics["win_rate"] == 0.5  # 1 win, 1 loss
    
    def test_get_all_metrics(self):
        """Test getting all metrics at once"""
        collector = MetricsCollector()
        
        # Record various metrics
        collector.record_api_request("/api/test", 0.5)
        collector.record_llm_inference(2.0, token_count=100)
        collector.record_trade(1000000, profit=10000)
        
        # Get all metrics
        all_metrics = collector.get_all_metrics()
        
        assert "timestamp" in all_metrics
        assert "system" in all_metrics
        assert "api" in all_metrics
        assert "llm" in all_metrics
        assert "trading" in all_metrics
        
        # Check system metrics
        assert "uptime_seconds" in all_metrics["system"]
        assert "start_time" in all_metrics["system"]
    
    def test_reset_metrics(self):
        """Test resetting metrics"""
        collector = MetricsCollector()
        
        # Record some data
        collector.record_api_request("/api/test", 0.5)
        collector.record_llm_inference(2.0)
        collector.record_trade(1000000)
        
        # Reset
        collector.reset_metrics()
        
        # Check all metrics are cleared
        api_metrics = collector.get_api_metrics()
        llm_metrics = collector.get_llm_metrics()
        trading_metrics = collector.get_trading_metrics()
        
        assert api_metrics["total_requests"] == 0
        assert llm_metrics["request_count"] == 0
        assert trading_metrics["total_trades"] == 0
    
    def test_percentile_calculation(self):
        """Test percentile calculation"""
        collector = MetricsCollector()
        
        # Record requests with known response times
        for i in range(100):
            collector.record_api_request("/api/test", i / 100.0)
        
        metrics = collector.get_api_metrics("/api/test")
        
        # Check percentiles
        assert metrics["p95_response_time"] >= 0.90
        assert metrics["p99_response_time"] >= 0.95


class TestStructuredLogger:
    """Test structured logging functionality"""
    
    def test_structured_logger_initialization(self):
        """Test structured logger can be initialized"""
        logger = StructuredLogger("test_logger", log_dir="logs/test")
        assert logger is not None
        assert logger.logger.name == "test_logger"
    
    def test_json_formatter(self):
        """Test JSON formatter"""
        import logging
        
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        data = json.loads(formatted)
        
        assert data["level"] == "INFO"
        assert data["message"] == "Test message"
        assert "timestamp" in data
        assert "logger" in data
    
    def test_log_with_context(self):
        """Test logging with context"""
        logger = StructuredLogger("test_context", log_dir="logs/test")
        
        # This should not raise an error
        logger.info("Test message", context={"user_id": "123", "action": "test"})
        logger.error("Error message", context={"error_code": "E001"})
    
    def test_log_api_request(self):
        """Test API request logging"""
        logger = StructuredLogger("test_api", log_dir="logs/test")
        
        # This should not raise an error
        logger.log_api_request(
            method="GET",
            path="/api/test",
            status_code=200,
            response_time=0.5,
            user_id="user123"
        )
    
    def test_log_llm_inference(self):
        """Test LLM inference logging"""
        logger = StructuredLogger("test_llm", log_dir="logs/test")
        
        # Successful inference
        logger.log_llm_inference(
            prompt_type="sentiment_analysis",
            inference_time=2.5,
            token_count=150,
            success=True
        )
        
        # Failed inference
        logger.log_llm_inference(
            prompt_type="trend_summary",
            inference_time=1.0,
            success=False,
            error="Connection timeout"
        )
    
    def test_log_trade(self):
        """Test trade logging"""
        logger = StructuredLogger("test_trade", log_dir="logs/test")
        
        # Successful trade
        logger.log_trade(
            action="BUY",
            symbol="005930",
            quantity=10,
            price=70000,
            success=True
        )
        
        # Failed trade
        logger.log_trade(
            action="SELL",
            symbol="005930",
            quantity=5,
            price=71000,
            success=False,
            error="Insufficient balance"
        )
    
    def test_log_system_event(self):
        """Test system event logging"""
        logger = StructuredLogger("test_system", log_dir="logs/test")
        
        logger.log_system_event(
            event_type="startup",
            message="Application started",
            severity="info"
        )
        
        logger.log_system_event(
            event_type="error",
            message="Database connection failed",
            severity="error",
            error_code="DB001"
        )


class TestAlertService:
    """Test alert service functionality"""
    
    def test_alert_service_initialization(self):
        """Test alert service can be initialized"""
        service = AlertService()
        assert service is not None
        assert len(service.alert_history) == 0
    
    def test_send_alert(self):
        """Test sending alerts"""
        service = AlertService()
        
        # Send an alert
        result = service.send_alert(
            AlertType.SYSTEM_ERROR,
            AlertLevel.ERROR,
            "Test error message",
            details={"error_code": "E001"}
        )
        
        assert result is True
        assert len(service.alert_history) == 1
        assert service.alert_counts[AlertType.SYSTEM_ERROR] == 1
    
    def test_alert_cooldown(self):
        """Test alert cooldown mechanism"""
        service = AlertService()
        service.alert_cooldown_minutes = 0.01  # 0.6 seconds for testing
        
        # Send first alert
        result1 = service.send_alert(
            AlertType.PERFORMANCE_DEGRADATION,
            AlertLevel.WARNING,
            "Performance issue"
        )
        assert result1 is True
        
        # Try to send same alert immediately (should be blocked)
        result2 = service.send_alert(
            AlertType.PERFORMANCE_DEGRADATION,
            AlertLevel.WARNING,
            "Performance issue again"
        )
        assert result2 is False
        
        # Wait for cooldown
        time.sleep(1)
        
        # Should work now
        result3 = service.send_alert(
            AlertType.PERFORMANCE_DEGRADATION,
            AlertLevel.WARNING,
            "Performance issue after cooldown"
        )
        assert result3 is True
    
    def test_alert_force_send(self):
        """Test forcing alert send bypasses cooldown"""
        service = AlertService()
        service.alert_cooldown_minutes = 10  # Long cooldown
        
        # Send first alert
        service.send_alert(
            AlertType.STOP_LOSS_TRIGGERED,
            AlertLevel.WARNING,
            "Stop loss 1"
        )
        
        # Force send immediately
        result = service.send_alert(
            AlertType.STOP_LOSS_TRIGGERED,
            AlertLevel.WARNING,
            "Stop loss 2",
            force=True
        )
        
        assert result is True
        assert len(service.alert_history) == 2
    
    def test_alert_system_error(self):
        """Test system error alert"""
        service = AlertService()
        
        try:
            raise ValueError("Test error")
        except Exception as e:
            service.alert_system_error(e, context={"module": "test"})
        
        assert len(service.alert_history) == 1
        alert = service.alert_history[0]
        assert alert["type"] == AlertType.SYSTEM_ERROR.value
        assert alert["level"] == AlertLevel.ERROR.value
    
    def test_alert_performance_degradation(self):
        """Test performance degradation alert"""
        service = AlertService()
        
        service.alert_performance_degradation(
            metric="api_response_time",
            value=5.5,
            threshold=5.0
        )
        
        assert len(service.alert_history) == 1
        alert = service.alert_history[0]
        assert alert["type"] == AlertType.PERFORMANCE_DEGRADATION.value
        assert alert["details"]["metric"] == "api_response_time"
    
    def test_alert_trade_execution(self):
        """Test trade execution alert"""
        service = AlertService()
        
        service.alert_trade_execution(
            symbol="005930",
            action="BUY",
            quantity=10,
            price=70000
        )
        
        assert len(service.alert_history) == 1
        alert = service.alert_history[0]
        assert alert["type"] == AlertType.TRADE_EXECUTION.value
        assert alert["level"] == AlertLevel.INFO.value
    
    def test_alert_trade_failure(self):
        """Test trade failure alert"""
        service = AlertService()
        
        service.alert_trade_failure(
            symbol="005930",
            action="SELL",
            error="Insufficient balance"
        )
        
        assert len(service.alert_history) == 1
        alert = service.alert_history[0]
        assert alert["type"] == AlertType.TRADE_FAILURE.value
        assert alert["level"] == AlertLevel.ERROR.value
    
    def test_alert_stop_loss_triggered(self):
        """Test stop loss alert"""
        service = AlertService()
        
        service.alert_stop_loss_triggered(
            symbol="005930",
            quantity=10,
            loss_amount=50000
        )
        
        assert len(service.alert_history) == 1
        alert = service.alert_history[0]
        assert alert["type"] == AlertType.STOP_LOSS_TRIGGERED.value
        assert alert["details"]["loss_amount"] == 50000
    
    def test_alert_daily_loss_limit(self):
        """Test daily loss limit alert"""
        service = AlertService()
        
        service.alert_daily_loss_limit(
            total_loss=150000,
            limit=100000
        )
        
        assert len(service.alert_history) == 1
        alert = service.alert_history[0]
        assert alert["type"] == AlertType.DAILY_LOSS_LIMIT.value
        assert alert["level"] == AlertLevel.CRITICAL.value
    
    def test_get_alert_history(self):
        """Test getting alert history"""
        service = AlertService()
        service.alert_cooldown_minutes = 0  # Disable cooldown for testing
        
        # Send multiple alerts
        for i in range(5):
            service.send_alert(
                AlertType.SYSTEM_ERROR,
                AlertLevel.ERROR,
                f"Error {i}"
            )
        
        # Get all alerts
        history = service.get_alert_history(limit=10)
        assert len(history) == 5
        
        # Get limited alerts
        history = service.get_alert_history(limit=3)
        assert len(history) == 3
    
    def test_get_alert_history_filtered(self):
        """Test getting filtered alert history"""
        service = AlertService()
        service.alert_cooldown_minutes = 0  # Disable cooldown for testing
        
        # Send different types of alerts
        service.send_alert(AlertType.SYSTEM_ERROR, AlertLevel.ERROR, "Error 1")
        service.send_alert(AlertType.TRADE_EXECUTION, AlertLevel.INFO, "Trade 1")
        service.send_alert(AlertType.SYSTEM_ERROR, AlertLevel.ERROR, "Error 2")
        
        # Get only system errors
        history = service.get_alert_history(alert_type=AlertType.SYSTEM_ERROR)
        assert len(history) == 2
        assert all(a["type"] == AlertType.SYSTEM_ERROR.value for a in history)
    
    def test_get_alert_stats(self):
        """Test getting alert statistics"""
        service = AlertService()
        service.alert_cooldown_minutes = 0  # Disable cooldown for testing
        
        # Send various alerts
        service.send_alert(AlertType.SYSTEM_ERROR, AlertLevel.ERROR, "Error 1")
        service.send_alert(AlertType.SYSTEM_ERROR, AlertLevel.ERROR, "Error 2")
        service.send_alert(AlertType.TRADE_EXECUTION, AlertLevel.INFO, "Trade 1")
        
        stats = service.get_alert_stats()
        
        assert stats["total_alerts"] == 3
        assert stats["alerts_by_type"][AlertType.SYSTEM_ERROR.value] == 2
        assert stats["alerts_by_type"][AlertType.TRADE_EXECUTION.value] == 1
        assert len(stats["recent_alerts"]) == 3


class TestGlobalInstances:
    """Test global instance getters"""
    
    def test_get_metrics_collector(self):
        """Test getting global metrics collector"""
        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()
        
        # Should return same instance
        assert collector1 is collector2
    
    def test_get_structured_logger(self):
        """Test getting global structured logger"""
        logger1 = get_structured_logger("test")
        logger2 = get_structured_logger("test")
        
        # Should return same instance for same name
        assert logger1 is logger2
        
        # Different name should return different instance
        logger3 = get_structured_logger("other")
        assert logger1 is not logger3
    
    def test_get_alert_service(self):
        """Test getting global alert service"""
        service1 = get_alert_service()
        service2 = get_alert_service()
        
        # Should return same instance
        assert service1 is service2


def test_integration_monitoring_flow():
    """Test complete monitoring flow"""
    # Get services
    collector = get_metrics_collector()
    logger = get_structured_logger("integration_test")
    alert_service = get_alert_service()
    
    # Simulate API request
    start_time = time.time()
    time.sleep(0.1)  # Simulate processing
    response_time = time.time() - start_time
    
    collector.record_api_request("/api/test", response_time, success=True)
    logger.log_api_request("GET", "/api/test", 200, response_time)
    
    # Simulate LLM inference
    collector.record_llm_inference(2.5, token_count=150, success=True)
    logger.log_llm_inference("test_prompt", 2.5, token_count=150, success=True)
    
    # Simulate trade
    collector.record_trade(1000000, profit=50000, success=True)
    logger.log_trade("BUY", "005930", 10, 70000, success=True)
    alert_service.alert_trade_execution("005930", "BUY", 10, 70000)
    
    # Check metrics were recorded
    all_metrics = collector.get_all_metrics()
    assert all_metrics["api"]["total_requests"] > 0
    assert all_metrics["llm"]["request_count"] > 0
    assert all_metrics["trading"]["total_trades"] > 0
    
    # Check alert was sent
    assert len(alert_service.alert_history) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
