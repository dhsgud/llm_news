"""
Auto Trading API Endpoints
Provides REST API for automated trading configuration and control
Requirements: 12.1, 12.5, 12.8, 23.1, 23.2, 23.3
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import logging

from app.database import get_db
from models.auto_trading_schemas import (
    TradingConfig,
    AutoTradeStatus,
    TradeExecutionRequest,
    TradeExecutionResponse,
    Portfolio
)
from models.auto_trade_config import AutoTradeConfig
from models.trade_history import TradeHistory
from services.auto_trading_engine import AutoTradingEngine
from services.brokerage_connector import get_brokerage_api
from api.security import verify_api_key, check_rate_limit
from services.security import audit_logger, two_factor_auth

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(check_rate_limit)])

# Global auto-trading engine instance (in production, use proper state management)
_trading_engines = {}


def get_trading_engine(user_id: str, db: Session) -> AutoTradingEngine:
    """
    Get or create auto-trading engine for user
    
    Args:
        user_id: User identifier
        db: Database session
    
    Returns:
        AutoTradingEngine instance
    """
    if user_id not in _trading_engines:
        brokerage_api = get_brokerage_api()
        _trading_engines[user_id] = AutoTradingEngine(db, brokerage_api)
    
    return _trading_engines[user_id]


def get_or_create_config(user_id: str, db: Session) -> AutoTradeConfig:
    """
    Get existing config or create default one
    
    Args:
        user_id: User identifier
        db: Database session
    
    Returns:
        AutoTradeConfig instance
    """
    config = db.query(AutoTradeConfig).filter(
        AutoTradeConfig.user_id == user_id
    ).first()
    
    if not config:
        # Create default config
        config = AutoTradeConfig(
            user_id=user_id,
            max_investment_amount=Decimal("10000000.00"),
            max_position_size=Decimal("2000000.00"),
            risk_level="MEDIUM",
            buy_threshold=80,
            sell_threshold=20,
            stop_loss_percentage=Decimal("5.0"),
            is_enabled=False
        )
        db.add(config)
        db.commit()
        db.refresh(config)
    
    return config


@router.post("/auto-trade/config", response_model=dict, status_code=status.HTTP_200_OK)
async def update_trading_config(
    config_data: TradingConfig,
    request: Request,
    user_id: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Update auto-trading configuration (requires API key authentication)
    
    Args:
        config_data: Trading configuration data
        request: HTTP request for audit logging
        user_id: User identifier from API key
        db: Database session
    
    Returns:
        Updated configuration
    
    Requirements: 12.1
    """
    try:
        # Get or create config
        config = get_or_create_config(user_id, db)
        
        # Update configuration
        config.max_investment_amount = config_data.max_investment_amount
        config.max_position_size = config_data.max_position_size
        config.risk_level = config_data.risk_level
        config.buy_threshold = config_data.buy_threshold
        config.sell_threshold = config_data.sell_threshold
        config.stop_loss_percentage = config_data.stop_loss_percentage
        config.daily_loss_limit = config_data.daily_loss_limit
        config.trading_start_time = config_data.trading_start_time
        config.trading_end_time = config_data.trading_end_time
        config.notification_email = config_data.notification_email
        config.notification_enabled = bool(config_data.notification_email)
        config.updated_at = datetime.now()
        
        # Update allowed/excluded symbols if provided
        if config_data.allowed_symbols is not None:
            config.allowed_symbols = ",".join(config_data.allowed_symbols)
        
        if config_data.excluded_symbols is not None:
            config.excluded_symbols = ",".join(config_data.excluded_symbols)
        
        db.commit()
        db.refresh(config)
        
        logger.info(f"Trading config updated for user {user_id}")
        
        return {
            "success": True,
            "message": "Configuration updated successfully",
            "config": {
                "user_id": config.user_id,
                "max_investment_amount": float(config.max_investment_amount),
                "max_position_size": float(config.max_position_size),
                "risk_level": config.risk_level,
                "buy_threshold": config.buy_threshold,
                "sell_threshold": config.sell_threshold,
                "stop_loss_percentage": float(config.stop_loss_percentage),
                "daily_loss_limit": float(config.daily_loss_limit) if config.daily_loss_limit else None,
                "trading_start_time": config.trading_start_time,
                "trading_end_time": config.trading_end_time,
                "notification_email": config.notification_email,
                "is_enabled": config.is_enabled
            }
        }
    
    except Exception as e:
        logger.error(f"Error updating trading config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update configuration: {str(e)}"
        )


@router.get("/auto-trade/config", response_model=dict, status_code=status.HTTP_200_OK)
async def get_trading_config(
    user_id: str = Query(default="default_user", description="User identifier"),
    db: Session = Depends(get_db)
):
    """
    Get current auto-trading configuration
    
    Args:
        user_id: User identifier
        db: Database session
    
    Returns:
        Current configuration
    """
    try:
        config = get_or_create_config(user_id, db)
        
        return {
            "success": True,
            "config": {
                "user_id": config.user_id,
                "max_investment_amount": float(config.max_investment_amount),
                "max_position_size": float(config.max_position_size),
                "risk_level": config.risk_level,
                "buy_threshold": config.buy_threshold,
                "sell_threshold": config.sell_threshold,
                "stop_loss_percentage": float(config.stop_loss_percentage),
                "daily_loss_limit": float(config.daily_loss_limit) if config.daily_loss_limit else None,
                "trading_start_time": config.trading_start_time,
                "trading_end_time": config.trading_end_time,
                "notification_email": config.notification_email,
                "is_enabled": config.is_enabled,
                "allowed_symbols": config.allowed_symbols.split(",") if config.allowed_symbols else [],
                "excluded_symbols": config.excluded_symbols.split(",") if config.excluded_symbols else []
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting trading config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get configuration: {str(e)}"
        )


@router.post("/auto-trade/start", response_model=dict, status_code=status.HTTP_200_OK)
async def start_auto_trading(
    user_id: str = Query(default="default_user", description="User identifier"),
    db: Session = Depends(get_db)
):
    """
    Start auto-trading system
    
    Args:
        user_id: User identifier
        db: Database session
    
    Returns:
        Start status
    
    Requirements: 12.1
    """
    try:
        # Get config
        config = get_or_create_config(user_id, db)
        
        # Enable auto-trading
        config.is_enabled = True
        config.updated_at = datetime.now()
        db.commit()
        
        # Get or create trading engine
        engine = get_trading_engine(user_id, db)
        
        # Start engine
        result = engine.start(config)
        
        logger.info(f"Auto-trading started for user {user_id}")
        
        return {
            "success": True,
            "message": "Auto-trading started successfully",
            "status": engine.get_status(config)
        }
    
    except Exception as e:
        logger.error(f"Error starting auto-trading: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start auto-trading: {str(e)}"
        )


@router.post("/auto-trade/stop", response_model=dict, status_code=status.HTTP_200_OK)
async def stop_auto_trading(
    user_id: str = Query(default="default_user", description="User identifier"),
    reason: str = Query(default="User requested", description="Reason for stopping"),
    db: Session = Depends(get_db)
):
    """
    Stop auto-trading system
    
    Args:
        user_id: User identifier
        reason: Reason for stopping
        db: Database session
    
    Returns:
        Stop status
    
    Requirements: 12.1
    """
    try:
        # Get config
        config = get_or_create_config(user_id, db)
        
        # Get trading engine if exists
        if user_id in _trading_engines:
            engine = _trading_engines[user_id]
            result = engine.stop(config, reason)
        else:
            # Just disable in config
            config.is_enabled = False
            config.updated_at = datetime.now()
            db.commit()
            result = {
                "success": True,
                "message": f"Auto-trading stopped: {reason}"
            }
        
        logger.info(f"Auto-trading stopped for user {user_id}: {reason}")
        
        return {
            "success": True,
            "message": result.get("message", "Auto-trading stopped"),
            "reason": reason
        }
    
    except Exception as e:
        logger.error(f"Error stopping auto-trading: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop auto-trading: {str(e)}"
        )


@router.get("/auto-trade/status", response_model=AutoTradeStatus, status_code=status.HTTP_200_OK)
async def get_auto_trading_status(
    user_id: str = Query(default="default_user", description="User identifier"),
    db: Session = Depends(get_db)
):
    """
    Get current auto-trading status
    
    Args:
        user_id: User identifier
        db: Database session
    
    Returns:
        Current status
    
    Requirements: 12.8
    """
    try:
        # Get config
        config = get_or_create_config(user_id, db)
        
        # Get engine status if exists
        if user_id in _trading_engines:
            engine = _trading_engines[user_id]
            status_data = engine.get_status(config)
        else:
            # Return basic status
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            trades_today = db.query(TradeHistory).filter(
                TradeHistory.user_id == user_id,
                TradeHistory.executed_at >= today_start
            ).all()
            
            daily_pnl = sum(
                trade.profit_loss for trade in trades_today
                if trade.profit_loss is not None
            ) or Decimal("0.0")
            
            last_trade = db.query(TradeHistory).filter(
                TradeHistory.user_id == user_id
            ).order_by(TradeHistory.executed_at.desc()).first()
            
            status_data = {
                "is_enabled": config.is_enabled,
                "is_running": False,
                "last_check_time": None,
                "last_trade_time": last_trade.executed_at if last_trade else None,
                "total_trades_today": len(trades_today),
                "daily_profit_loss": float(daily_pnl),
                "message": "System not started" if config.is_enabled else "System disabled"
            }
        
        return AutoTradeStatus(**status_data)
    
    except Exception as e:
        logger.error(f"Error getting auto-trading status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}"
        )


@router.get("/trades/history", response_model=dict, status_code=status.HTTP_200_OK)
async def get_trade_history(
    user_id: str = Query(default="default_user", description="User identifier"),
    days: int = Query(default=7, ge=1, le=90, description="Number of days to retrieve"),
    symbol: Optional[str] = Query(None, description="Filter by stock symbol"),
    action: Optional[str] = Query(None, description="Filter by action (BUY/SELL)"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of records"),
    db: Session = Depends(get_db)
):
    """
    Get trade history
    
    Args:
        user_id: User identifier
        days: Number of days to retrieve
        symbol: Optional symbol filter
        action: Optional action filter
        limit: Maximum number of records
        db: Database session
    
    Returns:
        Trade history list
    
    Requirements: 12.5, 12.8
    """
    try:
        # Calculate date range
        start_date = datetime.now() - timedelta(days=days)
        
        # Build query
        query = db.query(TradeHistory).filter(
            TradeHistory.user_id == user_id,
            TradeHistory.executed_at >= start_date
        )
        
        # Apply filters
        if symbol:
            query = query.filter(TradeHistory.symbol == symbol)
        
        if action:
            query = query.filter(TradeHistory.action == action.upper())
        
        # Order by most recent first
        query = query.order_by(TradeHistory.executed_at.desc())
        
        # Apply limit
        trades = query.limit(limit).all()
        
        # Format response
        trade_list = []
        for trade in trades:
            trade_list.append({
                "id": trade.id,
                "order_id": trade.order_id,
                "symbol": trade.symbol,
                "action": trade.action,
                "quantity": trade.quantity,
                "price": float(trade.price),
                "executed_price": float(trade.executed_price) if trade.executed_price else None,
                "total_amount": float(trade.total_amount) if trade.total_amount else None,
                "profit_loss": float(trade.profit_loss) if trade.profit_loss else None,
                "status": trade.status,
                "signal_ratio": trade.signal_ratio,
                "reasoning": trade.reasoning,
                "message": trade.message,
                "executed_at": trade.executed_at.isoformat() if trade.executed_at else None,
                "created_at": trade.created_at.isoformat()
            })
        
        # Calculate summary statistics
        total_trades = len(trade_list)
        buy_trades = sum(1 for t in trade_list if t["action"] == "BUY")
        sell_trades = sum(1 for t in trade_list if t["action"] == "SELL")
        total_pnl = sum(
            t["profit_loss"] for t in trade_list
            if t["profit_loss"] is not None
        )
        
        logger.info(f"Retrieved {total_trades} trades for user {user_id}")
        
        return {
            "success": True,
            "summary": {
                "total_trades": total_trades,
                "buy_trades": buy_trades,
                "sell_trades": sell_trades,
                "total_profit_loss": total_pnl,
                "date_range_days": days
            },
            "trades": trade_list
        }
    
    except Exception as e:
        logger.error(f"Error getting trade history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get trade history: {str(e)}"
        )


@router.post("/auto-trade/execute", response_model=TradeExecutionResponse, status_code=status.HTTP_200_OK)
async def execute_manual_trade(
    trade_request: TradeExecutionRequest,
    user_id: str = Query(default="default_user", description="User identifier"),
    db: Session = Depends(get_db)
):
    """
    Execute a manual trade (for testing or manual intervention)
    
    Args:
        trade_request: Trade execution request
        user_id: User identifier
        db: Database session
    
    Returns:
        Trade execution result
    
    Requirements: 12.5
    """
    try:
        # Get config
        config = get_or_create_config(user_id, db)
        
        # Get or create trading engine
        engine = get_trading_engine(user_id, db)
        
        # Determine signal ratio based on action
        signal_ratio = 100 if trade_request.action == "BUY" else 0
        
        # Process the trade
        result = engine.process_signal(
            config,
            trade_request.symbol,
            signal_ratio,
            f"Manual trade: {trade_request.action}"
        )
        
        logger.info(f"Manual trade executed for user {user_id}: {result}")
        
        return TradeExecutionResponse(
            success=result.get("success", False),
            order_id=result.get("order_id"),
            message=result.get("message", "Trade processed"),
            trade_details=result
        )
    
    except Exception as e:
        logger.error(f"Error executing manual trade: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute trade: {str(e)}"
        )


@router.post("/auto-trade/monitor", response_model=dict, status_code=status.HTTP_200_OK)
async def monitor_positions(
    user_id: str = Query(default="default_user", description="User identifier"),
    db: Session = Depends(get_db)
):
    """
    Manually trigger position monitoring (stop-loss checks)
    
    Args:
        user_id: User identifier
        db: Database session
    
    Returns:
        Monitoring results
    
    Requirements: 12.7
    """
    try:
        # Get config
        config = get_or_create_config(user_id, db)
        
        # Get or create trading engine
        engine = get_trading_engine(user_id, db)
        
        # Monitor positions
        actions = engine.monitor_positions(config)
        
        logger.info(f"Position monitoring completed for user {user_id}: {len(actions)} actions taken")
        
        return {
            "success": True,
            "message": f"Monitoring completed, {len(actions)} actions taken",
            "actions": actions,
            "checked_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error monitoring positions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to monitor positions: {str(e)}"
        )
