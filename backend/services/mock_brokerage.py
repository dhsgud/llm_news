"""
Mock Brokerage API Implementation
For testing and development purposes
"""

from typing import Dict, List
from datetime import datetime
from decimal import Decimal
import logging

from services.brokerage_connector import BrokerageAPIBase, StockPrice, AccountInfo
from models.trading_schemas import Order, TradeResult

logger = logging.getLogger(__name__)


class MockBrokerageAPI(BrokerageAPIBase):
    """
    Mock implementation of brokerage API for testing
    """
    
    def __init__(self, credentials: Dict[str, str]):
        super().__init__(credentials)
        self.mock_holdings = []
        self.mock_balance = Decimal("10000000.00")  # 10M KRW
        self.order_counter = 1
        
    def authenticate(self) -> bool:
        """Mock authentication - always succeeds"""
        self.is_authenticated = True
        self.access_token = "mock_token"
        logger.info("Mock brokerage authenticated")
        return True
    
    def get_stock_price(self, symbol: str) -> StockPrice:
        """Return mock stock price"""
        # Mock prices for common stocks
        mock_prices = {
            "005930": Decimal("75000.00"),  # Samsung
            "000660": Decimal("120000.00"),  # SK Hynix
            "035420": Decimal("250000.00"),  # Naver
        }
        
        price = mock_prices.get(symbol, Decimal("50000.00"))
        
        return StockPrice(
            symbol=symbol,
            price=price,
            volume=1000000,
            open_price=price * Decimal("0.99"),
            high_price=price * Decimal("1.02"),
            low_price=price * Decimal("0.98"),
            timestamp=datetime.now()
        )
    
    def get_account_balance(self) -> AccountInfo:
        """Return mock account balance"""
        total_holdings_value = sum(
            h.get("quantity", 0) * h.get("current_price", Decimal("0.0"))
            for h in self.mock_holdings
        )
        
        return AccountInfo(
            account_number="MOCK-12345",
            balance=self.mock_balance,
            available_cash=self.mock_balance,
            total_assets=self.mock_balance + total_holdings_value,
            holdings=self.mock_holdings
        )
    
    def get_account_holdings(self) -> List[Dict]:
        """Return mock holdings"""
        return self.mock_holdings
    
    def place_order(self, order: Order) -> TradeResult:
        """Mock order placement"""
        order_id = f"MOCK-ORDER-{self.order_counter:06d}"
        self.order_counter += 1
        
        # Get current price
        stock_price = self.get_stock_price(order.symbol)
        executed_price = order.price if order.price else stock_price.price
        total_amount = executed_price * Decimal(order.quantity)
        
        # Simulate order execution
        if order.trade_type == "BUY":
            # Check if enough balance
            if total_amount > self.mock_balance:
                return TradeResult(
                    order_id=order_id,
                    symbol=order.symbol,
                    trade_type=order.trade_type,
                    quantity=order.quantity,
                    executed_price=executed_price,
                    total_amount=total_amount,
                    status="FAILED",
                    message="Insufficient balance",
                    executed_at=datetime.now()
                )
            
            # Deduct balance
            self.mock_balance -= total_amount
            
            # Add to holdings
            existing = next(
                (h for h in self.mock_holdings if h["symbol"] == order.symbol),
                None
            )
            
            if existing:
                # Update existing holding
                total_qty = existing["quantity"] + order.quantity
                total_cost = (existing["average_price"] * existing["quantity"]) + total_amount
                existing["quantity"] = total_qty
                existing["average_price"] = total_cost / total_qty
                existing["current_price"] = executed_price
            else:
                # Add new holding
                self.mock_holdings.append({
                    "symbol": order.symbol,
                    "quantity": order.quantity,
                    "average_price": executed_price,
                    "current_price": executed_price
                })
        
        elif order.trade_type == "SELL":
            # Find holding
            existing = next(
                (h for h in self.mock_holdings if h["symbol"] == order.symbol),
                None
            )
            
            if not existing or existing["quantity"] < order.quantity:
                return TradeResult(
                    order_id=order_id,
                    symbol=order.symbol,
                    trade_type=order.trade_type,
                    quantity=order.quantity,
                    executed_price=executed_price,
                    total_amount=total_amount,
                    status="FAILED",
                    message="Insufficient holdings",
                    executed_at=datetime.now()
                )
            
            # Add to balance
            self.mock_balance += total_amount
            
            # Update holdings
            existing["quantity"] -= order.quantity
            if existing["quantity"] == 0:
                self.mock_holdings.remove(existing)
        
        logger.info(f"Mock order executed: {order.trade_type} {order.quantity} {order.symbol} @ {executed_price}")
        
        return TradeResult(
            order_id=order_id,
            symbol=order.symbol,
            trade_type=order.trade_type,
            quantity=order.quantity,
            executed_price=executed_price,
            total_amount=total_amount,
            status="SUCCESS",
            message="Order executed successfully",
            executed_at=datetime.now()
        )
    
    def cancel_order(self, order_id: str) -> bool:
        """Mock order cancellation"""
        logger.info(f"Mock order cancelled: {order_id}")
        return True
    
    def get_order_status(self, order_id: str) -> Dict:
        """Mock order status"""
        return {
            "order_id": order_id,
            "status": "COMPLETED",
            "message": "Order completed"
        }
