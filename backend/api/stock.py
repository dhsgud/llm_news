"""

Stock API Endpoints



Provides endpoints for stock data, stock-specific sentiment analysis,

and account holdings information.

"""



import logging

from datetime import datetime, timedelta

from typing import List, Optional, Dict, Any

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Path

from sqlalchemy.orm import Session

from pydantic import BaseModel, Field



from app.database import get_db

from models import (

    StockPrice, StockPriceResponse,

    AccountHolding, AccountHoldingResponse,

    NewsArticle, SentimentAnalysis

)

from services.stock_data_collector import StockDataCollector

from services.stock_news_filter import StockNewsFilter

from services.account_sync_service import AccountSyncService



logger = logging.getLogger(__name__)



router = APIRouter()





# Response Models

class StockInfoResponse(BaseModel):

    """Response model for stock information"""

    symbol: str = Field(..., description="Stock symbol/code")

    name: Optional[str] = Field(None, description="Stock name")

    current_price: Optional[Decimal] = Field(None, description="Current stock price")

    volume: Optional[int] = Field(None, description="Trading volume")

    open_price: Optional[Decimal] = Field(None, description="Opening price")

    high_price: Optional[Decimal] = Field(None, description="Day high price")

    low_price: Optional[Decimal] = Field(None, description="Day low price")

    market_cap: Optional[Decimal] = Field(None, description="Market capitalization")

    last_updated: Optional[datetime] = Field(None, description="Last price update timestamp")

    price_history: List[StockPriceResponse] = Field(default_factory=list, description="Recent price history")

    related_news: List[Dict[str, Any]] = Field(default_factory=list, description="Related news articles")





class StockSentimentResponse(BaseModel):

    """Response model for stock-specific sentiment analysis"""

    symbol: str = Field(..., description="Stock symbol/code")

    sentiment_score: float = Field(..., description="Average sentiment score")

    news_count: int = Field(..., description="Number of analyzed articles")

    summary: Optional[str] = Field(None, description="Sentiment summary text")

    sentiment_distribution: Dict[str, int] = Field(..., description="Count by sentiment type")

    related_news: List[Dict[str, Any]] = Field(default_factory=list, description="Related news articles")

    recommendation: str = Field(..., description="Buy/Hold/Sell recommendation")

    confidence: str = Field(..., description="Confidence level")

    last_analyzed: Optional[datetime] = Field(None, description="Last analysis timestamp")





class HoldingSummaryResponse(BaseModel):

    """Response model for account holdings summary"""

    total_holdings: int = Field(..., description="Number of different stocks held")

    total_value: Decimal = Field(..., description="Total portfolio value")

    total_cost: Decimal = Field(..., description="Total cost basis")

    profit_loss: Decimal = Field(..., description="Total profit/loss amount")

    profit_loss_percentage: float = Field(..., description="Profit/loss percentage")

    holdings: List[AccountHoldingResponse] = Field(default_factory=list, description="Individual holdings")

    last_updated: datetime = Field(..., description="Last sync timestamp")





@router.get("/stocks/{symbol}", response_model=StockInfoResponse)

async def get_stock_info(

    symbol: str = Path(..., description="Stock symbol/code (e.g., 005930 for Samsung)"),

    hours: int = Query(24, ge=1, le=168, description="Hours of price history to retrieve"),

    db: Session = Depends(get_db)

):

    """

    Get detailed information for a specific stock

    

    Retrieves current price, trading volume, and recent price history

    for the specified stock symbol.

    

    Args:

        symbol: Stock symbol/code

        hours: Number of hours of price history (1-168)

        db: Database session

        

    Returns:

        StockInfoResponse with current price and history

        

    Raises:

        HTTPException: If stock not found or query fails

    """

    logger.info(f"Stock info requested: symbol={symbol}, hours={hours}")

    

    try:

        # Get latest price

        latest_price = db.query(StockPrice).filter(

            StockPrice.symbol == symbol

        ).order_by(StockPrice.timestamp.desc()).first()

        

        if not latest_price:

            logger.warning(f"No price data found for symbol: {symbol}")

            raise HTTPException(

                status_code=404,

                detail=f"No price data found for stock symbol: {symbol}"

            )

        

        # Get price history

        cutoff_time = datetime.now() - timedelta(hours=hours)

        price_history = db.query(StockPrice).filter(

            StockPrice.symbol == symbol,

            StockPrice.timestamp >= cutoff_time

        ).order_by(StockPrice.timestamp.asc()).all()

        

        # Get related news (last 7 days)

        news_filter = StockNewsFilter()

        related_articles = news_filter.filter_news_by_stock(symbol, 7, db)

        

        news_list = []

        for article in related_articles[:5]:  # Limit to 5 most recent

            sentiment_analysis = db.query(SentimentAnalysis).filter(

                SentimentAnalysis.article_id == article.id

            ).first()

            

            news_list.append({

                "id": article.id,

                "title": article.title,

                "summary": article.summary or article.title,

                "published_at": article.published_date.isoformat(),

                "source": article.source,

                "url": article.url,

                "sentiment": sentiment_analysis.sentiment if sentiment_analysis else None,

                "sentiment_score": float(sentiment_analysis.score) if sentiment_analysis else None

            })

        

        # Get stock name from a mapping (you can expand this)
        stock_names = {
            "005930": "Samsung Electronics",
            "000660": "SK Hynix",
            "035420": "NAVER",
            "005380": "Hyundai Motor",
            "051910": "LG Chem",
            "006400": "Samsung SDI",
            "035720": "Kakao",
            "068270": "Celltrion"
        }
        logger.info(f"Retrieved stock info for {symbol}: price={latest_price.price}, history_count={len(price_history)}")

        return response

        

    except HTTPException:

        raise

    except Exception as e:

        logger.error(f"Failed to retrieve stock info for {symbol}: {e}", exc_info=True)

        raise HTTPException(

            status_code=500,

            detail=f"Failed to retrieve stock information: {str(e)}"

        )





@router.get("/stocks/{symbol}/sentiment", response_model=StockSentimentResponse)

async def get_stock_sentiment(

    symbol: str = Path(..., description="Stock symbol/code"),

    days: int = Query(7, ge=1, le=30, description="Number of days to analyze"),

    db: Session = Depends(get_db)

):

    """

    Get sentiment analysis for a specific stock

    

    Analyzes news articles related to the stock and provides

    aggregated sentiment scores and buy/sell recommendation.

    

    Args:

        symbol: Stock symbol/code

        days: Number of days to look back (1-30)

        db: Database session

        

    Returns:

        StockSentimentResponse with sentiment analysis and recommendation

        

    Raises:

        HTTPException: If analysis fails or no data available

    """

    logger.info(f"Stock sentiment requested: symbol={symbol}, days={days}")

    

    try:

        # Initialize stock news filter

        news_filter = StockNewsFilter()

        

        # Get sentiment analysis

        sentiment_data = news_filter.get_stock_sentiment(symbol, days, db)

        

        if sentiment_data["article_count"] == 0:

            logger.warning(f"No sentiment data found for symbol: {symbol}")

            raise HTTPException(

                status_code=404,

                detail=f"No sentiment data available for stock symbol: {symbol}"

            )

        

        # Get related news articles

        related_articles = news_filter.filter_news_by_stock(symbol, days, db)

        

        # Build news list with sentiment

        news_list = []

        for article in related_articles[:10]:  # Limit to 10 most recent

            sentiment_analysis = db.query(SentimentAnalysis).filter(

                SentimentAnalysis.article_id == article.id

            ).first()

            

            news_list.append({

                "id": article.id,

                "title": article.title,

                "published_date": article.published_date.isoformat(),

                "source": article.source,

                "url": article.url,

                "sentiment": sentiment_analysis.sentiment if sentiment_analysis else None,

                "sentiment_score": float(sentiment_analysis.score) if sentiment_analysis else None

            })

        

        # Generate recommendation based on average score

        avg_score = sentiment_data["average_score"]

        if avg_score > 0.5:

            recommendation = "Strong Buy"

            confidence = "High"

            summary = f"{symbol} 종목???�???�스 감성??매우 긍정?�입?�다. 강력??매수 ?�호?�니??"

        elif avg_score > 0.2:

            recommendation = "Buy"

            confidence = "Medium"

            summary = f"{symbol} 종목???�???�스 감성??긍정?�입?�다. 매수�?고려?�볼 ???�습?�다."

        elif avg_score > -0.2:

            recommendation = "Hold"

            confidence = "Medium"

            summary = f"{symbol} 종목???�???�스 감성??중립?�입?�다. 보유 ?�는 관망을 권장?�니??"

        elif avg_score > -0.5:

            recommendation = "Sell"

            confidence = "Medium"

            summary = f"{symbol} 종목???�???�스 감성??부?�적?�니?? 매도�?고려?�볼 ???�습?�다."

        else:

            recommendation = "Strong Sell"

            confidence = "High"

            summary = f"{symbol} 종목???�???�스 감성??매우 부?�적?�니?? 강력??매도 ?�호?�니??"

        

        # Get last analysis timestamp

        last_sentiment = db.query(SentimentAnalysis).join(

            NewsArticle

        ).filter(

            NewsArticle.id == SentimentAnalysis.article_id

        ).order_by(SentimentAnalysis.analyzed_at.desc()).first()

        

        response = StockSentimentResponse(

            symbol=symbol,

            sentiment_score=sentiment_data["average_score"],

            news_count=sentiment_data["article_count"],

            summary=summary,

            sentiment_distribution=sentiment_data["sentiment_distribution"],

            related_news=news_list,

            recommendation=recommendation,

            confidence=confidence,

            last_analyzed=last_sentiment.analyzed_at if last_sentiment else None

        )

        

        logger.info(

            f"Stock sentiment analysis completed for {symbol}: "

            f"avg_score={avg_score:.2f}, recommendation={recommendation}"

        )

        return response

        

    except HTTPException:

        raise

    except Exception as e:

        logger.error(f"Failed to analyze stock sentiment for {symbol}: {e}", exc_info=True)

        raise HTTPException(

            status_code=500,

            detail=f"Failed to analyze stock sentiment: {str(e)}"

        )





@router.get("/account/holdings", response_model=HoldingSummaryResponse)

async def get_account_holdings(

    db: Session = Depends(get_db)

):

    """

    Get account holdings summary with profit/loss calculations

    

    Retrieves all current holdings from the database with calculated

    profit/loss based on current prices vs. average purchase prices.

    

    Note: This endpoint returns cached data from the database.

    Use POST /account/sync to refresh from brokerage API.

    

    Args:

        db: Database session

        

    Returns:

        HoldingSummaryResponse with all holdings and summary statistics

        

    Raises:

        HTTPException: If query fails

    """

    logger.info("Account holdings summary requested")

    

    try:

        # Get all holdings

        holdings = db.query(AccountHolding).filter(

            AccountHolding.quantity > 0

        ).all()

        

        if not holdings:

            logger.info("No holdings found in account")

            return HoldingSummaryResponse(

                total_holdings=0,

                total_value=Decimal("0"),

                total_cost=Decimal("0"),

                profit_loss=Decimal("0"),

                profit_loss_percentage=0.0,

                holdings=[],

                last_updated=datetime.now()

            )

        

        # Calculate totals

        total_value = Decimal("0")

        total_cost = Decimal("0")

        

        # Get stock names mapping

        stock_names = {
            "005930": "Samsung Electronics",
            "000660": "SK Hynix",
            "035420": "NAVER",
            "005380": "Hyundai Motor",
            "051910": "LG Chem",
            "006400": "Samsung SDI",
            "035720": "Kakao",
            "068270": "Celltrion"
        }
        
        holdings_list = []
        for holding in holdings:
            holdings_list.append({
                "id": holding.id,
                "symbol": holding.symbol,
                "stock_name": stock_names.get(holding.symbol, holding.symbol),
                "quantity": holding.quantity,
                "average_price": holding.average_price,
                "current_price": holding.current_price,
                "updated_at": holding.updated_at
            })

        

        # Calculate overall profit/loss

        total_profit_loss = total_value - total_cost

        total_profit_loss_pct = float((total_profit_loss / total_cost * 100)) if total_cost > 0 else 0.0

        

        # Get most recent update time

        last_updated = max(h.updated_at for h in holdings) if holdings else datetime.now()

        

        response = {

            "total_holdings": len(holdings),

            "total_value": float(total_value),

            "total_cost": float(total_cost),

            "profit_loss": float(total_profit_loss),

            "profit_loss_percentage": total_profit_loss_pct,

            "holdings": holdings_list,

            "last_updated": last_updated.isoformat()

        }

        

        logger.info(

            f"Holdings summary retrieved: {len(holdings)} positions, "

            f"total_value={total_value}, P/L={total_profit_loss_pct:.2f}%"

        )

        return response

        

    except Exception as e:

        logger.error(f"Failed to retrieve account holdings: {e}", exc_info=True)

        raise HTTPException(

            status_code=500,

            detail=f"Failed to retrieve account holdings: {str(e)}"

        )





@router.post("/account/sync")

async def sync_account_holdings(

    db: Session = Depends(get_db)

):

    """

    Synchronize account holdings from brokerage API

    

    Fetches latest holdings data from the connected brokerage API

    and updates the local database. This is a manual sync endpoint.

    

    Note: Requires brokerage API to be configured and authenticated.

    

    Args:

        db: Database session

        

    Returns:

        Sync statistics (new, updated, removed holdings)

        

    Raises:

        HTTPException: If sync fails or API not configured

    """

    logger.info("Manual account sync requested")

    

    try:

        # Note: This requires AccountSyncService to be initialized with broker API

        # For now, return a message indicating manual configuration needed

        raise HTTPException(

            status_code=501,

            detail="Account sync requires brokerage API configuration. "

                   "Please configure your brokerage API credentials in the .env file "

                   "and restart the application with sync service enabled."

        )

        

        # TODO: Implement when broker API is configured

        # from services.korea_investment_api import KoreaInvestmentAPI

        # from config import settings

        # 

        # broker_api = KoreaInvestmentAPI(...)

        # broker_api.authenticate()

        # 

        # sync_service = AccountSyncService(broker_api)

        # stats = sync_service.sync_holdings(db)

        # 

        # return {

        #     "status": "success",

        #     "new_holdings": stats["new_holdings"],

        #     "updated_holdings": stats["updated_holdings"],

        #     "removed_holdings": stats["removed_holdings"],

        #     "timestamp": datetime.now()

        # }

        

    except HTTPException:

        raise

    except Exception as e:

        logger.error(f"Account sync failed: {e}", exc_info=True)

        raise HTTPException(

            status_code=500,

            detail=f"Account sync failed: {str(e)}"

        )

