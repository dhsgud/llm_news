"""
Test Task 23: Security Enhancement
Tests for API authentication, encryption, 2FA, and audit logging
"""

import pytest
import time
from decimal import Decimal

from services.security import (
    APIKeyManager,
    RateLimiter,
    EncryptionService,
    TwoFactorAuth,
    AuditLogger
)


class TestAPIKeyManager:
    """Test API key generation and validation"""
    
    def test_generate_api_key(self):
        """Test API key generation"""
        manager = APIKeyManager()
        
        api_key = manager.generate_api_key("user123", "test_key")
        
        assert api_key is not None
        assert len(api_key) > 20
    
    def test_validate_api_key(self):
        """Test API key validation"""
        manager = APIKeyManager()
        
        api_key = manager.generate_api_key("user123", "test_key")
        user_id = manager.validate_api_key(api_key)
        
        assert user_id == "user123"
    
    def test_invalid_api_key(self):
        """Test invalid API key"""
        manager = APIKeyManager()
        
        user_id = manager.validate_api_key("invalid_key")
        
        assert user_id is None
    
    def test_revoke_api_key(self):
        """Test API key revocation"""
        manager = APIKeyManager()
        
        api_key = manager.generate_api_key("user123", "test_key")
        
        # Revoke key
        success = manager.revoke_api_key(api_key)
        assert success is True
        
        # Try to validate revoked key
        user_id = manager.validate_api_key(api_key)
        assert user_id is None


class TestRateLimiter:
    """Test rate limiting functionality"""
    
    def test_rate_limit_allowed(self):
        """Test requests within limit"""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        
        # Make 5 requests
        for i in range(5):
            assert limiter.is_allowed("user123") is True
    
    def test_rate_limit_exceeded(self):
        """Test rate limit exceeded"""
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        
        # Make 3 requests (should succeed)
        for i in range(3):
            assert limiter.is_allowed("user123") is True
        
        # 4th request should fail
        assert limiter.is_allowed("user123") is False
    
    def test_rate_limit_window_reset(self):
        """Test rate limit window reset"""
        limiter = RateLimiter(max_requests=2, window_seconds=1)
        
        # Make 2 requests
        assert limiter.is_allowed("user123") is True
        assert limiter.is_allowed("user123") is True
        
        # 3rd request should fail
        assert limiter.is_allowed("user123") is False
        
        # Wait for window to reset
        time.sleep(1.1)
        
        # Should be allowed again
        assert limiter.is_allowed("user123") is True
    
    def test_get_remaining(self):
        """Test getting remaining requests"""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        
        assert limiter.get_remaining("user123") == 5
        
        limiter.is_allowed("user123")
        assert limiter.get_remaining("user123") == 4
        
        limiter.is_allowed("user123")
        assert limiter.get_remaining("user123") == 3


class TestEncryptionService:
    """Test encryption and decryption"""
    
    def test_encrypt_decrypt_string(self):
        """Test string encryption and decryption"""
        service = EncryptionService()
        
        original = "sensitive_api_key_12345"
        encrypted = service.encrypt(original)
        decrypted = service.decrypt(encrypted)
        
        assert encrypted != original
        assert decrypted == original
    
    def test_encrypt_decrypt_dict(self):
        """Test dictionary encryption and decryption"""
        service = EncryptionService()
        
        original = {
            "api_key": "key123",
            "api_secret": "secret456",
            "account": "12345678"
        }
        
        encrypted = service.encrypt_dict(original)
        decrypted = service.decrypt_dict(encrypted)
        
        assert encrypted != original
        assert decrypted == original
    
    def test_encryption_consistency(self):
        """Test that same data encrypts differently each time"""
        service = EncryptionService()
        
        data = "test_data"
        encrypted1 = service.encrypt(data)
        encrypted2 = service.encrypt(data)
        
        # Should be different due to random IV
        assert encrypted1 != encrypted2
        
        # But both should decrypt to same value
        assert service.decrypt(encrypted1) == data
        assert service.decrypt(encrypted2) == data


class TestTwoFactorAuth:
    """Test two-factor authentication"""
    
    def test_generate_secret(self):
        """Test 2FA secret generation"""
        tfa = TwoFactorAuth()
        
        secret = tfa.generate_secret("user123")
        
        assert secret is not None
        assert len(secret) == 32
    
    def test_provisioning_uri(self):
        """Test provisioning URI generation"""
        tfa = TwoFactorAuth()
        
        uri = tfa.get_provisioning_uri("user123", "Test App")
        
        assert uri.startswith("otpauth://totp/")
        assert "user123" in uri
        assert "Test%20App" in uri or "Test+App" in uri
    
    def test_verify_token(self):
        """Test token verification"""
        import pyotp
        
        tfa = TwoFactorAuth()
        secret = tfa.generate_secret("user123")
        
        # Generate valid token
        totp = pyotp.TOTP(secret)
        token = totp.now()
        
        # Verify token
        assert tfa.verify_token("user123", token) is True
    
    def test_invalid_token(self):
        """Test invalid token"""
        tfa = TwoFactorAuth()
        tfa.generate_secret("user123")
        
        # Try invalid token
        assert tfa.verify_token("user123", "000000") is False
    
    def test_is_enabled(self):
        """Test checking if 2FA is enabled"""
        tfa = TwoFactorAuth()
        
        assert tfa.is_enabled("user123") is False
        
        tfa.generate_secret("user123")
        
        assert tfa.is_enabled("user123") is True


class TestAuditLogger:
    """Test audit logging"""
    
    def test_log_trade(self):
        """Test trade logging"""
        logger = AuditLogger()
        
        # Should not raise exception
        logger.log_trade(
            user_id="user123",
            action="BUY",
            symbol="005930",
            quantity=10,
            price=70000.0,
            status="SUCCESS"
        )
    
    def test_log_auth(self):
        """Test authentication logging"""
        logger = AuditLogger()
        
        # Should not raise exception
        logger.log_auth(
            user_id="user123",
            action="login",
            success=True,
            ip_address="192.168.1.1"
        )
    
    def test_log_config_change(self):
        """Test configuration change logging"""
        logger = AuditLogger()
        
        # Should not raise exception
        logger.log_config_change(
            user_id="user123",
            config_type="max_investment",
            old_value=1000000,
            new_value=2000000
        )
    
    def test_log_security_event(self):
        """Test security event logging"""
        logger = AuditLogger()
        
        # Should not raise exception
        logger.log_security_event(
            event_type="SUSPICIOUS_ACTIVITY",
            severity="HIGH",
            details="Multiple failed login attempts",
            ip_address="192.168.1.1"
        )


def test_integration_api_key_and_rate_limit():
    """Test integration of API key and rate limiting"""
    manager = APIKeyManager()
    limiter = RateLimiter(max_requests=3, window_seconds=60)
    
    # Generate API key
    api_key = manager.generate_api_key("user123", "test")
    
    # Validate and check rate limit
    for i in range(3):
        user_id = manager.validate_api_key(api_key)
        assert user_id == "user123"
        assert limiter.is_allowed(user_id) is True
    
    # 4th request should be rate limited
    user_id = manager.validate_api_key(api_key)
    assert limiter.is_allowed(user_id) is False


def test_integration_encryption_and_2fa():
    """Test integration of encryption and 2FA"""
    import pyotp
    
    encryption = EncryptionService()
    tfa = TwoFactorAuth()
    
    # Generate and encrypt 2FA secret
    secret = tfa.generate_secret("user123")
    encrypted_secret = encryption.encrypt(secret)
    
    # Decrypt and verify
    decrypted_secret = encryption.decrypt(encrypted_secret)
    assert decrypted_secret == secret
    
    # Generate token with decrypted secret
    totp = pyotp.TOTP(decrypted_secret)
    token = totp.now()
    
    # Verify token
    assert tfa.verify_token("user123", token) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
