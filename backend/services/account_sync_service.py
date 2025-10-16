"""
Account Synchronization Service

Synchronizes account holdings and calculates average purchase prices
from brokerage API to local database.

Requirements: 11.6
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_

from services.brokerage_connector import BrokerageAPIBase
from models.account_holding import AccountHolding, AccountHoldingCreate
from app.database import SessionLocal

logger = logging.getLogger(__name__)


class AccountSyncService:
    """
    Synchronizes account information from brokerage API
    
    Responsibilities:
    - Sync holdings from brokerage API
    - Calculate and update average purchase prices
    - Track position changes
    - Update current prices
    
    Requirements: 11.6
    """
    
    def __init__(self, broker_api: BrokerageAPIBase):
        """
        Initialize account sync service
        
        Args:
            broker_api: Brokerage API instance
        """
        self.broker_api = broker_api
        logger.info("AccountSyncService initialized")
    
    def sync_holdings(self, db: Session = None) -> Dict:
        """
        Synchronize account holdings from brokerage API
        
        Fetches current holdings and updates database with:
        - Stock symbols and quantities
        - Average purchase prices
        - Current market prices
        
        Args:
            db: Database session (optional)
            
        Returns:
            Dict with sync statistics
            
        Requirements: 11.6
        """
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True
        
        try:
            # Get holdings from brokerage API
            holdings_data = self.broker_api.get_account_holdings()
            
            logger.info(f"Fetched {len(holdings_data)} holdings from brokerage API")
            
            # Get existing holdings from database
            existing_holdings = {
                h.symbol: h for h in db.query(AccountHolding).all()
            }
            
            stats = {
                "total_holdings": len(holdings_data),
                "new_holdings": 0,
                "updated_holdings": 0,
                "removed_holdings": 0,
                "errors": 0
            }
            
            # Track which symbols are in the API response
            api_symbols = set()
            
            # Process each holding from API
            for holding_data in holdings_data:
                symbol = holding_data["symbol"]
                api_symbols.add(symbol)
                
                try:
                    if symbol in existing_holdings:
                        # Update existing holding
                        self._update_holding(
                            existing_holdings[symbol],
                            holding_data,
                            db
                        )
                        stats["updated_holdings"] += 1
                    else:
                        # Create new holding
                        self._create_holding(holding_data, db)
                        stats["new_holdings"] += 1
                        
                except Exception as e:
                    logger.error(f"Failed to process holding {symbol}: {e}")
                    stats["errors"] += 1
            
            # Remove holdings that are no longer in the account
            for symbol, holding in existing_holdings.items():
                if symbol not in api_symbols:
                    db.delete(holding)
                    stats["removed_holdings"] += 1
                    logger.info(f"Removed holding {symbol} (no longer in account)")
            
            db.commit()
            
            logger.info(
                f"Holdings sync completed: {stats['new_holdings']} new, "
                f"{stats['updated_holdings']} updated, "
                f"{stats['removed_holdings']} removed, "
                f"{stats['errors']} errors"
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to sync holdings: {e}")
            db.rollback()
            return {
                "total_holdings": 0,
                "new_holdings": 0,
                "updated_holdings": 0,
                "removed_holdings": 0,
                "errors": 1,
                "error_message": str(e)
            }
        finally:
            if should_close:
                db.close()
    
    def update_current_prices(self, db: Session = None) -> int:
        """
        Update current prices for all holdings
        
        Args:
            db: Database session (optional)
            
        Returns:
            Number of holdings updated
        """
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True
        
        try:
            holdings = db.query(AccountHolding).all()
            
            if not holdings:
                logger.info("No holdings to update prices for")
                return 0
            
            updated_count = 0
            
            for holding in holdings:
                try:
                    # Get current price from brokerage API
                    price_data = self.broker_api.get_stock_price(holding.symbol)
                    
                    # Update current price
                    holding.current_price = price_data.price
                    holding.updated_at = datetime.now()
                    
                    updated_count += 1
                    
                    logger.debug(
                        f"Updated price for {holding.symbol}: {price_data.price}"
                    )
                    
                except Exception as e:
                    logger.error(
                        f"Failed to update price for {holding.symbol}: {e}"
                    )
            
            db.commit()
            
            logger.info(f"Updated prices for {updated_count}/{len(holdings)} holdings")
            
            return updated_count
            
        except Exception as e:
            logger.error(f"Failed to update current prices: {e}")
            db.rollback()
            return 0
        finally:
            if should_close:
                db.close()
    
    def get_holdings_summary(self, db: Session = None) -> Dict:
        """
        Get summary of current holdings
        
        Args:
            db: Database session (optional)
            
        Returns:
            Dict with holdings summary including profit/loss
        """
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True
        
        try:
            holdings = db.query(AccountHolding).all()
            
            if not holdings:
                return {
                    "total_holdings": 0,
                    "total_investment": 0.0,
                    "total_value": 0.0,
                    "total_profit_loss": 0.0,
                    "profit_loss_percentage": 0.0,
                    "holdings": []
                }
            
            total_investment = Decimal("0")
            total_value = Decimal("0")
            holdings_list = []
            
            for holding in holdings:
                # Calculate investment amount
                investment = holding.average_price * holding.quantity
                total_investment += investment
                
                # Calculate current value
                current_price = holding.current_price or holding.average_price
                current_value = current_price * holding.quantity
                total_value += current_value
                
                # Calculate profit/loss
                profit_loss = current_value - investment
                profit_loss_pct = (
                    (profit_loss / investment * 100) if investment > 0 else 0
                )
                
                holdings_list.append({
                    "symbol": holding.symbol,
                    "quantity": holding.quantity,
                    "average_price": float(holding.average_price),
                    "current_price": float(current_price),
                    "investment": float(investment),
                    "current_value": float(current_value),
                    "profit_loss": float(profit_loss),
                    "profit_loss_percentage": float(profit_loss_pct),
                    "updated_at": holding.updated_at.isoformat()
                })
            
            total_profit_loss = total_value - total_investment
            total_profit_loss_pct = (
                (total_profit_loss / total_investment * 100)
                if total_investment > 0 else 0
            )
            
            summary = {
                "total_holdings": len(holdings),
                "total_investment": float(total_investment),
                "total_value": float(total_value),
                "total_profit_loss": float(total_profit_loss),
                "profit_loss_percentage": float(total_profit_loss_pct),
                "holdings": holdings_list,
                "last_updated": max(
                    (h.updated_at for h in holdings),
                    default=datetime.now()
                ).isoformat()
            }
            
            logger.info(
                f"Holdings summary: {len(holdings)} positions, "
                f"P/L: {total_profit_loss_pct:.2f}%"
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get holdings summary: {e}")
            return {
                "error": str(e)
            }
        finally:
            if should_close:
                db.close()
    
    def calculate_average_price(
        self,
        symbol: str,
        new_quantity: int,
        new_price: Decimal,
        db: Session = None
    ) -> Optional[Decimal]:
        """
        Calculate new average purchase price after a trade
        
        Uses weighted average formula:
        new_avg = (old_avg * old_qty + new_price * new_qty) / (old_qty + new_qty)
        
        Args:
            symbol: Stock symbol
            new_quantity: Quantity bought/sold (negative for sell)
            new_price: Price of the trade
            db: Database session (optional)
            
        Returns:
            New average price, or None if calculation fails
            
        Requirements: 11.6
        """
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True
        
        try:
            holding = db.query(AccountHolding).filter(
                AccountHolding.symbol == symbol
            ).first()
            
            if not holding:
                # New position
                if new_quantity > 0:
                    logger.info(
                        f"New position for {symbol}: {new_quantity} @ {new_price}"
                    )
                    return new_price
                else:
                    logger.warning(
                        f"Cannot sell {symbol}: no existing position"
                    )
                    return None
            
            old_quantity = holding.quantity
            old_avg_price = holding.average_price
            
            if new_quantity > 0:
                # Buying - calculate weighted average
                total_cost = (old_avg_price * old_quantity) + (new_price * new_quantity)
                total_quantity = old_quantity + new_quantity
                new_avg_price = total_cost / total_quantity
                
                logger.info(
                    f"Updated avg price for {symbol}: "
                    f"{old_avg_price} -> {new_avg_price} "
                    f"(bought {new_quantity} @ {new_price})"
                )
                
                return new_avg_price
                
            else:
                # Selling - average price stays the same
                remaining_quantity = old_quantity + new_quantity  # new_quantity is negative
                
                if remaining_quantity < 0:
                    logger.warning(
                        f"Cannot sell {abs(new_quantity)} of {symbol}: "
                        f"only {old_quantity} available"
                    )
                    return None
                
                logger.info(
                    f"Sold {abs(new_quantity)} of {symbol} @ {new_price} "
                    f"(avg price unchanged: {old_avg_price})"
                )
                
                return old_avg_price
                
        except Exception as e:
            logger.error(f"Failed to calculate average price for {symbol}: {e}")
            return None
        finally:
            if should_close:
                db.close()
    
    def update_holding_after_trade(
        self,
        symbol: str,
        quantity: int,
        price: Decimal,
        db: Session = None
    ) -> bool:
        """
        Update holding after a trade execution
        
        Args:
            symbol: Stock symbol
            quantity: Quantity traded (positive for buy, negative for sell)
            price: Trade price
            db: Database session (optional)
            
        Returns:
            True if update successful
        """
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True
        
        try:
            holding = db.query(AccountHolding).filter(
                AccountHolding.symbol == symbol
            ).first()
            
            if quantity > 0:
                # Buy trade
                if holding:
                    # Update existing holding
                    new_avg_price = self.calculate_average_price(
                        symbol, quantity, price, db
                    )
                    
                    if new_avg_price is None:
                        return False
                    
                    holding.quantity += quantity
                    holding.average_price = new_avg_price
                    holding.updated_at = datetime.now()
                else:
                    # Create new holding
                    holding = AccountHolding(
                        symbol=symbol,
                        quantity=quantity,
                        average_price=price,
                        current_price=price
                    )
                    db.add(holding)
                
                logger.info(
                    f"Updated holding after buy: {symbol} "
                    f"+{quantity} @ {price}"
                )
                
            else:
                # Sell trade
                if not holding:
                    logger.error(f"Cannot sell {symbol}: no holding found")
                    return False
                
                if holding.quantity < abs(quantity):
                    logger.error(
                        f"Cannot sell {abs(quantity)} of {symbol}: "
                        f"only {holding.quantity} available"
                    )
                    return False
                
                holding.quantity += quantity  # quantity is negative
                holding.updated_at = datetime.now()
                
                # Remove holding if quantity is zero
                if holding.quantity == 0:
                    db.delete(holding)
                    logger.info(f"Removed holding {symbol} (quantity = 0)")
                else:
                    logger.info(
                        f"Updated holding after sell: {symbol} "
                        f"{quantity} @ {price}"
                    )
            
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to update holding after trade: {e}")
            db.rollback()
            return False
        finally:
            if should_close:
                db.close()
    
    def _create_holding(self, holding_data: Dict, db: Session) -> AccountHolding:
        """
        Create new holding in database
        
        Args:
            holding_data: Holding data from brokerage API
            db: Database session
            
        Returns:
            Created AccountHolding object
        """
        holding = AccountHolding(
            symbol=holding_data["symbol"],
            quantity=holding_data["quantity"],
            average_price=holding_data["average_price"],
            current_price=holding_data.get("current_price")
        )
        
        db.add(holding)
        
        logger.info(
            f"Created new holding: {holding.symbol} "
            f"({holding.quantity} @ {holding.average_price})"
        )
        
        return holding
    
    def _update_holding(
        self,
        holding: AccountHolding,
        holding_data: Dict,
        db: Session
    ) -> None:
        """
        Update existing holding with new data
        
        Args:
            holding: Existing AccountHolding object
            holding_data: New data from brokerage API
            db: Database session
        """
        # Update fields
        old_quantity = holding.quantity
        old_avg_price = holding.average_price
        
        holding.quantity = holding_data["quantity"]
        holding.average_price = holding_data["average_price"]
        holding.current_price = holding_data.get("current_price")
        holding.updated_at = datetime.now()
        
        # Log changes
        if old_quantity != holding.quantity or old_avg_price != holding.average_price:
            logger.info(
                f"Updated holding {holding.symbol}: "
                f"qty {old_quantity}->{holding.quantity}, "
                f"avg {old_avg_price}->{holding.average_price}"
            )
        else:
            logger.debug(f"Refreshed holding {holding.symbol}")
