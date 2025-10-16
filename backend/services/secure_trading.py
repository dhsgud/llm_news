"""
Secure trading wrapper with 2FA and audit logging
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from decimal import Decimal
import logging

from services.security import audit_logger, two_factor_auth
from services.auto_trading_engine import AutoTradingEngine
from models.trade_history import TradeHistory

logger = logging.getLogger(__name__)


class SecureTradingWrapper:
    """
    Wrapper for trading operations with security features
    - 2FA verification for high-value trades
    - Audit logging for all operations
    - Additional validation
    """
    
    def __init__(
        self,
        engine: AutoTradingEngine,
        user_id: str,
        db: Session,
        require_2fa_threshold: Decimal = Decimal("5000000.00")  # 5M KRW
    ):
        self.engine = engine
        self.user_id = user_id
        self.db = db
        self.require_2fa_threshold = require_2fa_threshold
    
    def requires_2fa(self, amount: Decimal) -> bool:
        """Check if trade requires 2FA verification"""
        return (
            two_factor_auth.is_enabled(self.user_id) and
            amount >= self.require_2fa_threshold
        )
    
    async def execute_trade(
        self,
        symbol: str,
        action: str,
        quantity: int,
        price: Decimal,
        two_fa_token: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute trade with security checks
        
        Args:
            symbol: Stock symbol
            action: BUY or SELL
            quantity: Number of shares
            price: Price per share
            two_fa_token: 2FA token if required
            ip_address: Client IP for audit log
        
        Returns:
            Trade execution result
        
        Raises:
            ValueError: If 2FA required but not provided or invalid
        """
        total_amount = Decimal(quantity) * price
        
        # Check if 2FA is required
        if self.requires_2fa(total_amount):
            if not two_fa_token:
                audit_logger.log_trade(
                    user_id=self.user_id,
                    action=action,
                    symbol=symbol,
                    quantity=quantity,
                    price=float(price),
                    status="REJECTED",
                    reason="2FA_REQUIRED"
                )
                raise ValueError("2FA verification required for this trade amount")
            
            # Verify 2FA token
            if not two_factor_auth.verify_token(self.user_id, two_fa_token):
                audit_logger.log_trade(
                    user_id=self.user_id,
                    action=action,
                    symbol=symbol,
                    quantity=quantity,
                    price=float(price),
                    status="REJECTED",
                    reason="2FA_INVALID"
                )
                raise ValueError("Invalid 2FA token")
        
        # Execute trade
        try:
            if action.upper() == "BUY":
                result = self.engine.execute_buy(symbol, quantity, float(price))
            elif action.upper() == "SELL":
                result = self.engine.execute_sell(symbol, quantity, float(price))
            else:
                raise ValueError(f"Invalid action: {action}")
            
            # Log successful trade
            audit_logger.log_trade(
                user_id=self.user_id,
                action=action,
                symbol=symbol,
                quantity=quantity,
                price=float(price),
                status="SUCCESS",
                ip_address=ip_address,
                two_fa_verified=bool(two_fa_token)
            )
            
            # Store in trade audit log database
            self._store_trade_audit(
                action=action,
                symbol=symbol,
                quantity=quantity,
                price=price,
                total_amount=total_amount,
                status="SUCCESS",
                ip_address=ip_address,
                two_fa_verified=bool(two_fa_token)
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Trade execution failed: {e}")
            
            # Log failed trade
            audit_logger.log_trade(
                user_id=self.user_id,
                action=action,
                symbol=symbol,
                quantity=quantity,
                price=float(price),
                status="FAILED",
                error=str(e),
                ip_address=ip_address
            )
            
            # Store in trade audit log database
            self._store_trade_audit(
                action=action,
                symbol=symbol,
                quantity=quantity,
                price=price,
                total_amount=total_amount,
                status="FAILED",
                error_message=str(e),
                ip_address=ip_address,
                two_fa_verified=bool(two_fa_token)
            )
            
            raise
    
    def _store_trade_audit(
        self,
        action: str,
        symbol: str,
        quantity: int,
        price: Decimal,
        total_amount: Decimal,
        status: str,
        error_message: Optional[str] = None,
        ip_address: Optional[str] = None,
        two_fa_verified: bool = False
    ):
        """Store trade in audit log database"""
        from models.security_models import TradeAuditLog
        
        audit_entry = TradeAuditLog(
            user_id=self.user_id,
            action=action,
            symbol=symbol,
            quantity=quantity,
            price=float(price),
            total_amount=float(total_amount),
            status=status,
            error_message=error_message,
            ip_address=ip_address,
            requires_2fa=self.requires_2fa(total_amount),
            two_fa_verified=two_fa_verified
        )
        
        self.db.add(audit_entry)
        self.db.commit()
    
    async def start_auto_trading(
        self,
        two_fa_token: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Start auto-trading with 2FA verification
        
        Args:
            two_fa_token: 2FA token
            ip_address: Client IP for audit log
        
        Returns:
            Status result
        """
        # Always require 2FA for starting auto-trading if enabled
        if two_factor_auth.is_enabled(self.user_id):
            if not two_fa_token:
                audit_logger.log_security_event(
                    event_type="AUTO_TRADING_START",
                    severity="WARNING",
                    details=f"2FA required but not provided for user {self.user_id}",
                    ip_address=ip_address
                )
                raise ValueError("2FA verification required to start auto-trading")
            
            if not two_factor_auth.verify_token(self.user_id, two_fa_token):
                audit_logger.log_security_event(
                    event_type="AUTO_TRADING_START",
                    severity="WARNING",
                    details=f"Invalid 2FA token for user {self.user_id}",
                    ip_address=ip_address
                )
                raise ValueError("Invalid 2FA token")
        
        # Start auto-trading
        try:
            self.engine.start()
            
            audit_logger.log_security_event(
                event_type="AUTO_TRADING_START",
                severity="INFO",
                details=f"Auto-trading started for user {self.user_id}",
                ip_address=ip_address,
                two_fa_verified=bool(two_fa_token)
            )
            
            return {
                "status": "started",
                "message": "Auto-trading started successfully",
                "user_id": self.user_id
            }
            
        except Exception as e:
            logger.error(f"Failed to start auto-trading: {e}")
            
            audit_logger.log_security_event(
                event_type="AUTO_TRADING_START",
                severity="ERROR",
                details=f"Failed to start auto-trading for user {self.user_id}: {str(e)}",
                ip_address=ip_address
            )
            
            raise
    
    async def stop_auto_trading(
        self,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Stop auto-trading (no 2FA required for safety)
        
        Args:
            ip_address: Client IP for audit log
        
        Returns:
            Status result
        """
        try:
            self.engine.stop()
            
            audit_logger.log_security_event(
                event_type="AUTO_TRADING_STOP",
                severity="INFO",
                details=f"Auto-trading stopped for user {self.user_id}",
                ip_address=ip_address
            )
            
            return {
                "status": "stopped",
                "message": "Auto-trading stopped successfully",
                "user_id": self.user_id
            }
            
        except Exception as e:
            logger.error(f"Failed to stop auto-trading: {e}")
            
            audit_logger.log_security_event(
                event_type="AUTO_TRADING_STOP",
                severity="ERROR",
                details=f"Failed to stop auto-trading for user {self.user_id}: {str(e)}",
                ip_address=ip_address
            )
            
            raise
