"""
Auto Trading Engine Module
Implements automated trading based on AI signals with risk management
Requirements: 12.2, 12.3, 12.4, 12.5, 12.6, 12.7
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import logging
import asyncio
from enum import Enum

try:
    from models.auto_trade_config import AutoTradeConfig
    from models.trade_history import TradeHistory
    from models.account_holding import AccountHolding
    from services.risk_manager import RiskManager, RiskValidationError
    from services.signal_generator import SignalCalculator
    from services.brokerage_connector import BrokerageAPIBase, StockPrice
    from models.trading_schemas import Order, TradeResult
except ImportError:
    from models.auto_trade_config import AutoTradeConfig
    from models.trade_history import TradeHistory
    from models.account_holding import AccountHolding
    from services.risk_manager import RiskManager, RiskValidationError
    from services.signal_generator import SignalCalculator
    from services.brokerage_connector import BrokerageAPIBase, StockPrice
    from models.trading_schemas import Order, TradeResult


logger = logging.getLogger(__name__)


class TradeAction(Enum):
    """Trade action types"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class AutoTradingEngine:
    """
    Automated trading engine that executes trades based on AI signals
    Integrates risk management, position monitoring, and notifications
    """
    
    def __init__(
        self,
        db: Session,
        brokerage_api: BrokerageAPIBase,
        signal_calculator: Optional[SignalCalculator] = None,
        risk_manager: Optional[RiskManager] = None
    ):
        """
        Initialize auto trading engine
        
        Args:
            db: Database session
            brokerage_api: Brokerage API connector
            signal_calculator: Signal calculator instance
            risk_manager: Risk manager instance
        """
        self.db = db
        self.brokerage_api = brokerage_api
        self.signal_calculator = signal_calculator or SignalCalculator()
        self.risk_manager = risk_manager or RiskManager(db)
        self.is_running = False
        self.last_check_time: Optional[datetime] = None
        
        logger.info("AutoTradingEngine initialized")
    
    def start(self, config: AutoTradeConfig) -> Dict[str, Any]:
        """
        Start auto trading for a user
        
        Args:
            config: Auto-trade configuration
        
        Returns:
            Status dictionary
        """
        if not config.is_enabled:
            return {
                "success": False,
                "message": "Auto-trading is disabled in configuration"
            }
        
        self.is_running = True
        logger.info(f"Auto-trading started for user {config.user_id}")
        
        return {
            "success": True,
            "message": "Auto-trading started successfully",
            "config": {
                "user_id": config.user_id,
                "max_investment": float(config.max_investment_amount),
                "risk_level": config.risk_level
            }
        }
    
    def stop(self, config: AutoTradeConfig, reason: str = "User requested") -> Dict[str, Any]:
        """
        Stop auto trading
        
        Args:
            config: Auto-trade configuration
            reason: Reason for stopping
        
        Returns:
            Status dictionary
        """
        self.is_running = False
        config.is_enabled = False
        self.db.commit()
        
        logger.info(f"Auto-trading stopped for user {config.user_id}: {reason}")
        
        return {
            "success": True,
            "message": f"Auto-trading stopped: {reason}"
        }
    
    def process_signal(
        self,
        config: AutoTradeConfig,
        symbol: str,
        signal_ratio: int,
        reasoning: str = ""
    ) -> Dict[str, Any]:
        """
        Process a trading signal and execute if thresholds are met
        
        Args:
            config: Auto-trade configuration
            symbol: Stock symbol
            signal_ratio: Signal strength (0-100)
            reasoning: AI reasoning for the signal
        
        Returns:
            Result dictionary with execution details
        """
        try:
            # Check if auto-trading is enabled
            if not config.is_enabled:
                return {
                    "success": False,
                    "action": "NONE",
                    "message": "Auto-trading is disabled"
                }
            
            # Determine action based on thresholds
            action = self._determine_action(config, signal_ratio)
            
            if action == TradeAction.HOLD:
                return {
                    "success": True,
                    "action": "HOLD",
                    "message": f"Signal ratio {signal_ratio} within hold range ({config.sell_threshold}-{config.buy_threshold})"
                }
            
            # Get current holdings
            holdings_info = self._get_holdings_info(config.user_id)
            
            # Get current price
            try:
                stock_price = self.brokerage_api.get_stock_price(symbol)
                current_price = stock_price.price
            except Exception as e:
                logger.error(f"Failed to get stock price for {symbol}: {e}")
                return {
                    "success": False,
                    "action": action.value,
                    "message": f"Failed to get stock price: {str(e)}"
                }
            
            # Execute trade based on action
            if action == TradeAction.BUY:
                return self._execute_buy(
                    config, symbol, signal_ratio, current_price,
                    holdings_info, reasoning
                )
            elif action == TradeAction.SELL:
                return self._execute_sell(
                    config, symbol, signal_ratio, current_price,
                    holdings_info, reasoning
                )
        
        except Exception as e:
            logger.error(f"Error processing signal for {symbol}: {e}")
            return {
                "success": False,
                "action": "ERROR",
                "message": f"Error: {str(e)}"
            }
    
    def _determine_action(self, config: AutoTradeConfig, signal_ratio: int) -> TradeAction:
        """
        Determine trade action based on signal ratio and thresholds
        
        Args:
            config: Auto-trade configuration
            signal_ratio: Signal strength (0-100)
        
        Returns:
            TradeAction enum
        """
        if signal_ratio >= config.buy_threshold:
            return TradeAction.BUY
        elif signal_ratio <= config.sell_threshold:
            return TradeAction.SELL
        else:
            return TradeAction.HOLD
    
    def _execute_buy(
        self,
        config: AutoTradeConfig,
        symbol: str,
        signal_ratio: int,
        price: Decimal,
        holdings_info: Dict[str, Any],
        reasoning: str
    ) -> Dict[str, Any]:
        """
        Execute a buy order
        
        Args:
            config: Auto-trade configuration
            symbol: Stock symbol
            signal_ratio: Signal strength
            price: Current price
            holdings_info: Current holdings information
            reasoning: AI reasoning
        
        Returns:
            Execution result dictionary
        """
        try:
            # Calculate position size
            quantity = self.risk_manager.calculate_position_size(
                config, symbol, price, signal_ratio, holdings_info
            )
            
            if quantity <= 0:
                return {
                    "success": False,
                    "action": "BUY",
                    "message": "Calculated position size is 0"
                }
            
            # Validate trade
            is_valid, validation_msg = self.risk_manager.validate_trade(
                config, symbol, "BUY", quantity, price, holdings_info
            )
            
            if not is_valid:
                logger.warning(f"Buy order validation failed for {symbol}: {validation_msg}")
                return {
                    "success": False,
                    "action": "BUY",
                    "message": f"Validation failed: {validation_msg}"
                }
            
            # Create order
            order = Order(
                symbol=symbol,
                trade_type="BUY",
                quantity=quantity,
                price=price,
                order_type="MARKET"
            )
            
            # Execute order through brokerage API
            trade_result = self.brokerage_api.place_order(order)
            
            # Record trade in database
            self._record_trade(
                config.user_id,
                trade_result,
                signal_ratio,
                reasoning
            )
            
            # Send notification
            self._send_notification(
                config,
                f"BUY order executed: {quantity} shares of {symbol} at {price}",
                trade_result
            )
            
            logger.info(f"Buy order executed: {quantity} shares of {symbol} at {price}")
            
            return {
                "success": trade_result.status == "SUCCESS",
                "action": "BUY",
                "symbol": symbol,
                "quantity": quantity,
                "price": float(price),
                "order_id": trade_result.order_id,
                "message": trade_result.message or "Order executed"
            }
        
        except Exception as e:
            logger.error(f"Error executing buy order for {symbol}: {e}")
            return {
                "success": False,
                "action": "BUY",
                "message": f"Execution error: {str(e)}"
            }
    
    def _execute_sell(
        self,
        config: AutoTradeConfig,
        symbol: str,
        signal_ratio: int,
        price: Decimal,
        holdings_info: Dict[str, Any],
        reasoning: str
    ) -> Dict[str, Any]:
        """
        Execute a sell order
        
        Args:
            config: Auto-trade configuration
            symbol: Stock symbol
            signal_ratio: Signal strength
            price: Current price
            holdings_info: Current holdings information
            reasoning: AI reasoning
        
        Returns:
            Execution result dictionary
        """
        try:
            # Find holding for this symbol
            holdings = holdings_info.get("holdings", [])
            holding = next((h for h in holdings if h.get("symbol") == symbol), None)
            
            if not holding:
                return {
                    "success": False,
                    "action": "SELL",
                    "message": f"No holdings found for {symbol}"
                }
            
            quantity = holding.get("quantity", 0)
            
            if quantity <= 0:
                return {
                    "success": False,
                    "action": "SELL",
                    "message": f"No shares to sell for {symbol}"
                }
            
            # Validate trade
            is_valid, validation_msg = self.risk_manager.validate_trade(
                config, symbol, "SELL", quantity, price, holdings_info
            )
            
            if not is_valid:
                logger.warning(f"Sell order validation failed for {symbol}: {validation_msg}")
                return {
                    "success": False,
                    "action": "SELL",
                    "message": f"Validation failed: {validation_msg}"
                }
            
            # Create order
            order = Order(
                symbol=symbol,
                trade_type="SELL",
                quantity=quantity,
                price=price,
                order_type="MARKET"
            )
            
            # Execute order through brokerage API
            trade_result = self.brokerage_api.place_order(order)
            
            # Calculate profit/loss
            avg_price = holding.get("average_price", Decimal("0.0"))
            profit_loss = (price - avg_price) * Decimal(quantity)
            
            # Record trade in database
            self._record_trade(
                config.user_id,
                trade_result,
                signal_ratio,
                reasoning,
                profit_loss
            )
            
            # Send notification
            self._send_notification(
                config,
                f"SELL order executed: {quantity} shares of {symbol} at {price} (P/L: {profit_loss})",
                trade_result
            )
            
            logger.info(f"Sell order executed: {quantity} shares of {symbol} at {price} (P/L: {profit_loss})")
            
            return {
                "success": trade_result.status == "SUCCESS",
                "action": "SELL",
                "symbol": symbol,
                "quantity": quantity,
                "price": float(price),
                "profit_loss": float(profit_loss),
                "order_id": trade_result.order_id,
                "message": trade_result.message or "Order executed"
            }
        
        except Exception as e:
            logger.error(f"Error executing sell order for {symbol}: {e}")
            return {
                "success": False,
                "action": "SELL",
                "message": f"Execution error: {str(e)}"
            }
    
    def monitor_positions(self, config: AutoTradeConfig) -> List[Dict[str, Any]]:
        """
        Monitor all positions for stop-loss triggers
        
        Args:
            config: Auto-trade configuration
        
        Returns:
            List of actions taken
        """
        actions = []
        
        try:
            # Get current holdings
            holdings_info = self._get_holdings_info(config.user_id)
            holdings = holdings_info.get("holdings", [])
            
            for holding in holdings:
                symbol = holding.get("symbol")
                
                # Get current price
                try:
                    stock_price = self.brokerage_api.get_stock_price(symbol)
                    current_price = stock_price.price
                except Exception as e:
                    logger.error(f"Failed to get price for {symbol}: {e}")
                    continue
                
                # Check stop-loss
                should_sell, quantity, reason = self.risk_manager.check_stop_loss(
                    config, symbol, current_price, holdings_info
                )
                
                if should_sell and quantity:
                    logger.warning(f"Stop-loss triggered for {symbol}: {reason}")
                    
                    # Execute emergency sell
                    result = self._execute_sell(
                        config, symbol, 0, current_price,
                        holdings_info, f"STOP-LOSS: {reason}"
                    )
                    
                    actions.append({
                        "symbol": symbol,
                        "action": "STOP_LOSS_SELL",
                        "result": result,
                        "reason": reason
                    })
            
            self.last_check_time = datetime.now()
            
        except Exception as e:
            logger.error(f"Error monitoring positions: {e}")
        
        return actions
    
    def _get_holdings_info(self, user_id: str) -> Dict[str, Any]:
        """
        Get current holdings information from brokerage
        
        Args:
            user_id: User identifier
        
        Returns:
            Holdings information dictionary
        """
        try:
            account_info = self.brokerage_api.get_account_balance()
            holdings_list = self.brokerage_api.get_account_holdings()
            
            return {
                "cash_balance": account_info.available_cash,
                "invested_amount": account_info.total_assets - account_info.available_cash,
                "holdings": holdings_list
            }
        
        except Exception as e:
            logger.error(f"Error getting holdings info: {e}")
            return {
                "cash_balance": Decimal("0.0"),
                "invested_amount": Decimal("0.0"),
                "holdings": []
            }
    
    def _record_trade(
        self,
        user_id: str,
        trade_result: TradeResult,
        signal_ratio: int,
        reasoning: str,
        profit_loss: Decimal = Decimal("0.0")
    ) -> None:
        """
        Record trade in database
        
        Args:
            user_id: User identifier
            trade_result: Trade execution result
            signal_ratio: Signal strength
            reasoning: AI reasoning
            profit_loss: Realized profit/loss (for sells)
        """
        try:
            trade_record = TradeHistory(
                user_id=user_id,
                order_id=trade_result.order_id,
                symbol=trade_result.symbol,
                action=trade_result.trade_type,
                trade_type=trade_result.trade_type,
                quantity=trade_result.quantity,
                price=trade_result.executed_price,
                executed_price=trade_result.executed_price,
                total_amount=trade_result.total_amount,
                profit_loss=profit_loss,
                executed_at=trade_result.executed_at,
                status="COMPLETED" if trade_result.status == "SUCCESS" else "FAILED",
                signal_ratio=signal_ratio,
                reasoning=reasoning,
                message=trade_result.message
            )
            
            self.db.add(trade_record)
            self.db.commit()
            
            logger.info(f"Trade recorded: {trade_result.trade_type} {trade_result.quantity} {trade_result.symbol}")
            
            # Record trade metrics
            try:
                from services.monitoring import get_metrics_collector
                collector = get_metrics_collector()
                collector.record_trade(
                    amount=float(trade_result.total_amount),
                    profit=float(profit_loss) if profit_loss else None,
                    success=trade_result.status == "SUCCESS"
                )
            except Exception as metric_error:
                logger.debug(f"Failed to record trade metrics: {metric_error}")
        
        except Exception as e:
            logger.error(f"Error recording trade: {e}")
            self.db.rollback()
    
    def _send_notification(
        self,
        config: AutoTradeConfig,
        message: str,
        trade_result: TradeResult
    ) -> None:
        """
        Send trade notification to user
        
        Args:
            config: Auto-trade configuration
            message: Notification message
            trade_result: Trade execution result
        """
        if not config.notification_enabled:
            return
        
        try:
            # Send alert through alert service
            from services.alert_service import get_alert_service
            alert_service = get_alert_service()
            
            if trade_result.status == "SUCCESS":
                alert_service.alert_trade_execution(
                    symbol=trade_result.symbol,
                    action=trade_result.trade_type,
                    quantity=trade_result.quantity,
                    price=float(trade_result.executed_price)
                )
            else:
                alert_service.alert_trade_failure(
                    symbol=trade_result.symbol,
                    action=trade_result.trade_type,
                    error=trade_result.message or "Unknown error"
                )
            
            logger.info(f"NOTIFICATION to {config.notification_email}: {message}")
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    def get_status(self, config: AutoTradeConfig) -> Dict[str, Any]:
        """
        Get current auto-trading status
        
        Args:
            config: Auto-trade configuration
        
        Returns:
            Status dictionary
        """
        try:
            # Get today's trades
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            trades_today = self.db.query(TradeHistory).filter(
                and_(
                    TradeHistory.user_id == config.user_id,
                    TradeHistory.executed_at >= today_start
                )
            ).all()
            
            # Calculate daily P/L
            daily_pnl = sum(
                trade.profit_loss for trade in trades_today
                if trade.profit_loss is not None
            ) or Decimal("0.0")
            
            # Get last trade time
            last_trade = self.db.query(TradeHistory).filter(
                TradeHistory.user_id == config.user_id
            ).order_by(TradeHistory.executed_at.desc()).first()
            
            return {
                "is_enabled": config.is_enabled,
                "is_running": self.is_running,
                "last_check_time": self.last_check_time,
                "last_trade_time": last_trade.executed_at if last_trade else None,
                "total_trades_today": len(trades_today),
                "daily_profit_loss": float(daily_pnl),
                "message": "System running normally" if self.is_running else "System stopped"
            }
        
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return {
                "is_enabled": config.is_enabled,
                "is_running": self.is_running,
                "message": f"Error: {str(e)}"
            }
    
    def check_market_conditions(self, config: AutoTradeConfig) -> Tuple[bool, str]:
        """
        Check if market conditions are safe for trading
        
        Args:
            config: Auto-trade configuration
        
        Returns:
            Tuple of (is_safe, message)
        """
        try:
            # Check for abnormal market conditions
            is_abnormal, reason = self.risk_manager.detect_abnormal_market()
            
            if is_abnormal:
                logger.warning(f"Abnormal market detected: {reason}")
                # Optionally trigger emergency stop
                # self.risk_manager.emergency_stop(config, reason)
                return False, reason
            
            return True, "Market conditions normal"
        
        except Exception as e:
            logger.error(f"Error checking market conditions: {e}")
            return False, f"Error: {str(e)}"
