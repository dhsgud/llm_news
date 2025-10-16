"""
Alert Service
Sends notifications for system errors, performance issues, and trading events
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json

try:
    from config import settings
except ImportError:
    from config import settings

logger = logging.getLogger(__name__)


class AlertLevel(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """Types of alerts"""
    SYSTEM_ERROR = "system_error"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    TRADE_EXECUTION = "trade_execution"
    TRADE_FAILURE = "trade_failure"
    STOP_LOSS_TRIGGERED = "stop_loss_triggered"
    DAILY_LOSS_LIMIT = "daily_loss_limit"
    API_ERROR = "api_error"
    LLM_ERROR = "llm_error"
    DATABASE_ERROR = "database_error"
    SECURITY_ALERT = "security_alert"


class AlertService:
    """
    Service for sending alerts and notifications
    """
    
    def __init__(self):
        """Initialize alert service"""
        self.alert_history: List[Dict] = []
        self.alert_counts: Dict[AlertType, int] = defaultdict(int)
        self.last_alert_time: Dict[AlertType, datetime] = {}
        self.alert_cooldown_minutes = 5  # Minimum time between same alert types
        
        # Email configuration
        self.smtp_server = getattr(settings, 'smtp_server', 'smtp.gmail.com')
        self.smtp_port = getattr(settings, 'smtp_port', 587)
        self.smtp_username = getattr(settings, 'smtp_username', None)
        self.smtp_password = getattr(settings, 'smtp_password', None)
        self.alert_email_to = getattr(settings, 'alert_email_to', None)
        self.alert_email_from = getattr(settings, 'alert_email_from', self.smtp_username)
        
        # SMS configuration (placeholder)
        self.sms_enabled = getattr(settings, 'sms_enabled', False)
        self.sms_api_key = getattr(settings, 'sms_api_key', None)
        self.sms_phone_number = getattr(settings, 'sms_phone_number', None)
    
    def send_alert(self, alert_type: AlertType, level: AlertLevel, message: str,
                  details: Optional[Dict[str, Any]] = None, force: bool = False) -> bool:
        """
        Send an alert
        
        Args:
            alert_type: Type of alert
            level: Alert severity level
            message: Alert message
            details: Additional details
            force: Force send even if in cooldown period
        
        Returns:
            True if alert was sent, False otherwise
        """
        # Check cooldown
        if not force and alert_type in self.last_alert_time:
            time_since_last = datetime.now() - self.last_alert_time[alert_type]
            if time_since_last < timedelta(minutes=self.alert_cooldown_minutes):
                logger.debug(f"Alert {alert_type} in cooldown period, skipping")
                return False
        
        # Create alert record
        alert = {
            "timestamp": datetime.now().isoformat(),
            "type": alert_type.value,
            "level": level.value,
            "message": message,
            "details": details or {},
        }
        
        # Store in history
        self.alert_history.append(alert)
        self.alert_counts[alert_type] += 1
        self.last_alert_time[alert_type] = datetime.now()
        
        # Log alert
        log_level = {
            AlertLevel.INFO: logging.INFO,
            AlertLevel.WARNING: logging.WARNING,
            AlertLevel.ERROR: logging.ERROR,
            AlertLevel.CRITICAL: logging.CRITICAL,
        }.get(level, logging.INFO)
        
        logger.log(log_level, f"ALERT [{alert_type.value}]: {message}", extra={"alert_details": details})
        
        # Send notifications based on level
        if level in [AlertLevel.ERROR, AlertLevel.CRITICAL]:
            self._send_email_notification(alert)
            
            if level == AlertLevel.CRITICAL and self.sms_enabled:
                self._send_sms_notification(alert)
        
        return True
    
    def _send_email_notification(self, alert: Dict) -> bool:
        """
        Send email notification
        
        Args:
            alert: Alert data
        
        Returns:
            True if email was sent successfully
        """
        if not self.smtp_username or not self.smtp_password or not self.alert_email_to:
            logger.warning("Email configuration incomplete, skipping email notification")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.alert_email_from
            msg['To'] = self.alert_email_to
            msg['Subject'] = f"[{alert['level'].upper()}] {alert['type']}"
            
            # Email body
            body = f"""
Alert Notification
==================

Time: {alert['timestamp']}
Type: {alert['type']}
Level: {alert['level']}

Message:
{alert['message']}

Details:
{json.dumps(alert['details'], indent=2)}

---
Market Sentiment Analyzer Alert System
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email notification sent for alert: {alert['type']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False
    
    def _send_sms_notification(self, alert: Dict) -> bool:
        """
        Send SMS notification (placeholder implementation)
        
        Args:
            alert: Alert data
        
        Returns:
            True if SMS was sent successfully
        """
        if not self.sms_enabled or not self.sms_api_key or not self.sms_phone_number:
            logger.warning("SMS configuration incomplete, skipping SMS notification")
            return False
        
        try:
            # Placeholder for SMS API integration
            # Example: Twilio, AWS SNS, etc.
            message = f"[{alert['level'].upper()}] {alert['type']}: {alert['message']}"
            
            logger.info(f"SMS notification would be sent: {message}")
            # TODO: Implement actual SMS sending
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS notification: {e}")
            return False
    
    def alert_system_error(self, error: Exception, context: Optional[Dict] = None):
        """Alert for system errors"""
        self.send_alert(
            AlertType.SYSTEM_ERROR,
            AlertLevel.ERROR,
            f"System error occurred: {str(error)}",
            details={"error_type": type(error).__name__, "context": context or {}}
        )
    
    def alert_performance_degradation(self, metric: str, value: float, threshold: float):
        """Alert for performance degradation"""
        self.send_alert(
            AlertType.PERFORMANCE_DEGRADATION,
            AlertLevel.WARNING,
            f"Performance degradation detected: {metric} = {value:.2f} (threshold: {threshold:.2f})",
            details={"metric": metric, "value": value, "threshold": threshold}
        )
    
    def alert_trade_execution(self, symbol: str, action: str, quantity: int, price: float):
        """Alert for successful trade execution"""
        self.send_alert(
            AlertType.TRADE_EXECUTION,
            AlertLevel.INFO,
            f"Trade executed: {action} {quantity} {symbol} @ {price}",
            details={"symbol": symbol, "action": action, "quantity": quantity, "price": price}
        )
    
    def alert_trade_failure(self, symbol: str, action: str, error: str):
        """Alert for trade failure"""
        self.send_alert(
            AlertType.TRADE_FAILURE,
            AlertLevel.ERROR,
            f"Trade failed: {action} {symbol} - {error}",
            details={"symbol": symbol, "action": action, "error": error}
        )
    
    def alert_stop_loss_triggered(self, symbol: str, quantity: int, loss_amount: float):
        """Alert for stop loss trigger"""
        self.send_alert(
            AlertType.STOP_LOSS_TRIGGERED,
            AlertLevel.WARNING,
            f"Stop loss triggered: {symbol} - Loss: {loss_amount:.2f}",
            details={"symbol": symbol, "quantity": quantity, "loss_amount": loss_amount},
            force=True  # Always send stop loss alerts
        )
    
    def alert_daily_loss_limit(self, total_loss: float, limit: float):
        """Alert for daily loss limit reached"""
        self.send_alert(
            AlertType.DAILY_LOSS_LIMIT,
            AlertLevel.CRITICAL,
            f"Daily loss limit reached: {total_loss:.2f} (limit: {limit:.2f})",
            details={"total_loss": total_loss, "limit": limit},
            force=True
        )
    
    def alert_api_error(self, api_name: str, error: str):
        """Alert for API errors"""
        self.send_alert(
            AlertType.API_ERROR,
            AlertLevel.ERROR,
            f"API error: {api_name} - {error}",
            details={"api_name": api_name, "error": error}
        )
    
    def alert_llm_error(self, prompt_type: str, error: str):
        """Alert for LLM errors"""
        self.send_alert(
            AlertType.LLM_ERROR,
            AlertLevel.ERROR,
            f"LLM error: {prompt_type} - {error}",
            details={"prompt_type": prompt_type, "error": error}
        )
    
    def alert_database_error(self, operation: str, error: str):
        """Alert for database errors"""
        self.send_alert(
            AlertType.DATABASE_ERROR,
            AlertLevel.CRITICAL,
            f"Database error: {operation} - {error}",
            details={"operation": operation, "error": error}
        )
    
    def alert_security_event(self, event_type: str, details: Dict):
        """Alert for security events"""
        self.send_alert(
            AlertType.SECURITY_ALERT,
            AlertLevel.CRITICAL,
            f"Security alert: {event_type}",
            details=details,
            force=True
        )
    
    def get_alert_history(self, limit: int = 100, alert_type: Optional[AlertType] = None) -> List[Dict]:
        """
        Get alert history
        
        Args:
            limit: Maximum number of alerts to return
            alert_type: Filter by alert type
        
        Returns:
            List of alerts
        """
        alerts = self.alert_history
        
        if alert_type:
            alerts = [a for a in alerts if a['type'] == alert_type.value]
        
        return alerts[-limit:]
    
    def get_alert_stats(self) -> Dict:
        """
        Get alert statistics
        
        Returns:
            Dictionary containing alert statistics
        """
        return {
            "total_alerts": len(self.alert_history),
            "alerts_by_type": {k.value: v for k, v in self.alert_counts.items()},
            "recent_alerts": self.get_alert_history(limit=10),
        }


# Global alert service instance
_alert_service: Optional[AlertService] = None


def get_alert_service() -> AlertService:
    """
    Get global alert service instance
    
    Returns:
        AlertService instance
    """
    global _alert_service
    if _alert_service is None:
        _alert_service = AlertService()
    return _alert_service
