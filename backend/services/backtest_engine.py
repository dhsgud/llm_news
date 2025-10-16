"""
Backtesting Engine
Simulates trading strategy against historical data
Requirements: Task 27
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging
import numpy as np

try:
    from models.backtest_models import BacktestRun, BacktestTrade, BacktestDailyStats
    from models.backtest_schemas import BacktestStrategyConfig, BacktestMetrics
    from models.stock_price import StockPrice
    from models.sentiment_analysis import SentimentAnalysis
    from services.signal_generator import SignalCalculator
except ImportError:
    from models.backtest_models import BacktestRun, BacktestTrade, BacktestDailyStats
    from models.backtest_schemas import BacktestStrategyConfig, BacktestMetrics
    from models.stock_price import StockPrice
    from models.sentiment_analysis import SentimentAnalysis
    from services.signal_generator import SignalCalculator


logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    Engine for running backtests on historical data
    Simulates trading strategy execution and calculates performance metrics
    """
    
    def __init__(self, db: Session):
        """
        Initialize backtest engine
        
        Args:
            db: Database session
        """
        self.db = db
        self.signal_calculator = SignalCalculator()
    
    def run_backtest(
        self,
        backtest_run: BacktestRun,
        strategy_config: BacktestStrategyConfig
    ) -> BacktestRun:
        """
        Execute a backtest run
        
        Args:
            backtest_run: BacktestRun database object
            strategy_config: Strategy configuration
        
        Returns:
            Updated BacktestRun object with results
        """
        try:
            logger.info(f"Starting backtest: {backtest_run.name}")
            
            # Update status
            backtest_run.status = "RUNNING"
            backtest_run.started_at = datetime.utcnow()
            self.db.commit()
            
            # Initialize portfolio state
            portfolio = {
                "cash": float(backtest_run.initial_capital),
                "holdings": {},  # symbol -> {quantity, avg_price}
                "peak_value": float(backtest_run.initial_capital)
            }
            
            # Get trading days in the period
            trading_days = self._get_trading_days(
                backtest_run.start_date,
                backtest_run.end_date
            )
            
            if not trading_days:
                raise ValueError("No trading days found in the specified period")
            
            # Run simulation day by day
            for current_date in trading_days:
                self._simulate_trading_day(
                    backtest_run,
                    strategy_config,
                    portfolio,
                    current_date
                )
            
            # Calculate final metrics
            self._calculate_metrics(backtest_run, portfolio)
            
            # Update status
            backtest_run.status = "COMPLETED"
            backtest_run.completed_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Backtest completed: {backtest_run.name}")
            return backtest_run
        
        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            backtest_run.status = "FAILED"
            backtest_run.error_message = str(e)
            backtest_run.completed_at = datetime.utcnow()
            self.db.commit()
            raise
    
    def _get_trading_days(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[datetime]:
        """
        Get list of trading days with available data
        
        Args:
            start_date: Start date
            end_date: End date
        
        Returns:
            List of datetime objects representing trading days
        """
        # Query distinct dates from stock price data
        dates = self.db.query(StockPrice.timestamp).filter(
            and_(
                StockPrice.timestamp >= start_date,
                StockPrice.timestamp <= end_date
            )
        ).distinct().order_by(StockPrice.timestamp).all()
        
        return [date[0] for date in dates]
    
    def _simulate_trading_day(
        self,
        backtest_run: BacktestRun,
        strategy_config: BacktestStrategyConfig,
        portfolio: Dict[str, Any],
        current_date: datetime
    ) -> None:
        """
        Simulate trading for a single day
        
        Args:
            backtest_run: BacktestRun object
            strategy_config: Strategy configuration
            portfolio: Current portfolio state
            current_date: Current simulation date
        """
        # Get available symbols for this date
        symbols = self._get_available_symbols(current_date, strategy_config)
        
        # Check stop-loss for existing positions
        self._check_stop_losses(
            backtest_run,
            strategy_config,
            portfolio,
            current_date
        )
        
        # Generate signals and execute trades
        for symbol in symbols:
            signal_ratio = self._calculate_signal(symbol, current_date)
            
            if signal_ratio is None:
                continue
            
            # Determine action
            if signal_ratio >= strategy_config.buy_threshold:
                self._execute_buy(
                    backtest_run,
                    strategy_config,
                    portfolio,
                    symbol,
                    signal_ratio,
                    current_date
                )
            elif signal_ratio <= strategy_config.sell_threshold:
                self._execute_sell(
                    backtest_run,
                    portfolio,
                    symbol,
                    signal_ratio,
                    current_date
                )
        
        # Record daily statistics
        self._record_daily_stats(backtest_run, portfolio, current_date)
    
    def _get_available_symbols(
        self,
        date: datetime,
        strategy_config: BacktestStrategyConfig
    ) -> List[str]:
        """
        Get symbols available for trading on a specific date
        
        Args:
            date: Trading date
            strategy_config: Strategy configuration
        
        Returns:
            List of stock symbols
        """
        query = self.db.query(StockPrice.symbol).filter(
            StockPrice.timestamp == date
        ).distinct()
        
        # Filter by configured symbols if specified
        if strategy_config.symbols:
            query = query.filter(StockPrice.symbol.in_(strategy_config.symbols))
        
        symbols = [row[0] for row in query.all()]
        return symbols
    
    def _calculate_signal(
        self,
        symbol: str,
        date: datetime
    ) -> Optional[int]:
        """
        Calculate trading signal for a symbol on a specific date
        
        Args:
            symbol: Stock symbol
            date: Trading date
        
        Returns:
            Signal ratio (0-100) or None if insufficient data
        """
        try:
            # Get sentiment data for the past 7 days
            start_date = date - timedelta(days=7)
            
            # Get sentiments for this period
            # Note: We need to join with news articles to filter by date
            try:
                from models.news_article import NewsArticle
            except ImportError:
                from models.news_article import NewsArticle
            
            sentiments = self.db.query(SentimentAnalysis).join(
                NewsArticle, SentimentAnalysis.article_id == NewsArticle.id
            ).filter(
                and_(
                    NewsArticle.published_date >= start_date,
                    NewsArticle.published_date <= date
                )
            ).all()
            
            if not sentiments:
                return None
            
            # Calculate signal using SignalCalculator
            # For simplicity, use a basic calculation
            avg_sentiment = sum(s.score for s in sentiments) / len(sentiments)
            
            # Normalize to 0-100 range
            # Assuming sentiment_score is in range [-1.5, 1.0]
            normalized = ((avg_sentiment + 1.5) / 2.5) * 100
            signal_ratio = max(0, min(100, int(normalized)))
            
            return signal_ratio
        
        except Exception as e:
            logger.error(f"Error calculating signal for {symbol}: {e}")
            return None
    
    def _get_stock_price(
        self,
        symbol: str,
        date: datetime
    ) -> Optional[Decimal]:
        """
        Get stock price for a symbol on a specific date
        
        Args:
            symbol: Stock symbol
            date: Trading date
        
        Returns:
            Stock price or None if not available
        """
        price_record = self.db.query(StockPrice).filter(
            and_(
                StockPrice.symbol == symbol,
                StockPrice.timestamp == date
            )
        ).first()
        
        return price_record.price if price_record else None
    
    def _execute_buy(
        self,
        backtest_run: BacktestRun,
        strategy_config: BacktestStrategyConfig,
        portfolio: Dict[str, Any],
        symbol: str,
        signal_ratio: int,
        date: datetime
    ) -> None:
        """
        Execute a buy order in the backtest
        
        Args:
            backtest_run: BacktestRun object
            strategy_config: Strategy configuration
            portfolio: Current portfolio state
            symbol: Stock symbol
            signal_ratio: Signal strength
            date: Trading date
        """
        # Skip if already holding this symbol
        if symbol in portfolio["holdings"]:
            return
        
        price = self._get_stock_price(symbol, date)
        if price is None:
            return
        
        # Calculate position size
        max_position = float(strategy_config.max_position_size)
        available_cash = portfolio["cash"]
        
        position_size = min(max_position, available_cash * 0.9)  # Use max 90% of cash
        
        if position_size < float(price):
            return  # Not enough cash
        
        quantity = int(position_size / float(price))
        total_cost = quantity * float(price)
        
        if total_cost > available_cash:
            return
        
        # Execute trade
        portfolio["cash"] -= total_cost
        portfolio["holdings"][symbol] = {
            "quantity": quantity,
            "avg_price": float(price)
        }
        
        # Record trade
        trade = BacktestTrade(
            backtest_run_id=backtest_run.id,
            symbol=symbol,
            action="BUY",
            quantity=quantity,
            price=float(price),
            total_amount=total_cost,
            signal_ratio=signal_ratio,
            reasoning=f"Signal ratio {signal_ratio} >= buy threshold",
            executed_at=date
        )
        self.db.add(trade)
        
        logger.debug(f"BUY: {quantity} {symbol} @ {price} on {date}")
    
    def _execute_sell(
        self,
        backtest_run: BacktestRun,
        portfolio: Dict[str, Any],
        symbol: str,
        signal_ratio: int,
        date: datetime,
        reason: str = "Signal threshold"
    ) -> None:
        """
        Execute a sell order in the backtest
        
        Args:
            backtest_run: BacktestRun object
            portfolio: Current portfolio state
            symbol: Stock symbol
            signal_ratio: Signal strength
            date: Trading date
            reason: Reason for selling
        """
        # Skip if not holding this symbol
        if symbol not in portfolio["holdings"]:
            return
        
        price = self._get_stock_price(symbol, date)
        if price is None:
            return
        
        holding = portfolio["holdings"][symbol]
        quantity = holding["quantity"]
        avg_price = holding["avg_price"]
        
        total_proceeds = quantity * float(price)
        profit_loss = total_proceeds - (quantity * avg_price)
        profit_loss_pct = (profit_loss / (quantity * avg_price)) * 100
        
        # Execute trade
        portfolio["cash"] += total_proceeds
        del portfolio["holdings"][symbol]
        
        # Record trade
        trade = BacktestTrade(
            backtest_run_id=backtest_run.id,
            symbol=symbol,
            action="SELL",
            quantity=quantity,
            price=float(price),
            total_amount=total_proceeds,
            signal_ratio=signal_ratio,
            reasoning=reason,
            profit_loss=profit_loss,
            profit_loss_percentage=profit_loss_pct,
            executed_at=date
        )
        self.db.add(trade)
        
        logger.debug(f"SELL: {quantity} {symbol} @ {price} on {date} (P/L: {profit_loss:.2f})")
    
    def _check_stop_losses(
        self,
        backtest_run: BacktestRun,
        strategy_config: BacktestStrategyConfig,
        portfolio: Dict[str, Any],
        date: datetime
    ) -> None:
        """
        Check and execute stop-loss orders
        
        Args:
            backtest_run: BacktestRun object
            strategy_config: Strategy configuration
            portfolio: Current portfolio state
            date: Trading date
        """
        stop_loss_pct = float(strategy_config.stop_loss_percentage)
        
        for symbol in list(portfolio["holdings"].keys()):
            holding = portfolio["holdings"][symbol]
            current_price = self._get_stock_price(symbol, date)
            
            if current_price is None:
                continue
            
            avg_price = holding["avg_price"]
            loss_pct = ((float(current_price) - avg_price) / avg_price) * 100
            
            if loss_pct <= -stop_loss_pct:
                self._execute_sell(
                    backtest_run,
                    portfolio,
                    symbol,
                    0,
                    date,
                    reason=f"STOP-LOSS: {loss_pct:.2f}%"
                )
    
    def _record_daily_stats(
        self,
        backtest_run: BacktestRun,
        portfolio: Dict[str, Any],
        date: datetime
    ) -> None:
        """
        Record daily portfolio statistics
        
        Args:
            backtest_run: BacktestRun object
            portfolio: Current portfolio state
            date: Trading date
        """
        # Calculate portfolio value
        invested_amount = 0.0
        holdings_list = []
        
        for symbol, holding in portfolio["holdings"].items():
            current_price = self._get_stock_price(symbol, date)
            if current_price:
                value = holding["quantity"] * float(current_price)
                invested_amount += value
                holdings_list.append({
                    "symbol": symbol,
                    "quantity": holding["quantity"],
                    "avg_price": holding["avg_price"],
                    "current_price": float(current_price),
                    "value": value
                })
        
        portfolio_value = portfolio["cash"] + invested_amount
        
        # Calculate returns
        initial_capital = float(backtest_run.initial_capital)
        cumulative_return = ((portfolio_value - initial_capital) / initial_capital) * 100
        
        # Calculate drawdown
        if portfolio_value > portfolio["peak_value"]:
            portfolio["peak_value"] = portfolio_value
        
        drawdown = ((portfolio["peak_value"] - portfolio_value) / portfolio["peak_value"]) * 100
        
        # Get previous day stats for daily return
        prev_stats = self.db.query(BacktestDailyStats).filter(
            BacktestDailyStats.backtest_run_id == backtest_run.id
        ).order_by(BacktestDailyStats.date.desc()).first()
        
        daily_return = None
        if prev_stats:
            daily_return = ((portfolio_value - prev_stats.portfolio_value) / prev_stats.portfolio_value) * 100
        
        # Record stats
        stats = BacktestDailyStats(
            backtest_run_id=backtest_run.id,
            date=date,
            portfolio_value=portfolio_value,
            cash_balance=portfolio["cash"],
            invested_amount=invested_amount,
            daily_return=daily_return,
            cumulative_return=cumulative_return,
            drawdown=drawdown,
            holdings=holdings_list
        )
        self.db.add(stats)
    
    def _calculate_metrics(
        self,
        backtest_run: BacktestRun,
        portfolio: Dict[str, Any]
    ) -> None:
        """
        Calculate final performance metrics
        
        Args:
            backtest_run: BacktestRun object
            portfolio: Final portfolio state
        """
        # Get all trades
        trades = self.db.query(BacktestTrade).filter(
            BacktestTrade.backtest_run_id == backtest_run.id
        ).all()
        
        # Get final portfolio value
        final_stats = self.db.query(BacktestDailyStats).filter(
            BacktestDailyStats.backtest_run_id == backtest_run.id
        ).order_by(BacktestDailyStats.date.desc()).first()
        
        final_capital = final_stats.portfolio_value if final_stats else float(backtest_run.initial_capital)
        
        # Basic metrics
        backtest_run.final_capital = final_capital
        backtest_run.total_return = ((final_capital - float(backtest_run.initial_capital)) / float(backtest_run.initial_capital)) * 100
        backtest_run.total_trades = len(trades)
        
        # Win/loss metrics
        sell_trades = [t for t in trades if t.action == "SELL"]
        winning_trades = [t for t in sell_trades if t.profit_loss and t.profit_loss > 0]
        losing_trades = [t for t in sell_trades if t.profit_loss and t.profit_loss < 0]
        
        backtest_run.winning_trades = len(winning_trades)
        backtest_run.losing_trades = len(losing_trades)
        backtest_run.win_rate = (len(winning_trades) / len(sell_trades) * 100) if sell_trades else 0.0
        
        # Risk metrics
        all_stats = self.db.query(BacktestDailyStats).filter(
            BacktestDailyStats.backtest_run_id == backtest_run.id
        ).order_by(BacktestDailyStats.date).all()
        
        if all_stats:
            # Max drawdown
            drawdowns = [s.drawdown for s in all_stats if s.drawdown is not None]
            backtest_run.max_drawdown = max(drawdowns) if drawdowns else 0.0
            
            # Sharpe ratio
            daily_returns = [s.daily_return for s in all_stats if s.daily_return is not None]
            if daily_returns:
                avg_return = np.mean(daily_returns)
                std_return = np.std(daily_returns)
                backtest_run.sharpe_ratio = (avg_return / std_return * np.sqrt(252)) if std_return > 0 else 0.0
                
                # Sortino ratio (using only negative returns for std)
                negative_returns = [r for r in daily_returns if r < 0]
                if negative_returns:
                    downside_std = np.std(negative_returns)
                    backtest_run.sortino_ratio = (avg_return / downside_std * np.sqrt(252)) if downside_std > 0 else 0.0
        
        self.db.commit()
