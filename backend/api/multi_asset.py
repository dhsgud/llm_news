"""
Multi-Asset API endpoints
Supports stocks, cryptocurrencies, and forex
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

try:
    from app.database import get_db
    from models.asset_models import AssetType
    from models.asset_schemas import (
        AssetCreate, AssetResponse, AssetDetailResponse,
        AssetPriceResponse, AssetSentimentResponse,
        PortfolioSummary
    )
    from services.multi_asset_service import MultiAssetService
    from config import settings
except ImportError:
    from app.database import get_db
    from models.asset_models import AssetType
    from models.asset_schemas import (
        AssetCreate, AssetResponse, AssetDetailResponse,
        AssetPriceResponse, AssetSentimentResponse,
        PortfolioSummary
    )
    from services.multi_asset_service import MultiAssetService
    from config import settings

router = APIRouter(prefix="/api/assets", tags=["Multi-Asset"])


def get_asset_service(db: Session = Depends(get_db)) -> MultiAssetService:
    """Dependency for asset service"""
    forex_api_key = getattr(settings, 'FOREX_API_KEY', None)
    return MultiAssetService(db, forex_api_key=forex_api_key)


@router.post("/", response_model=AssetResponse)
def create_asset(
    asset: AssetCreate,
    service: MultiAssetService = Depends(get_asset_service)
):
    """
    Add a new asset to track
    
    - **symbol**: Asset symbol (e.g., BTC, EUR/USD)
    - **name**: Asset name
    - **asset_type**: Type of asset (stock, crypto, forex)
    - **exchange**: Exchange name (optional)
    - **base_currency**: Base currency for forex (optional)
    - **quote_currency**: Quote currency for forex (optional)
    """
    try:
        existing = service.get_asset(asset.symbol, asset.asset_type)
        if existing:
            raise HTTPException(status_code=400, detail="Asset already exists")
        
        new_asset = service.add_asset(
            symbol=asset.symbol,
            name=asset.name,
            asset_type=asset.asset_type,
            exchange=asset.exchange,
            base_currency=asset.base_currency,
            quote_currency=asset.quote_currency
        )
        return new_asset
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[AssetResponse])
def list_assets(
    asset_type: Optional[AssetType] = Query(None, description="Filter by asset type"),
    service: MultiAssetService = Depends(get_asset_service)
):
    """
    List all tracked assets
    
    - **asset_type**: Optional filter by asset type
    """
    try:
        assets = service.list_assets(asset_type=asset_type)
        return assets
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}", response_model=AssetDetailResponse)
def get_asset_detail(
    symbol: str,
    asset_type: Optional[AssetType] = Query(None, description="Asset type for disambiguation"),
    service: MultiAssetService = Depends(get_asset_service)
):
    """
    Get detailed information about an asset
    
    - **symbol**: Asset symbol
    - **asset_type**: Optional asset type if symbol is ambiguous
    """
    try:
        asset = service.get_asset(symbol, asset_type=asset_type)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        latest_price = service.get_latest_price(asset.id)
        
        # Calculate 24h change
        price_change_24h = None
        price_change_percent_24h = None
        if latest_price:
            history = service.get_price_history(asset.id, days=1)
            if len(history) > 1:
                old_price = history[0].close_price
                new_price = latest_price.close_price
                price_change_24h = new_price - old_price
                price_change_percent_24h = (price_change_24h / old_price * 100) if old_price > 0 else 0
        
        return AssetDetailResponse(
            **asset.__dict__,
            latest_price=latest_price,
            latest_sentiment=None,  # TODO: Implement sentiment for crypto/forex
            price_change_24h=price_change_24h,
            price_change_percent_24h=price_change_percent_24h
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}/prices", response_model=List[AssetPriceResponse])
def get_price_history(
    symbol: str,
    days: int = Query(7, ge=1, le=365, description="Number of days of history"),
    asset_type: Optional[AssetType] = Query(None),
    service: MultiAssetService = Depends(get_asset_service)
):
    """
    Get price history for an asset
    
    - **symbol**: Asset symbol
    - **days**: Number of days of historical data (1-365)
    - **asset_type**: Optional asset type
    """
    try:
        asset = service.get_asset(symbol, asset_type=asset_type)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        prices = service.get_price_history(asset.id, days=days)
        return prices
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/prices/update")
def update_all_prices(
    service: MultiAssetService = Depends(get_asset_service)
):
    """
    Update prices for all tracked assets
    
    Returns statistics about the update operation
    """
    try:
        stats = service.update_all_prices()
        return {
            "success": True,
            "message": "Price update completed",
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/portfolio/summary", response_model=PortfolioSummary)
def get_portfolio_summary(
    service: MultiAssetService = Depends(get_asset_service)
):
    """
    Get portfolio summary across all asset types
    
    Returns total value, profit/loss, and breakdown by asset type
    """
    try:
        summary = service.get_portfolio_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crypto/search")
def search_crypto(
    query: str = Query(..., min_length=1, description="Search query"),
    service: MultiAssetService = Depends(get_asset_service)
):
    """
    Search for cryptocurrencies by name or symbol
    
    - **query**: Search term
    """
    try:
        results = service.search_crypto(query)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/forex/currencies")
def get_forex_currencies(
    service: MultiAssetService = Depends(get_asset_service)
):
    """
    Get list of supported forex currencies
    """
    try:
        currencies = service.get_supported_currencies()
        return {"currencies": currencies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
