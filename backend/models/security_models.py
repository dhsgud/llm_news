"""
Database models for security features
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float
from sqlalchemy.sql import func
from app.database import Base


class APIKey(Base):
    """API Key storage"""
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    key_hash = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(String(100), index=True, nullable=False)
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used = Column(DateTime(timezone=True), nullable=True)


class TwoFactorSecret(Base):
    """Two-factor authentication secrets"""
    __tablename__ = "two_factor_secrets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), unique=True, index=True, nullable=False)
    secret = Column(String(32), nullable=False)  # Encrypted
    is_enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_verified = Column(DateTime(timezone=True), nullable=True)


class AuditLog(Base):
    """Audit log for security events"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    user_id = Column(String(100), index=True, nullable=True)
    event_type = Column(String(50), index=True, nullable=False)
    action = Column(String(100), nullable=False)
    success = Column(Boolean, nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    details = Column(Text, nullable=True)


class TradeAuditLog(Base):
    """Detailed audit log for trading activities"""
    __tablename__ = "trade_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    user_id = Column(String(100), index=True, nullable=False)
    trade_id = Column(Integer, nullable=True)
    action = Column(String(20), nullable=False)  # BUY, SELL, CANCEL
    symbol = Column(String(20), index=True, nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    status = Column(String(20), nullable=False)  # SUCCESS, FAILED, PENDING
    error_message = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    requires_2fa = Column(Boolean, default=False)
    two_fa_verified = Column(Boolean, default=False)


class EncryptedCredential(Base):
    """Encrypted storage for sensitive credentials"""
    __tablename__ = "encrypted_credentials"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), index=True, nullable=False)
    service_name = Column(String(100), nullable=False)  # e.g., "korea_investment"
    credential_type = Column(String(50), nullable=False)  # e.g., "api_key", "api_secret"
    encrypted_value = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
