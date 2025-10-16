"""
Security services for authentication, encryption, and audit logging
"""

import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import pyotp
import logging

logger = logging.getLogger(__name__)


class APIKeyManager:
    """Manages API key generation, validation, and storage"""
    
    def __init__(self):
        self._api_keys: Dict[str, Dict[str, Any]] = {}
    
    def generate_api_key(self, user_id: str, name: str = "default") -> str:
        """Generate a new API key for a user"""
        # Generate secure random key
        key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        # Store key metadata
        self._api_keys[key_hash] = {
            "user_id": user_id,
            "name": name,
            "created_at": datetime.utcnow(),
            "last_used": None,
            "is_active": True
        }
        
        logger.info(f"Generated API key for user {user_id}: {name}")
        return key
    
    def validate_api_key(self, api_key: str) -> Optional[str]:
        """Validate API key and return user_id if valid"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        if key_hash not in self._api_keys:
            logger.warning(f"Invalid API key attempt: {key_hash[:8]}...")
            return None
        
        key_data = self._api_keys[key_hash]
        
        if not key_data["is_active"]:
            logger.warning(f"Inactive API key used: {key_hash[:8]}...")
            return None
        
        # Update last used timestamp
        key_data["last_used"] = datetime.utcnow()
        
        return key_data["user_id"]
    
    def revoke_api_key(self, api_key: str) -> bool:
        """Revoke an API key"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        if key_hash in self._api_keys:
            self._api_keys[key_hash]["is_active"] = False
            logger.info(f"Revoked API key: {key_hash[:8]}...")
            return True
        
        return False


class RateLimiter:
    """Rate limiting for API endpoints"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, list] = {}
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed for given identifier"""
        now = time.time()
        
        # Initialize or get request history
        if identifier not in self._requests:
            self._requests[identifier] = []
        
        # Remove old requests outside the window
        self._requests[identifier] = [
            req_time for req_time in self._requests[identifier]
            if now - req_time < self.window_seconds
        ]
        
        # Check if limit exceeded
        if len(self._requests[identifier]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for {identifier}")
            return False
        
        # Add current request
        self._requests[identifier].append(now)
        return True
    
    def get_remaining(self, identifier: str) -> int:
        """Get remaining requests for identifier"""
        now = time.time()
        
        if identifier not in self._requests:
            return self.max_requests
        
        # Count recent requests
        recent_requests = [
            req_time for req_time in self._requests[identifier]
            if now - req_time < self.window_seconds
        ]
        
        return max(0, self.max_requests - len(recent_requests))
    
    def reset(self, identifier: str):
        """Reset rate limit for identifier"""
        if identifier in self._requests:
            del self._requests[identifier]


class EncryptionService:
    """Service for encrypting and decrypting sensitive data"""
    
    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize encryption service
        
        Args:
            master_key: Master encryption key (base64 encoded)
                       If None, generates a new key
        """
        if master_key:
            self.key = master_key.encode()
        else:
            # Generate new key from password
            self.key = self._generate_key()
        
        self.cipher = Fernet(self.key)
    
    def _generate_key(self, password: str = None) -> bytes:
        """Generate encryption key from password"""
        if password is None:
            # Generate random key
            return Fernet.generate_key()
        
        # Derive key from password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'market_analyzer_salt',  # In production, use random salt
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data"""
        try:
            encrypted = self.cipher.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data"""
        try:
            decoded = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.cipher.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    def encrypt_dict(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Encrypt dictionary values"""
        return {
            key: self.encrypt(str(value))
            for key, value in data.items()
        }
    
    def decrypt_dict(self, encrypted_data: Dict[str, str]) -> Dict[str, str]:
        """Decrypt dictionary values"""
        return {
            key: self.decrypt(value)
            for key, value in encrypted_data.items()
        }


class TwoFactorAuth:
    """Two-factor authentication using TOTP"""
    
    def __init__(self):
        self._secrets: Dict[str, str] = {}
    
    def generate_secret(self, user_id: str) -> str:
        """Generate TOTP secret for user"""
        secret = pyotp.random_base32()
        self._secrets[user_id] = secret
        logger.info(f"Generated 2FA secret for user {user_id}")
        return secret
    
    def get_provisioning_uri(self, user_id: str, issuer: str = "Market Analyzer") -> str:
        """Get provisioning URI for QR code generation"""
        if user_id not in self._secrets:
            self.generate_secret(user_id)
        
        totp = pyotp.TOTP(self._secrets[user_id])
        return totp.provisioning_uri(name=user_id, issuer_name=issuer)
    
    def verify_token(self, user_id: str, token: str) -> bool:
        """Verify TOTP token"""
        if user_id not in self._secrets:
            logger.warning(f"No 2FA secret found for user {user_id}")
            return False
        
        totp = pyotp.TOTP(self._secrets[user_id])
        is_valid = totp.verify(token, valid_window=1)
        
        if is_valid:
            logger.info(f"2FA verification successful for user {user_id}")
        else:
            logger.warning(f"2FA verification failed for user {user_id}")
        
        return is_valid
    
    def is_enabled(self, user_id: str) -> bool:
        """Check if 2FA is enabled for user"""
        return user_id in self._secrets


class AuditLogger:
    """Audit logging for security-sensitive operations"""
    
    def __init__(self):
        self.logger = logging.getLogger("audit")
        
        # Create audit log handler
        import os
        os.makedirs("logs", exist_ok=True)
        
        from logging.handlers import RotatingFileHandler
        handler = RotatingFileHandler(
            "logs/audit.log",
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_trade(self, user_id: str, action: str, symbol: str, 
                  quantity: int, price: float, **kwargs):
        """Log trading activity"""
        self.logger.info(
            f"TRADE | user={user_id} | action={action} | "
            f"symbol={symbol} | quantity={quantity} | price={price} | "
            f"extra={kwargs}"
        )
    
    def log_auth(self, user_id: str, action: str, success: bool, **kwargs):
        """Log authentication events"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(
            f"AUTH | user={user_id} | action={action} | "
            f"status={status} | extra={kwargs}"
        )
    
    def log_config_change(self, user_id: str, config_type: str, 
                         old_value: Any, new_value: Any):
        """Log configuration changes"""
        self.logger.info(
            f"CONFIG | user={user_id} | type={config_type} | "
            f"old={old_value} | new={new_value}"
        )
    
    def log_security_event(self, event_type: str, severity: str, 
                          details: str, **kwargs):
        """Log security events"""
        self.logger.warning(
            f"SECURITY | type={event_type} | severity={severity} | "
            f"details={details} | extra={kwargs}"
        )


# Global instances
api_key_manager = APIKeyManager()
rate_limiter = RateLimiter(max_requests=100, window_seconds=60)
encryption_service = EncryptionService()
two_factor_auth = TwoFactorAuth()
audit_logger = AuditLogger()
