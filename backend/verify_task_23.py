"""

Verification script for Task 23: Security Enhancement

Tests all security features in an integrated manner

"""



import sys

import os



# Add parent directory to path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))



from services.security import (

    api_key_manager,

    rate_limiter,

    encryption_service,

    two_factor_auth,

    audit_logger

)

from app.database import engine, SessionLocal

from models.security_models import (

    APIKey,

    TwoFactorSecret,

    AuditLog,

    TradeAuditLog,

    EncryptedCredential

)

from sqlalchemy import inspect

import pyotp





def verify_database_tables():

    """Verify that all security tables exist"""

    print("\n=== Verifying Database Tables ===")

    

    inspector = inspect(engine)

    tables = inspector.get_table_names()

    

    required_tables = [

        'api_keys',

        'two_factor_secrets',

        'audit_logs',

        'trade_audit_logs',

        'encrypted_credentials'

    ]

    

    for table in required_tables:

        if table in tables:

            print(f"??Table '{table}' exists")

        else:

            print(f"??Table '{table}' missing")

            return False

    

    return True





def verify_api_key_functionality():

    """Verify API key generation and validation"""

    print("\n=== Verifying API Key Functionality ===")

    

    try:

        # Generate API key

        api_key = api_key_manager.generate_api_key("test_user", "verification_test")

        print(f"??API key generated: {api_key[:20]}...")

        

        # Validate API key

        user_id = api_key_manager.validate_api_key(api_key)

        if user_id == "test_user":

            print(f"??API key validated successfully")

        else:

            print(f"??API key validation failed")

            return False

        

        # Test invalid key

        invalid_user = api_key_manager.validate_api_key("invalid_key")

        if invalid_user is None:

            print(f"??Invalid API key rejected")

        else:

            print(f"??Invalid API key accepted")

            return False

        

        # Revoke key

        success = api_key_manager.revoke_api_key(api_key)

        if success:

            print(f"??API key revoked")

        else:

            print(f"??API key revocation failed")

            return False

        

        # Try to use revoked key

        revoked_user = api_key_manager.validate_api_key(api_key)

        if revoked_user is None:

            print(f"??Revoked API key rejected")

        else:

            print(f"??Revoked API key still valid")

            return False

        

        return True

        

    except Exception as e:

        print(f"??API key test failed: {e}")

        return False





def verify_rate_limiting():

    """Verify rate limiting functionality"""

    print("\n=== Verifying Rate Limiting ===")

    

    try:

        limiter = RateLimiter(max_requests=3, window_seconds=60)

        

        # Make 3 requests

        for i in range(3):

            if not limiter.is_allowed("test_user"):

                print(f"??Request {i+1} blocked unexpectedly")

                return False

        print(f"??3 requests allowed")

        

        # 4th request should be blocked

        if limiter.is_allowed("test_user"):

            print(f"??4th request not blocked")

            return False

        print(f"??4th request blocked (rate limit working)")

        

        # Check remaining

        remaining = limiter.get_remaining("test_user")

        if remaining == 0:

            print(f"??Remaining requests: {remaining}")

        else:

            print(f"??Incorrect remaining count: {remaining}")

            return False

        

        return True

        

    except Exception as e:

        print(f"??Rate limiting test failed: {e}")

        return False





def verify_encryption():

    """Verify encryption functionality"""

    print("\n=== Verifying Encryption ===")

    

    try:

        # Test string encryption

        original = "sensitive_api_key_12345"

        encrypted = encryption_service.encrypt(original)

        decrypted = encryption_service.decrypt(encrypted)

        

        if encrypted != original:

            print(f"??String encrypted")

        else:

            print(f"??String not encrypted")

            return False

        

        if decrypted == original:

            print(f"??String decrypted correctly")

        else:

            print(f"??String decryption failed")

            return False

        

        # Test dictionary encryption

        original_dict = {

            "api_key": "key123",

            "api_secret": "secret456"

        }

        encrypted_dict = encryption_service.encrypt_dict(original_dict)

        decrypted_dict = encryption_service.decrypt_dict(encrypted_dict)

        

        if encrypted_dict != original_dict:

            print(f"??Dictionary encrypted")

        else:

            print(f"??Dictionary not encrypted")

            return False

        

        if decrypted_dict == original_dict:

            print(f"??Dictionary decrypted correctly")

        else:

            print(f"??Dictionary decryption failed")

            return False

        

        return True

        

    except Exception as e:

        print(f"??Encryption test failed: {e}")

        return False





def verify_two_factor_auth():

    """Verify 2FA functionality"""

    print("\n=== Verifying Two-Factor Authentication ===")

    

    try:

        # Generate secret

        secret = two_factor_auth.generate_secret("test_user")

        if len(secret) == 32:

            print(f"??2FA secret generated: {secret[:8]}...")

        else:

            print(f"??Invalid secret length")

            return False

        

        # Get provisioning URI

        uri = two_factor_auth.get_provisioning_uri("test_user", "Test App")

        if uri.startswith("otpauth://totp/"):

            print(f"??Provisioning URI generated")

        else:

            print(f"??Invalid provisioning URI")

            return False

        

        # Generate and verify token

        totp = pyotp.TOTP(secret)

        token = totp.now()

        

        if two_factor_auth.verify_token("test_user", token):

            print(f"??Valid token verified")

        else:

            print(f"??Valid token rejected")

            return False

        

        # Test invalid token

        if not two_factor_auth.verify_token("test_user", "000000"):

            print(f"??Invalid token rejected")

        else:

            print(f"??Invalid token accepted")

            return False

        

        # Check enabled status

        if two_factor_auth.is_enabled("test_user"):

            print(f"??2FA enabled status correct")

        else:

            print(f"??2FA enabled status incorrect")

            return False

        

        return True

        

    except Exception as e:

        print(f"??2FA test failed: {e}")

        return False





def verify_audit_logging():

    """Verify audit logging functionality"""

    print("\n=== Verifying Audit Logging ===")

    

    try:

        # Test trade logging

        audit_logger.log_trade(

            user_id="test_user",

            action="BUY",

            symbol="005930",

            quantity=10,

            price=70000.0,

            status="SUCCESS"

        )

        print(f"??Trade logged")

        

        # Test auth logging

        audit_logger.log_auth(

            user_id="test_user",

            action="login",

            success=True,

            ip_address="192.168.1.1"

        )

        print(f"??Auth event logged")

        

        # Test config change logging

        audit_logger.log_config_change(

            user_id="test_user",

            config_type="max_investment",

            old_value=1000000,

            new_value=2000000

        )

        print(f"??Config change logged")

        

        # Test security event logging

        audit_logger.log_security_event(

            event_type="TEST_EVENT",

            severity="INFO",

            details="Verification test"

        )

        print(f"??Security event logged")

        

        # Check if log file exists

        import os

        if os.path.exists("logs/audit.log"):

            print(f"??Audit log file created")

        else:

            print(f"??Audit log file not found")

            return False

        

        return True

        

    except Exception as e:

        print(f"??Audit logging test failed: {e}")

        return False





def verify_database_models():

    """Verify database models can be used"""

    print("\n=== Verifying Database Models ===")

    

    try:

        db = SessionLocal()

        

        # Test APIKey model

        api_key = APIKey(

            key_hash="test_hash_123",

            user_id="test_user",

            name="test_key",

            is_active=True

        )

        db.add(api_key)

        db.commit()

        print(f"??APIKey model working")

        

        # Test EncryptedCredential model

        cred = EncryptedCredential(

            user_id="test_user",

            service_name="test_service",

            credential_type="api_key",

            encrypted_value="encrypted_test_value"

        )

        db.add(cred)

        db.commit()

        print(f"??EncryptedCredential model working")

        

        # Test TradeAuditLog model

        trade_log = TradeAuditLog(

            user_id="test_user",

            action="BUY",

            symbol="005930",

            quantity=10,

            price=70000.0,

            total_amount=700000.0,

            status="SUCCESS"

        )

        db.add(trade_log)

        db.commit()

        print(f"??TradeAuditLog model working")

        

        # Clean up

        db.query(APIKey).filter(APIKey.key_hash == "test_hash_123").delete()

        db.query(EncryptedCredential).filter(EncryptedCredential.user_id == "test_user").delete()

        db.query(TradeAuditLog).filter(TradeAuditLog.user_id == "test_user").delete()

        db.commit()

        db.close()

        

        return True

        

    except Exception as e:

        print(f"??Database model test failed: {e}")

        return False





def main():

    """Run all verification tests"""

    print("=" * 60)

    print("Task 23: Security Enhancement Verification")

    print("=" * 60)

    

    results = []

    

    # Run all tests

    results.append(("Database Tables", verify_database_tables()))

    results.append(("API Key Functionality", verify_api_key_functionality()))

    results.append(("Rate Limiting", verify_rate_limiting()))

    results.append(("Encryption", verify_encryption()))

    results.append(("Two-Factor Auth", verify_two_factor_auth()))

    results.append(("Audit Logging", verify_audit_logging()))

    results.append(("Database Models", verify_database_models()))

    

    # Print summary

    print("\n" + "=" * 60)

    print("Verification Summary")

    print("=" * 60)

    

    all_passed = True

    for name, passed in results:

        status = "??PASS" if passed else "??FAIL"

        print(f"{status} - {name}")

        if not passed:

            all_passed = False

    

    print("=" * 60)

    

    if all_passed:

        print("\n✅ All security features verified successfully!")

        print("\nTask 23 is complete and ready for production use.")

        return 0

    else:

        print("\n⚠️  Some tests failed. Please review the output above.")

        return 1





if __name__ == "__main__":

    # Import RateLimiter for testing

    from services.security import RateLimiter

    

    sys.exit(main())

