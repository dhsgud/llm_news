"""
Trading-related Pydantic schemas
These are data transfer objects for trading operations, not database models
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal
from decimal import Decimal


class Order(BaseModel):
    """
    Schema for placing a stock order
    Used for buy/sell order requests to brokerage APIs
    """
    symbol: str = Field(..., max_length=20, description="Stock symbol/ticker")
    trade_type: Literal["BUY", "SELL"] = Field(..., description="Order type: BUY or SELL")
    quantity: int = Field(..., gt=0, description="Number of shares to trade")
    price: Optional[Decimal] = Field(None, gt=0, description="Limit price (optional for market orders)")
    order_type: Literal["MARKET", "LIMIT"] = Field(default="MARKET", description="Order execution type")
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "005930",
                "trade_type": "BUY",
                "quantity": 10,
                "price": 75000.00,
                "order_type": "LIMIT"
            }
        }


class TradeResult(BaseModel):
    """
    Schema for trade execution result
    Returned after an order is executed through brokerage API
    """
    order_id: str = Field(..., description="Unique order identifier from brokerage")
    symbol: str = Field(..., max_length=20, description="Stock symbol/ticker")
    trade_type: Literal["BUY", "SELL"] = Field(..., description="Order type: BUY or SELL")
    quantity: int = Field(..., gt=0, description="Number of shares traded")
    executed_price: Decimal = Field(..., gt=0, description="Actual execution price per share")
    total_amount: Decimal = Field(..., description="Total transaction amount")
    executed_at: datetime = Field(..., description="Timestamp of order execution")
    status: Literal["SUCCESS", "FAILED", "PENDING", "PARTIAL"] = Field(..., description="Order execution status")
    message: Optional[str] = Field(None, description="Additional information or error message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "order_id": "ORD20251007001",
                "symbol": "005930",
                "trade_type": "BUY",
                "quantity": 10,
                "executed_price": 74500.00,
                "total_amount": 745000.00,
                "executed_at": "2025-10-07T14:30:00",
                "status": "SUCCESS",
                "message": "Order executed successfully"
            }
        }


class OrderRequest(BaseModel):
    """
    Extended order request with additional parameters
    """
    symbol: str = Field(..., max_length=20)
    trade_type: Literal["BUY", "SELL"]
    quantity: int = Field(..., gt=0)
    price: Optional[Decimal] = Field(None, gt=0)
    order_type: Literal["MARKET", "LIMIT"] = "MARKET"
    signal_ratio: Optional[int] = Field(None, ge=0, le=100, description="AI signal ratio that triggered this order")
    reasoning: Optional[str] = Field(None, description="Reasoning for the trade decision")


class OrderResponse(BaseModel):
    """
    Response after submitting an order
    """
    success: bool
    order_id: Optional[str] = None
    message: str
    trade_result: Optional[TradeResult] = None
