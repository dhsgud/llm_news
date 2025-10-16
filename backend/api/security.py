"""
Security API endpoints for authentication and authorization
"""

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from pydantic import BaseModel
from typing import Optional
import logging

from services.security import (
    api_key_manager,
    rate_limiter,
    two_factor_auth,
    audit_logger
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/security", tags=["security"])


# Request/Response Models
class APIKeyRequest(BaseModel):
    user_id: str
    name: str = "default"


class APIKeyResponse(BaseModel):
    api_key: str
    user_id: str
    name: str
    message: str


class TwoFactorSetupResponse(BaseModel):
    secret: str
    provisioning_uri: str
    qr_code_url: str


class TwoFactorVerifyRequest(BaseModel):
    user_id: str
    token: str


class TwoFactorVerifyResponse(BaseModel):
    success: bool
    message: str


# Dependency for API key authentication
async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """Verify API key from header"""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    user_id = api_key_manager.validate_api_key(x_api_key)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return user_id


# Dependency for rate limiting
async def check_rate_limit(request: Request):
    """Check rate limit for request"""
    # Use IP address as identifier
    client_ip = request.client.host
    
    if not rate_limiter.is_allowed(client_ip):
        remaining = rate_limiter.get_remaining(client_ip)
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Try again later. Remaining: {remaining}"
        )


@router.post("/api-keys", response_model=APIKeyResponse)
async def generate_api_key(request: APIKeyRequest):
    """
    Generate a new API key for a user
    
    In production, this should require admin authentication
    """
    try:
        api_key = api_key_manager.generate_api_key(
            user_id=request.user_id,
            name=request.name
        )
        
        audit_logger.log_auth(
            user_id=request.user_id,
            action="api_key_generated",
            success=True,
            name=request.name
        )
        
        return APIKeyResponse(
            api_key=api_key,
            user_id=request.user_id,
            name=request.name,
            message="API key generated successfully. Store it securely!"
        )
    except Exception as e:
        logger.error(f"Failed to generate API key: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate API key")


@router.delete("/api-keys")
async def revoke_api_key(
    x_api_key: str = Header(...),
    user_id: str = Depends(verify_api_key)
):
    """Revoke an API key"""
    try:
        success = api_key_manager.revoke_api_key(x_api_key)
        
        audit_logger.log_auth(
            user_id=user_id,
            action="api_key_revoked",
            success=success
        )
        
        if success:
            return {"message": "API key revoked successfully"}
        else:
            raise HTTPException(status_code=404, detail="API key not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to revoke API key: {e}")
        raise HTTPException(status_code=500, detail="Failed to revoke API key")


@router.post("/2fa/setup", response_model=TwoFactorSetupResponse)
async def setup_two_factor(
    user_id: str,
    api_user_id: str = Depends(verify_api_key)
):
    """
    Setup two-factor authentication for a user
    Returns secret and provisioning URI for QR code
    """
    # Verify user can only setup 2FA for themselves
    if user_id != api_user_id:
        raise HTTPException(status_code=403, detail="Cannot setup 2FA for other users")
    
    try:
        secret = two_factor_auth.generate_secret(user_id)
        provisioning_uri = two_factor_auth.get_provisioning_uri(user_id)
        
        # Generate QR code URL (using a QR code service)
        qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={provisioning_uri}"
        
        audit_logger.log_auth(
            user_id=user_id,
            action="2fa_setup",
            success=True
        )
        
        return TwoFactorSetupResponse(
            secret=secret,
            provisioning_uri=provisioning_uri,
            qr_code_url=qr_code_url
        )
    except Exception as e:
        logger.error(f"Failed to setup 2FA: {e}")
        raise HTTPException(status_code=500, detail="Failed to setup 2FA")


@router.post("/2fa/verify", response_model=TwoFactorVerifyResponse)
async def verify_two_factor(request: TwoFactorVerifyRequest):
    """Verify two-factor authentication token"""
    try:
        is_valid = two_factor_auth.verify_token(request.user_id, request.token)
        
        audit_logger.log_auth(
            user_id=request.user_id,
            action="2fa_verify",
            success=is_valid
        )
        
        if is_valid:
            return TwoFactorVerifyResponse(
                success=True,
                message="2FA verification successful"
            )
        else:
            return TwoFactorVerifyResponse(
                success=False,
                message="Invalid 2FA token"
            )
    except Exception as e:
        logger.error(f"Failed to verify 2FA: {e}")
        raise HTTPException(status_code=500, detail="Failed to verify 2FA")


@router.get("/2fa/status")
async def get_2fa_status(user_id: str = Depends(verify_api_key)):
    """Check if 2FA is enabled for user"""
    is_enabled = two_factor_auth.is_enabled(user_id)
    return {
        "user_id": user_id,
        "2fa_enabled": is_enabled
    }


@router.get("/rate-limit/status")
async def get_rate_limit_status(
    request: Request,
    user_id: str = Depends(verify_api_key)
):
    """Get current rate limit status"""
    client_ip = request.client.host
    remaining = rate_limiter.get_remaining(client_ip)
    
    return {
        "user_id": user_id,
        "remaining_requests": remaining,
        "max_requests": rate_limiter.max_requests,
        "window_seconds": rate_limiter.window_seconds
    }
