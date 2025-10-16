"""
Backtesting API Endpoints
REST API for running and managing backtests
Requirements: Task 27
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import logging

try:
    from app.database import get_db
    from models.backtest_models import BacktestRun, BacktestTrade, BacktestDailyStats
    from models.backtest_schemas import (
        BacktestRequest, BacktestResult, BacktestSummary,
        BacktestStrategyConfig, BacktestMetrics, BacktestComparison,
        BacktestTradeResult, BacktestDailyStatsResult
    )
    from services.backtest_engine import BacktestEngine
except ImportError:
    from app.database import get_db
    from models.backtest_models import BacktestRun, BacktestTrade, BacktestDailyStats
    from models.backtest_schemas import (
        BacktestRequest, BacktestResult, BacktestSummary,
        BacktestStrategyConfig, BacktestMetrics, BacktestComparison,
        BacktestTradeResult, BacktestDailyStatsResult
    )
    from services.backtest_engine import BacktestEngine


router = APIRouter(prefix="/api/backtest", tags=["Backtesting"])
logger = logging.getLogger(__name__)


def run_backtest_task(backtest_id: int, db_url: str):
    """Background task to run backtest"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        backtest_run = db.query(BacktestRun).filter(BacktestRun.id == backtest_id).first()
        if not backtest_run:
            return
        
        strategy_config = BacktestStrategyConfig(**backtest_run.strategy_config)
        engine = BacktestEngine(db)
        engine.run_backtest(backtest_run, strategy_config)
    finally:
        db.close()


@router.post("/run", response_model=BacktestSummary)
async def create_backtest(
    request: BacktestRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user_id: str = "default_user"
):
    """
    Create and start a new backtest run
    """
    try:
        # Validate date range
        if request.end_date <= request.start_date:
            raise HTTPException(status_code=400, detail="End date must be after start date")
        
        # Create backtest run
        backtest_run = BacktestRun(
            user_id=user_id,
            name=request.name,
            description=request.description,
            strategy_config=request.strategy_config.model_dump(),
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=float(request.initial_capital),
            status="PENDING"
        )
        
        db.add(backtest_run)
        db.commit()
        db.refresh(backtest_run)
        
        # Start backtest in background
        from config import DATABASE_URL
        background_tasks.add_task(run_backtest_task, backtest_run.id, DATABASE_URL)
        
        logger.info(f"Backtest created: {backtest_run.id}")
        
        return BacktestSummary(
            id=backtest_run.id,
            name=backtest_run.name,
            description=backtest_run.description,
            status=backtest_run.status,
            start_date=backtest_run.start_date,
            end_date=backtest_run.end_date,
            initial_capital=backtest_run.initial_capital,
            final_capital=backtest_run.final_capital,
            total_return=backtest_run.total_return,
            total_trades=backtest_run.total_trades,
            win_rate=backtest_run.win_rate,
            max_drawdown=backtest_run.max_drawdown,
            created_at=backtest_run.created_at,
            completed_at=backtest_run.completed_at
        )
    
    except Exception as e:
        logger.error(f"Error creating backtest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=List[BacktestSummary])
async def list_backtests(
    db: Session = Depends(get_db),
    user_id: str = "default_user",
    limit: int = 50
):
    """
    List all backtest runs for a user
    """
    try:
        backtests = db.query(BacktestRun).filter(
            BacktestRun.user_id == user_id
        ).order_by(BacktestRun.created_at.desc()).limit(limit).all()
        
        return [
            BacktestSummary(
                id=bt.id,
                name=bt.name,
                description=bt.description,
                status=bt.status,
                start_date=bt.start_date,
                end_date=bt.end_date,
                initial_capital=bt.initial_capital,
                final_capital=bt.final_capital,
                total_return=bt.total_return,
                total_trades=bt.total_trades,
                win_rate=bt.win_rate,
                max_drawdown=bt.max_drawdown,
                created_at=bt.created_at,
                completed_at=bt.completed_at
            )
            for bt in backtests
        ]
    
    except Exception as e:
        logger.error(f"Error listing backtests: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{backtest_id}", response_model=BacktestResult)
async def get_backtest_result(
    backtest_id: int,
    db: Session = Depends(get_db),
    include_trades: bool = True,
    include_daily_stats: bool = True
):
    """
    Get detailed results of a backtest run
    """
    try:
        backtest = db.query(BacktestRun).filter(BacktestRun.id == backtest_id).first()
        
        if not backtest:
            raise HTTPException(status_code=404, detail="Backtest not found")
        
        # Build metrics
        metrics = None
        if backtest.status == "COMPLETED":
            trades = db.query(BacktestTrade).filter(
                BacktestTrade.backtest_run_id == backtest_id,
                BacktestTrade.action == "SELL"
            ).all()
            
            winning_trades = [t for t in trades if t.profit_loss and t.profit_loss > 0]
            losing_trades = [t for t in trades if t.profit_loss and t.profit_loss < 0]
            
            avg_win = sum(t.profit_loss for t in winning_trades) / len(winning_trades) if winning_trades else 0
            avg_loss = sum(t.profit_loss for t in losing_trades) / len(losing_trades) if losing_trades else 0
            profit_factor = abs(avg_win * len(winning_trades) / (avg_loss * len(losing_trades))) if losing_trades and avg_loss != 0 else 0
            
            metrics = BacktestMetrics(
                initial_capital=backtest.initial_capital,
                final_capital=backtest.final_capital or 0,
                total_return=backtest.final_capital - backtest.initial_capital if backtest.final_capital else 0,
                total_return_percentage=backtest.total_return or 0,
                total_trades=backtest.total_trades,
                winning_trades=backtest.winning_trades,
                losing_trades=backtest.losing_trades,
                win_rate=backtest.win_rate or 0,
                max_drawdown=backtest.max_drawdown or 0,
                sharpe_ratio=backtest.sharpe_ratio,
                sortino_ratio=backtest.sortino_ratio,
                average_win=avg_win,
                average_loss=avg_loss,
                profit_factor=profit_factor
            )
        
        # Get trades
        trades_list = []
        if include_trades:
            trades = db.query(BacktestTrade).filter(
                BacktestTrade.backtest_run_id == backtest_id
            ).order_by(BacktestTrade.executed_at).all()
            
            trades_list = [
                BacktestTradeResult(
                    symbol=t.symbol,
                    action=t.action,
                    quantity=t.quantity,
                    price=t.price,
                    total_amount=t.total_amount,
                    signal_ratio=t.signal_ratio,
                    reasoning=t.reasoning,
                    profit_loss=t.profit_loss,
                    profit_loss_percentage=t.profit_loss_percentage,
                    executed_at=t.executed_at
                )
                for t in trades
            ]
        
        # Get daily stats
        daily_stats_list = []
        if include_daily_stats:
            stats = db.query(BacktestDailyStats).filter(
                BacktestDailyStats.backtest_run_id == backtest_id
            ).order_by(BacktestDailyStats.date).all()
            
            daily_stats_list = [
                BacktestDailyStatsResult(
                    date=s.date,
                    portfolio_value=s.portfolio_value,
                    cash_balance=s.cash_balance,
                    invested_amount=s.invested_amount,
                    daily_return=s.daily_return,
                    cumulative_return=s.cumulative_return,
                    drawdown=s.drawdown,
                    holdings=s.holdings
                )
                for s in stats
            ]
        
        return BacktestResult(
            id=backtest.id,
            name=backtest.name,
            description=backtest.description,
            status=backtest.status,
            start_date=backtest.start_date,
            end_date=backtest.end_date,
            strategy_config=backtest.strategy_config,
            metrics=metrics,
            trades=trades_list,
            daily_stats=daily_stats_list,
            error_message=backtest.error_message,
            created_at=backtest.created_at,
            started_at=backtest.started_at,
            completed_at=backtest.completed_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting backtest result: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{backtest_id}")
async def delete_backtest(
    backtest_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a backtest run and all associated data
    """
    try:
        backtest = db.query(BacktestRun).filter(BacktestRun.id == backtest_id).first()
        
        if not backtest:
            raise HTTPException(status_code=404, detail="Backtest not found")
        
        db.delete(backtest)
        db.commit()
        
        return {"message": "Backtest deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting backtest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare", response_model=BacktestComparison)
async def compare_backtests(
    backtest_ids: List[int],
    db: Session = Depends(get_db)
):
    """
    Compare multiple backtest runs
    """
    try:
        if len(backtest_ids) < 2:
            raise HTTPException(status_code=400, detail="At least 2 backtests required for comparison")
        
        backtests = db.query(BacktestRun).filter(
            BacktestRun.id.in_(backtest_ids)
        ).all()
        
        if len(backtests) != len(backtest_ids):
            raise HTTPException(status_code=404, detail="One or more backtests not found")
        
        summaries = [
            BacktestSummary(
                id=bt.id,
                name=bt.name,
                description=bt.description,
                status=bt.status,
                start_date=bt.start_date,
                end_date=bt.end_date,
                initial_capital=bt.initial_capital,
                final_capital=bt.final_capital,
                total_return=bt.total_return,
                total_trades=bt.total_trades,
                win_rate=bt.win_rate,
                max_drawdown=bt.max_drawdown,
                created_at=bt.created_at,
                completed_at=bt.completed_at
            )
            for bt in backtests
        ]
        
        # Find best performers
        completed = [bt for bt in backtests if bt.status == "COMPLETED"]
        
        best_return = None
        best_sharpe = None
        lowest_drawdown = None
        
        if completed:
            best_return = max(completed, key=lambda x: x.total_return or 0).id
            best_sharpe = max(completed, key=lambda x: x.sharpe_ratio or 0).id
            lowest_drawdown = min(completed, key=lambda x: x.max_drawdown or float('inf')).id
        
        return BacktestComparison(
            backtests=summaries,
            best_return=best_return,
            best_sharpe=best_sharpe,
            lowest_drawdown=lowest_drawdown
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing backtests: {e}")
        raise HTTPException(status_code=500, detail=str(e))
