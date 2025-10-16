"""
Stock Data Collector Module

Collects real-time stock price data from brokerage APIs and stores in database.
Runs periodically to maintain up-to-date stock information.

Requirements: 11.2, 11.3
"""

import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from services.brokerage_connector import BrokerageAPIBase, StockPrice as BrokerageStockPrice
from models.stock_price import StockPrice, StockPriceCreate
from models.account_holding import AccountHolding, AccountHoldingCreate
from app.database import SessionLocal

logger = logging.getLogger(__name__)


class StockDataCollector:
    """
    Collects real-time stock data from brokerage APIs
    
    Responsibilities:
    - Periodic price collection (every 1 minute)
    - Database storage of stock prices
    - Account holdings synchronization
    
    Requirements: 11.2, 11.3
    """
    
    def __init__(
        self,
        broker_api: BrokerageAPIBase,
        symbols: List[str] = None,
        collection_interval_minutes: int = 1
    ):
        """
        Initialize stock data collector
        
        Args:
            broker_api: Brokerage API instance for data collection
            symbols: List of stock symbols to track (default: None, will use holdings)
            collection_interval_minutes: Collection frequency in minutes (default: 1)
        """
        self.broker_api = broker_api
        self.symbols = symbols or []
        self.collection_interval_minutes = collection_interval_minutes
        self.scheduler = BackgroundScheduler()
        self.is_running = False
        
        logger.info(
            f"StockDataCollector initialized with {len(self.symbols)} symbols, "
            f"collection interval: {collection_interval_minutes} minute(s)"
        )
    
    def start_collection(self) -> None:
        """
        Start periodic stock data collection
        
        Schedules collection job to run at specified interval
        """
        if self.is_running:
            logger.warning("Stock data collection is already running")
            return
        
        try:
            # Add job to scheduler
            self.scheduler.add_job(
                func=self.collect_prices,
                trigger=IntervalTrigger(minutes=self.collection_interval_minutes),
                id='stock_price_collection',
                name='Collect stock prices',
                replace_existing=True
            )
            
            # Start scheduler
            self.scheduler.start()
            self.is_running = True
            
            # Run initial collection immediately
            self.collect_prices()
            
            logger.info("Stock data collection started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start stock data collection: {e}")
            raise
    
    def stop_collection(self) -> None:
        """
        Stop periodic stock data collection
        """
        if not self.is_running:
            logger.warning("Stock data collection is not running")
            return
        
        try:
            self.scheduler.shutdown(wait=False)
            self.is_running = False
            logger.info("Stock data collection stopped")
            
        except Exception as e:
            logger.error(f"Failed to stop stock data collection: {e}")
    
    def collect_prices(self) -> Dict[str, bool]:
        """
        Collect current prices for all tracked symbols
        
        Returns:
            Dict[str, bool]: Dictionary mapping symbols to success status
            
        Requirements: 11.2, 11.3
        """
        results = {}
        
        # If no symbols specified, get from account holdings
        if not self.symbols:
            self.symbols = self._get_symbols_from_holdings()
        
        if not self.symbols:
            logger.warning("No symbols to collect prices for")
            return results
        
        logger.info(f"Collecting prices for {len(self.symbols)} symbols")
        
        db = SessionLocal()
        try:
            for symbol in self.symbols:
                try:
                    # Get price from brokerage API
                    price_data = self.broker_api.get_stock_price(symbol)
                    
                    # Store in database
                    success = self._store_price(db, price_data)
                    results[symbol] = success
                    
                    if success:
                        logger.debug(f"Collected price for {symbol}: {price_data.price}")
                    
                except Exception as e:
                    logger.error(f"Failed to collect price for {symbol}: {e}")
                    results[symbol] = False
            
            db.commit()
            logger.info(
                f"Price collection completed: "
                f"{sum(results.values())}/{len(results)} successful"
            )
            
        except Exception as e:
            logger.error(f"Error during price collection: {e}")
            db.rollback()
        finally:
            db.close()
        
        return results
    
    def collect_single_price(self, symbol: str) -> Optional[StockPrice]:
        """
        Collect price for a single symbol
        
        Args:
            symbol: Stock symbol to collect
            
        Returns:
            StockPrice: Stored price record, or None if failed
        """
        db = SessionLocal()
        try:
            # Get price from brokerage API
            price_data = self.broker_api.get_stock_price(symbol)
            
            # Store in database
            success = self._store_price(db, price_data)
            
            if success:
                db.commit()
                logger.info(f"Collected single price for {symbol}: {price_data.price}")
                
                # Query and return the stored record
                stored_price = db.query(StockPrice).filter(
                    StockPrice.symbol == symbol
                ).order_by(StockPrice.timestamp.desc()).first()
                
                return stored_price
            else:
                db.rollback()
                return None
                
        except Exception as e:
            logger.error(f"Failed to collect single price for {symbol}: {e}")
            db.rollback()
            return None
        finally:
            db.close()
    
    def add_symbol(self, symbol: str) -> None:
        """
        Add a symbol to the collection list
        
        Args:
            symbol: Stock symbol to add
        """
        if symbol not in self.symbols:
            self.symbols.append(symbol)
            logger.info(f"Added symbol {symbol} to collection list")
    
    def remove_symbol(self, symbol: str) -> None:
        """
        Remove a symbol from the collection list
        
        Args:
            symbol: Stock symbol to remove
        """
        if symbol in self.symbols:
            self.symbols.remove(symbol)
            logger.info(f"Removed symbol {symbol} from collection list")
    
    def sync_account_holdings(self) -> int:
        """
        Synchronize account holdings from brokerage API to database
        
        Updates holdings information including quantity and average price
        
        Returns:
            int: Number of holdings synchronized
            
        Requirements: 11.6
        """
        db = SessionLocal()
        try:
            # Get holdings from brokerage API
            holdings_data = self.broker_api.get_account_holdings()
            
            logger.info(f"Syncing {len(holdings_data)} holdings from brokerage API")
            
            # Clear existing holdings
            db.query(AccountHolding).delete()
            
            # Insert new holdings
            for holding in holdings_data:
                db_holding = AccountHolding(
                    symbol=holding["symbol"],
                    quantity=holding["quantity"],
                    average_price=holding["average_price"],
                    current_price=holding.get("current_price")
                )
                db.add(db_holding)
                
                # Add symbol to collection list if not already present
                if holding["symbol"] not in self.symbols:
                    self.symbols.append(holding["symbol"])
            
            db.commit()
            
            logger.info(
                f"Successfully synced {len(holdings_data)} holdings. "
                f"Now tracking {len(self.symbols)} symbols."
            )
            
            return len(holdings_data)
            
        except Exception as e:
            logger.error(f"Failed to sync account holdings: {e}")
            db.rollback()
            return 0
        finally:
            db.close()
    
    def get_latest_price(self, symbol: str, db: Session) -> Optional[StockPrice]:
        """
        Get the most recent price for a symbol from database
        
        Args:
            symbol: Stock symbol
            db: Database session
            
        Returns:
            StockPrice: Latest price record, or None if not found
        """
        try:
            return db.query(StockPrice).filter(
                StockPrice.symbol == symbol
            ).order_by(StockPrice.timestamp.desc()).first()
            
        except Exception as e:
            logger.error(f"Failed to get latest price for {symbol}: {e}")
            return None
    
    def get_price_history(
        self,
        symbol: str,
        hours: int = 24,
        db: Session = None
    ) -> List[StockPrice]:
        """
        Get price history for a symbol
        
        Args:
            symbol: Stock symbol
            hours: Number of hours of history to retrieve
            db: Database session (optional, will create if not provided)
            
        Returns:
            List[StockPrice]: List of price records
        """
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True
        
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            prices = db.query(StockPrice).filter(
                StockPrice.symbol == symbol,
                StockPrice.timestamp >= cutoff_time
            ).order_by(StockPrice.timestamp.asc()).all()
            
            return prices
            
        except Exception as e:
            logger.error(f"Failed to get price history for {symbol}: {e}")
            return []
        finally:
            if should_close:
                db.close()
    
    def _store_price(self, db: Session, price_data: BrokerageStockPrice) -> bool:
        """
        Store price data in database
        
        Args:
            db: Database session
            price_data: Price data from brokerage API
            
        Returns:
            bool: True if stored successfully
        """
        try:
            db_price = StockPrice(
                symbol=price_data.symbol,
                price=price_data.price,
                volume=price_data.volume,
                open_price=price_data.open_price,
                high_price=price_data.high_price,
                low_price=price_data.low_price,
                timestamp=price_data.timestamp
            )
            
            db.add(db_price)
            return True
            
        except Exception as e:
            logger.error(f"Failed to store price for {price_data.symbol}: {e}")
            return False
    
    def _get_symbols_from_holdings(self) -> List[str]:
        """
        Get list of symbols from current account holdings
        
        Returns:
            List[str]: List of stock symbols
        """
        db = SessionLocal()
        try:
            holdings = db.query(AccountHolding).all()
            return [h.symbol for h in holdings]
            
        except Exception as e:
            logger.error(f"Failed to get symbols from holdings: {e}")
            return []
        finally:
            db.close()
    
    def cleanup_old_prices(self, days: int = 30) -> int:
        """
        Remove price data older than specified days
        
        Args:
            days: Number of days to retain
            
        Returns:
            int: Number of records deleted
        """
        db = SessionLocal()
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            deleted = db.query(StockPrice).filter(
                StockPrice.timestamp < cutoff_date
            ).delete()
            
            db.commit()
            
            logger.info(f"Cleaned up {deleted} old price records (older than {days} days)")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Failed to cleanup old prices: {e}")
            db.rollback()
            return 0
        finally:
            db.close()
