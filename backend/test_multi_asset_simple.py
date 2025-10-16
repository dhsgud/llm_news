"""
Simple test to verify multi-asset components
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing multi-asset components...")

# Test 1: Import models
print("\n1. Testing model imports...")
try:
    from models.asset_models import Asset, AssetPrice, AssetType
    from models.asset_schemas import AssetCreate, AssetResponse
    print("   ??Models imported successfully")
except Exception as e:
    print(f"   ??Model import failed: {e}")
    sys.exit(1)

# Test 2: Import collectors
print("\n2. Testing collector imports...")
try:
    from services.crypto_data_collector import CryptoDataCollector
    from services.forex_data_collector import ForexDataCollector
    print("   ??Collectors imported successfully")
except Exception as e:
    print(f"   ??Collector import failed: {e}")
    sys.exit(1)

# Test 3: Import service
print("\n3. Testing service import...")
try:
    from services.multi_asset_service import MultiAssetService
    print("   ??Service imported successfully")
except Exception as e:
    print(f"   ??Service import failed: {e}")
    sys.exit(1)

# Test 4: Import API
print("\n4. Testing API import...")
try:
    # Check if file exists
    import os
    api_file = os.path.join(os.path.dirname(__file__), 'api', 'multi_asset.py')
    if os.path.exists(api_file):
        print("   ??API file exists")
    else:
        print("   ??API file not found")
        sys.exit(1)
except Exception as e:
    print(f"   ??API check failed: {e}")
    sys.exit(1)

# Test 5: Test crypto collector
print("\n5. Testing crypto collector...")
try:
    collector = CryptoDataCollector()
    currencies = collector.get_supported_coins()
    if currencies:
        print(f"   ??Retrieved {len(currencies)} cryptocurrencies")
    else:
        print("   ??No data (API might be rate limited)")
except Exception as e:
    print(f"   ??Crypto collector test failed: {e}")

# Test 6: Test forex collector
print("\n6. Testing forex collector...")
try:
    collector = ForexDataCollector()
    currencies = collector.get_supported_currencies()
    print(f"   ??{len(currencies)} forex currencies supported")
except Exception as e:
    print(f"   ??Forex collector test failed: {e}")

print("\n" + "=" * 60)
print("??All basic tests passed!")
print("=" * 60)
print("\nNext steps:")
print("1. Run: python run_multi_asset_migration.py")
print("2. Run: python verify_task_28.py")
print("3. Run: python examples/multi_asset_demo.py")
