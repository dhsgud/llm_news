"""
Security Features Demo
Demonstrates how to use the security features in the Market Sentiment Analyzer
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.security import (
    api_key_manager,
    rate_limiter,
    encryption_service,
    two_factor_auth,
    audit_logger
)
import pyotp


def demo_api_key():
    """Demo: API Key Management"""
    print("\n" + "="*60)
    print("Demo 1: API Key Management")
    print("="*60)
    
    # Generate API key
    print("\n1. Generating API key...")
    api_key = api_key_manager.generate_api_key("demo_user", "demo_app")
    print(f"   Generated: {api_key[:30]}...")
    
    # Validate API key
    print("\n2. Validating API key...")
    user_id = api_key_manager.validate_api_key(api_key)
    print(f"   User ID: {user_id}")
    
    # Try invalid key
    print("\n3. Testing invalid key...")
    invalid_user = api_key_manager.validate_api_key("invalid_key")
    print(f"   Result: {invalid_user} (should be None)")
    
    # Revoke key
    print("\n4. Revoking API key...")
    api_key_manager.revoke_api_key(api_key)
    print("   Key revoked")
    
    # Try to use revoked key
    print("\n5. Testing revoked key...")
    revoked_user = api_key_manager.validate_api_key(api_key)
    print(f"   Result: {revoked_user} (should be None)")


def demo_rate_limiting():
    """Demo: Rate Limiting"""
    print("\n" + "="*60)
    print("Demo 2: Rate Limiting")
    print("="*60)
    
    limiter = rate_limiter
    user_id = "demo_user"
    
    print(f"\nRate limit: {limiter.max_requests} requests per {limiter.window_seconds} seconds")
    
    # Make requests
    print("\nMaking requests...")
    for i in range(limiter.max_requests + 2):
        allowed = limiter.is_allowed(user_id)
        remaining = limiter.get_remaining(user_id)
        status = "??Allowed" if allowed else "??Blocked"
        print(f"   Request {i+1}: {status} (Remaining: {remaining})")


def demo_encryption():
    """Demo: Encryption"""
    print("\n" + "="*60)
    print("Demo 3: Encryption")
    print("="*60)
    
    # Encrypt string
    print("\n1. String Encryption:")
    original = "my_secret_api_key_12345"
    print(f"   Original: {original}")
    
    encrypted = encryption_service.encrypt(original)
    print(f"   Encrypted: {encrypted[:50]}...")
    
    decrypted = encryption_service.decrypt(encrypted)
    print(f"   Decrypted: {decrypted}")
    
    # Encrypt dictionary
    print("\n2. Dictionary Encryption:")
    credentials = {
        "api_key": "key_12345",
        "api_secret": "secret_67890",
        "account": "1234567890"
    }
    print(f"   Original: {credentials}")
    
    encrypted_dict = encryption_service.encrypt_dict(credentials)
    print(f"   Encrypted: {list(encrypted_dict.keys())}")
    
    decrypted_dict = encryption_service.decrypt_dict(encrypted_dict)
    print(f"   Decrypted: {decrypted_dict}")


def demo_two_factor_auth():
    """Demo: Two-Factor Authentication"""
    print("\n" + "="*60)
    print("Demo 4: Two-Factor Authentication")
    print("="*60)
    
    user_id = "demo_user"
    
    # Generate secret
    print("\n1. Setting up 2FA...")
    secret = two_factor_auth.generate_secret(user_id)
    print(f"   Secret: {secret}")
    
    # Get provisioning URI
    uri = two_factor_auth.get_provisioning_uri(user_id, "Market Analyzer")
    print(f"   Provisioning URI: {uri[:60]}...")
    
    # Generate QR code URL
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={uri}"
    print(f"   QR Code URL: {qr_url[:60]}...")
    
    # Generate and verify token
    print("\n2. Generating and verifying token...")
    totp = pyotp.TOTP(secret)
    token = totp.now()
    print(f"   Current token: {token}")
    
    is_valid = two_factor_auth.verify_token(user_id, token)
    print(f"   Verification: {'??Valid' if is_valid else '??Invalid'}")
    
    # Test invalid token
    print("\n3. Testing invalid token...")
    is_valid = two_factor_auth.verify_token(user_id, "000000")
    print(f"   Verification: {'??Valid' if is_valid else '??Invalid (expected)'}")


def demo_audit_logging():
    """Demo: Audit Logging"""
    print("\n" + "="*60)
    print("Demo 5: Audit Logging")
    print("="*60)
    
    # Log trade
    print("\n1. Logging trade...")
    audit_logger.log_trade(
        user_id="demo_user",
        action="BUY",
        symbol="005930",
        quantity=10,
        price=70000.0,
        status="SUCCESS",
        ip_address="192.168.1.100"
    )
    print("   ??Trade logged")
    
    # Log authentication
    print("\n2. Logging authentication...")
    audit_logger.log_auth(
        user_id="demo_user",
        action="login",
        success=True,
        ip_address="192.168.1.100"
    )
    print("   ??Auth event logged")
    
    # Log config change
    print("\n3. Logging config change...")
    audit_logger.log_config_change(
        user_id="demo_user",
        config_type="max_investment",
        old_value=1000000,
        new_value=2000000
    )
    print("   ??Config change logged")
    
    # Log security event
    print("\n4. Logging security event...")
    audit_logger.log_security_event(
        event_type="DEMO_EVENT",
        severity="INFO",
        details="This is a demo security event",
        user_id="demo_user"
    )
    print("   ??Security event logged")
    
    print("\n   Check logs/audit.log for details")


def demo_secure_trading_flow():
    """Demo: Complete Secure Trading Flow"""
    print("\n" + "="*60)
    print("Demo 6: Complete Secure Trading Flow")
    print("="*60)
    
    user_id = "demo_user"
    
    # Step 1: Generate API key
    print("\n1. User generates API key...")
    api_key = api_key_manager.generate_api_key(user_id, "trading_app")
    print(f"   ??API key: {api_key[:30]}...")
    
    # Step 2: Setup 2FA
    print("\n2. User sets up 2FA...")
    secret = two_factor_auth.generate_secret(user_id)
    print(f"   ??2FA secret: {secret[:16]}...")
    
    # Step 3: Validate API key
    print("\n3. Validating API key for request...")
    validated_user = api_key_manager.validate_api_key(api_key)
    print(f"   ??User validated: {validated_user}")
    
    # Step 4: Check rate limit
    print("\n4. Checking rate limit...")
    allowed = rate_limiter.is_allowed(user_id)
    print(f"   ??Request allowed: {allowed}")
    
    # Step 5: Verify 2FA for high-value trade
    print("\n5. Verifying 2FA for high-value trade...")
    totp = pyotp.TOTP(secret)
    token = totp.now()
    is_valid = two_factor_auth.verify_token(user_id, token)
    print(f"   ??2FA verified: {is_valid}")
    
    # Step 6: Execute trade
    print("\n6. Executing trade...")
    if is_valid:
        audit_logger.log_trade(
            user_id=user_id,
            action="BUY",
            symbol="005930",
            quantity=100,
            price=70000.0,
            status="SUCCESS",
            two_fa_verified=True
        )
        print("   ??Trade executed and logged")
    
    # Step 7: Encrypt sensitive data
    print("\n7. Encrypting trade details for storage...")
    trade_data = {
        "symbol": "005930",
        "quantity": "100",
        "price": "70000"
    }
    encrypted_data = encryption_service.encrypt_dict(trade_data)
    print(f"   ??Data encrypted: {list(encrypted_data.keys())}")


def main():
    """Run all demos"""
    print("\n" + "="*60)
    print("Market Sentiment Analyzer - Security Features Demo")
    print("="*60)
    
    try:
        demo_api_key()
        demo_rate_limiting()
        demo_encryption()
        demo_two_factor_auth()
        demo_audit_logging()
        demo_secure_trading_flow()
        
        print("\n" + "="*60)
        print("All demos completed successfully!")
        print("="*60)
        print("\nNext steps:")
        print("1. Check logs/audit.log for audit trail")
        print("2. Review backend/TASK_23_SUMMARY.md for documentation")
        print("3. Run backend/verify_task_23.py for full verification")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n??Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
