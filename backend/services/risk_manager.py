"""
Risk Management Module for Auto Trading System
Validates trades, calculates position sizes, and enforces safety limits
"""

from datetime import datetime, time
from decimal import Decimal
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import logging

try:
    from models.auto_trade_config import AutoTradeConfig
    from models.trade_history import TradeHistory
    from models.account_holding import AccountHolding
except ImportError:
    from models.auto_trade_config import AutoTradeConfig
    from models.trade_history import TradeHistory
    from models.account_holding import AccountHolding


logger = logging.getLogger(__name__)


class RiskValidationError(Exception):
    """Exception raised when a trade fails risk validation"""
    pass


class RiskManager:
    """
    Manages risk for automated trading system
    Validates trades, calculates position sizes, and enforces safety limits
    """
    
    def __init__(self, db: Session):
        """
        Initialize RiskManager
        
        Args:
            db: Database session
        """
        self.db = db
    
    def validate_trade(
        self,
        config: AutoTradeConfig,
        symbol: str,
        action: str,
        quantity: int,
        price: Decimal,
        current_holdings: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """
        Validate if a trade should be executed based on risk parameters
        
        Args:
            config: Auto-trade configuration
            symbol: Stock symbol
            action: "BUY" or "SELL"
            quantity: Number of shares
            price: Price per share
            current_holdings: Current holdings information (optional)
        
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            # Check if auto-trading is enabled
            if not config.is_enabled:
                return False, "Auto-trading is disabled"
            
            # Check trading hours
            if not self._is_within_trading_hours(config):
                return False, "Outside of configured trading hours"
            
            # Check if symbol is allowed
            if not self._is_symbol_allowed(config, symbol):
                return False, f"Symbol {symbol} is not in allowed list or is excluded"
            
            # Check daily loss limit
            if not self._check_daily_loss_limit(config):
                return False, "Daily loss limit exceeded"
            
            # Validate based on action
            if action == "BUY":
                return self._validate_buy(config, symbol, quantity, price, current_holdings)
            elif action == "SELL":
                return self._validate_sell(config, symbol, quantity, current_holdings)
            else:
                return False, f"Invalid action: {action}"
        
        except Exception as e:
            logger.error(f"Error validating trade: {e}")
            return False, f"Validation error: {str(e)}"
    
    def _is_within_trading_hours(self, config: AutoTradeConfig) -> bool:
        """
        Check if current time is within configured trading hours
        
        Args:
            config: Auto-trade configuration
        
        Returns:
            True if within trading hours
        """
        now = datetime.now().time()
        
        try:
            start_time = time.fromisoformat(config.trading_start_time)
            end_time = time.fromisoformat(config.trading_end_time)
            
            return start_time <= now <= end_time
        except Exception as e:
            logger.error(f"Error parsing trading hours: {e}")
            return False
    
    def _is_symbol_allowed(self, config: AutoTradeConfig, symbol: str) -> bool:
        """
        Check if symbol is allowed for trading
        
        Args:
            config: Auto-trade configuration
            symbol: Stock symbol
        
        Returns:
            True if symbol is allowed
        """
        # Check excluded symbols first
        if config.excluded_symbols:
            excluded = [s.strip() for s in config.excluded_symbols.split(",")]
            if symbol in excluded:
                return False
        
        # If allowed symbols list exists, check if symbol is in it
        if config.allowed_symbols:
            allowed = [s.strip() for s in config.allowed_symbols.split(",")]
            return symbol in allowed
        
        # If no allowed list, all symbols (except excluded) are allowed
        return True
    
    def _check_daily_loss_limit(self, config: AutoTradeConfig) -> bool:
        """
        Check if daily loss limit has been exceeded
        
        Args:
            config: Auto-trade configuration
        
        Returns:
            True if within daily loss limit
        """
        if not config.daily_loss_limit:
            return True  # No limit set
        
        try:
            # Get today's trades
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            daily_pnl = self.db.query(func.sum(TradeHistory.profit_loss)).filter(
                and_(
                    TradeHistory.user_id == config.user_id,
                    TradeHistory.executed_at >= today_start,
                    TradeHistory.status == "COMPLETED"
                )
            ).scalar() or Decimal("0.0")
            
            # If loss exceeds limit, block trading
            if daily_pnl < -abs(config.daily_loss_limit):
                logger.warning(f"Daily loss limit exceeded: {daily_pnl} < -{config.daily_loss_limit}")
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Error checking daily loss limit: {e}")
            return False
    
    def _validate_buy(
        self,
        config: AutoTradeConfig,
        symbol: str,
        quantity: int,
        price: Decimal,
        current_holdings: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """
        Validate a buy order
        
        Args:
            config: Auto-trade configuration
            symbol: Stock symbol
            quantity: Number of shares
            price: Price per share
            current_holdings: Current holdings information
        
        Returns:
            Tuple of (is_valid, message)
        """
        trade_value = Decimal(quantity) * price
        
        # Check position size limit
        if trade_value > config.max_position_size:
            return False, f"Trade value {trade_value} exceeds max position size {config.max_position_size}"
        
        # Check total investment limit
        if current_holdings:
            total_invested = current_holdings.get("invested_amount", Decimal("0.0"))
            if total_invested + trade_value > config.max_investment_amount:
                return False, f"Total investment would exceed limit: {total_invested + trade_value} > {config.max_investment_amount}"
            
            # Check cash balance
            cash_balance = current_holdings.get("cash_balance", Decimal("0.0"))
            if cash_balance < trade_value:
                return False, f"Insufficient cash balance: {cash_balance} < {trade_value}"
        
        return True, "Buy order validated"
    
    def _validate_sell(
        self,
        config: AutoTradeConfig,
        symbol: str,
        quantity: int,
        current_holdings: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """
        Validate a sell order
        
        Args:
            config: Auto-trade configuration
            symbol: Stock symbol
            quantity: Number of shares
            current_holdings: Current holdings information
        
        Returns:
            Tuple of (is_valid, message)
        """
        # Check if we have enough shares to sell
        if current_holdings:
            holdings = current_holdings.get("holdings", [])
            holding = next((h for h in holdings if h.get("symbol") == symbol), None)
            
            if not holding:
                return False, f"No holdings found for symbol {symbol}"
            
            held_quantity = holding.get("quantity", 0)
            if held_quantity < quantity:
                return False, f"Insufficient shares: have {held_quantity}, trying to sell {quantity}"
        
        return True, "Sell order validated"
    
    def calculate_position_size(
        self,
        config: AutoTradeConfig,
        symbol: str,
        price: Decimal,
        signal_ratio: int,
        current_holdings: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Calculate optimal position size based on risk parameters
        
        Args:
            config: Auto-trade configuration
            symbol: Stock symbol
            price: Current price per share
            signal_ratio: Signal strength (0-100)
            current_holdings: Current holdings information
        
        Returns:
            Number of shares to buy
        """
        try:
            # Base position size from max_position_size
            base_amount = config.max_position_size
            
            # Adjust based on risk level
            risk_multipliers = {
                "LOW": Decimal("0.5"),
                "MEDIUM": Decimal("0.75"),
                "HIGH": Decimal("1.0")
            }
            risk_multiplier = risk_multipliers.get(config.risk_level, Decimal("0.75"))
            
            # Adjust based on signal strength (normalize to 0-1)
            signal_strength = Decimal(signal_ratio) / Decimal("100")
            
            # Calculate position amount
            position_amount = base_amount * risk_multiplier * signal_strength
            
            # Check available cash
            if current_holdings:
                cash_balance = current_holdings.get("cash_balance", Decimal("0.0"))
                invested_amount = current_holdings.get("invested_amount", Decimal("0.0"))
                
                # Don't exceed max investment
                available_for_investment = config.max_investment_amount - invested_amount
                position_amount = min(position_amount, available_for_investment, cash_balance)
            
            # Calculate quantity
            if price <= 0:
                return 0
            
            quantity = int(position_amount / price)
            
            # Ensure at least 1 share if we have enough money
            if quantity == 0 and position_amount >= price:
                quantity = 1
            
            logger.info(f"Calculated position size for {symbol}: {quantity} shares at {price}")
            return quantity
        
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0
    
    def check_stop_loss(
        self,
        config: AutoTradeConfig,
        symbol: str,
        current_price: Decimal,
        current_holdings: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[int], str]:
        """
        Check if stop-loss should be triggered for a position
        
        Args:
            config: Auto-trade configuration
            symbol: Stock symbol
            current_price: Current market price
            current_holdings: Current holdings information
        
        Returns:
            Tuple of (should_sell, quantity_to_sell, reason)
        """
        try:
            if not current_holdings:
                return False, None, "No holdings information"
            
            holdings = current_holdings.get("holdings", [])
            holding = next((h for h in holdings if h.get("symbol") == symbol), None)
            
            if not holding:
                return False, None, f"No position found for {symbol}"
            
            average_price = holding.get("average_price", Decimal("0.0"))
            quantity = holding.get("quantity", 0)
            
            if average_price <= 0:
                return False, None, "Invalid average price"
            
            # Calculate loss percentage
            loss_percentage = ((current_price - average_price) / average_price) * Decimal("100")
            
            # Check if stop-loss threshold is breached
            stop_loss_threshold = -abs(config.stop_loss_percentage)
            
            if loss_percentage <= stop_loss_threshold:
                reason = f"Stop-loss triggered: {loss_percentage:.2f}% loss (threshold: {stop_loss_threshold}%)"
                logger.warning(f"{reason} for {symbol}")
                return True, quantity, reason
            
            return False, None, "Within stop-loss threshold"
        
        except Exception as e:
            logger.error(f"Error checking stop-loss: {e}")
            return False, None, f"Error: {str(e)}"
    
    def detect_abnormal_market(self, vix_value: Optional[Decimal] = None) -> Tuple[bool, str]:
        """
        Detect abnormal market conditions (circuit breakers, extreme volatility)
        
        Args:
            vix_value: Current VIX value (optional)
        
        Returns:
            Tuple of (is_abnormal, reason)
        """
        try:
            # Check VIX for extreme volatility
            if vix_value is not None:
                # VIX > 40 indicates extreme fear/volatility
                if vix_value > Decimal("40"):
                    return True, f"Extreme market volatility detected (VIX: {vix_value})"
                
                # VIX > 30 indicates high volatility
                if vix_value > Decimal("30"):
                    logger.warning(f"High market volatility (VIX: {vix_value})")
            
            # Additional checks could be added here:
            # - Check for circuit breakers
            # - Check for market halts
            # - Check for unusual trading volumes
            
            return False, "Market conditions normal"
        
        except Exception as e:
            logger.error(f"Error detecting abnormal market: {e}")
            return True, f"Error checking market conditions: {str(e)}"
    
    def emergency_stop(self, config: AutoTradeConfig, reason: str) -> bool:
        """
        Emergency stop - disable auto-trading immediately
        
        Args:
            config: Auto-trade configuration
            reason: Reason for emergency stop
        
        Returns:
            True if successfully stopped
        """
        try:
            config.is_enabled = False
            self.db.commit()
            
            logger.critical(f"EMERGENCY STOP activated for user {config.user_id}: {reason}")
            
            # TODO: Send emergency notification
            
            return True
        
        except Exception as e:
            logger.error(f"Error during emergency stop: {e}")
            self.db.rollback()
            return False
