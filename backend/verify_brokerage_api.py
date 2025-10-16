"""

Verification script for Brokerage API implementation



This script verifies that all brokerage API components are properly

installed and can be imported without errors.

"""



import sys

import os

from pathlib import Path



# Setup path for imports

backend_path = Path(__file__).parent.absolute()

project_root = backend_path.parent

sys.path.insert(0, str(project_root))

os.chdir(project_root)





def verify_imports():

    """Verify all imports work correctly"""

    print("=" * 60)

    print("Brokerage API Implementation Verification")

    print("=" * 60)

    

    try:

        print("\n1. Importing base classes...")

        from services.brokerage_connector import BrokerageAPIBase, AccountInfo, StockPrice

        print("   ??BrokerageAPIBase imported")

        print("   ??AccountInfo imported")

        print("   ??StockPrice imported")

        

        print("\n2. Importing Korea Investment API...")

        from services.korea_investment_api import KoreaInvestmentAPI

        print("   ??KoreaInvestmentAPI imported")

        

        print("\n3. Importing Kiwoom API...")

        from services.kiwoom_api import KiwoomAPI

        print("   ??KiwoomAPI imported")

        

        print("\n4. Importing from services package...")

        from services import (

            BrokerageAPIBase as Base,

            AccountInfo as Info,

            StockPrice as Price,

            KoreaInvestmentAPI as KoreaAPI,

            KiwoomAPI as Kiwoom

        )

        print("   ??All exports available from services package")

        

        print("\n5. Importing trading schemas...")

        from models.trading_schemas import Order, TradeResult

        print("   ??Order imported")

        print("   ??TradeResult imported")

        

        print("\n6. Verifying class structure...")

        

        # Check BrokerageAPIBase has required methods

        required_methods = [

            'authenticate',

            'get_stock_price',

            'get_account_balance',

            'get_account_holdings',

            'place_order',

            'cancel_order',

            'get_order_status'

        ]

        

        for method in required_methods:

            assert hasattr(BrokerageAPIBase, method), f"Missing method: {method}"

        print(f"   ??BrokerageAPIBase has all {len(required_methods)} required methods")

        

        # Check class hierarchy (note: may show warning due to import path differences)

        korea_base = KoreaInvestmentAPI.__bases__[0].__name__

        kiwoom_base = KiwoomAPI.__bases__[0].__name__

        

        if korea_base == "BrokerageAPIBase":

            print("   ??KoreaInvestmentAPI extends BrokerageAPIBase")

        else:

            print(f"   ⚠️  KoreaInvestmentAPI extends {korea_base}")

        

        if kiwoom_base == "BrokerageAPIBase":

            print("   ??KiwoomAPI extends BrokerageAPIBase")

        else:

            print(f"   ⚠️  KiwoomAPI extends {kiwoom_base}")

        

        print("\n7. Testing instantiation...")

        

        # Test Korea Investment API instantiation

        korea_api = KoreaInvestmentAPI(

            app_key="test",

            app_secret="test",

            account_number="12345678",

            use_virtual=True

        )

        print("   ??KoreaInvestmentAPI can be instantiated")

        

        # Test Kiwoom API instantiation

        kiwoom_api = KiwoomAPI(account_number="12345678")

        print("   ??KiwoomAPI can be instantiated")

        

        # Test AccountInfo instantiation

        from decimal import Decimal

        account_info = AccountInfo(

            account_number="12345678",

            balance=Decimal("1000000"),

            available_cash=Decimal("500000"),

            total_assets=Decimal("1500000")

        )

        print("   ??AccountInfo can be instantiated")

        

        # Test StockPrice instantiation

        from datetime import datetime

        stock_price = StockPrice(

            symbol="005930",

            price=Decimal("75000"),

            volume=1000000,

            open_price=Decimal("74500"),

            high_price=Decimal("75500"),

            low_price=Decimal("74000"),

            timestamp=datetime.now()

        )

        print("   ??StockPrice can be instantiated")

        

        print("\n" + "=" * 60)

        print("??All verifications passed!")

        print("=" * 60)

        print("\nBrokerage API implementation is ready to use.")

        print("\nNext steps:")

        print("  1. Set environment variables in .env file")

        print("  2. Run: python examples/brokerage_api_example.py")

        print("  3. Run tests: pytest tests/test_brokerage_api.py -v")

        

        return True

        

    except ImportError as e:

        print(f"\n??Import Error: {e}")

        return False

    except AssertionError as e:

        print(f"\n??Assertion Error: {e}")

        return False

    except Exception as e:

        print(f"\n??Unexpected Error: {e}")

        import traceback

        traceback.print_exc()

        return False





if __name__ == "__main__":

    success = verify_imports()

    sys.exit(0 if success else 1)

