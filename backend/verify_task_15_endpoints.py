"""

Quick verification script for Task 15 API endpoints



This script tests the three new stock-related endpoints to verify they work correctly.

Run this after starting the FastAPI server.

"""



import requests

import json

from datetime import datetime, timedelta

from decimal import Decimal



BASE_URL = "http://localhost:8000"





def print_section(title):

    """Print a section header"""

    print("\n" + "=" * 80)

    print(f"  {title}")

    print("=" * 80)





def test_stock_info():

    """Test GET /api/stocks/{symbol}"""

    print_section("Test 1: GET /api/stocks/{symbol}")

    

    symbol = "005930"  # Samsung Electronics

    url = f"{BASE_URL}/api/stocks/{symbol}?hours=24"

    

    print(f"\nRequest: GET {url}")

    

    try:

        response = requests.get(url)

        print(f"Status Code: {response.status_code}")

        

        if response.status_code == 200:

            data = response.json()

            print(f"\n??Success!")

            print(f"Symbol: {data['symbol']}")

            print(f"Current Price: {data.get('current_price', 'N/A')}")

            print(f"Volume: {data.get('volume', 'N/A')}")

            print(f"Open: {data.get('open_price', 'N/A')}")

            print(f"High: {data.get('high_price', 'N/A')}")

            print(f"Low: {data.get('low_price', 'N/A')}")

            print(f"Last Updated: {data.get('last_updated', 'N/A')}")

            print(f"Price History: {len(data.get('price_history', []))} data points")

        elif response.status_code == 404:

            print(f"\n⚠️  No data found for symbol {symbol}")

            print("This is expected if no price data has been collected yet.")

        else:

            print(f"\n??Error: {response.json()}")

    except requests.exceptions.ConnectionError:

        print("\n??Connection Error: Is the FastAPI server running?")

        print("Start it with: python backend/main.py")

    except Exception as e:

        print(f"\n??Error: {e}")





def test_stock_sentiment():

    """Test GET /api/stocks/{symbol}/sentiment"""

    print_section("Test 2: GET /api/stocks/{symbol}/sentiment")

    

    symbol = "005930"  # Samsung Electronics

    url = f"{BASE_URL}/api/stocks/{symbol}/sentiment?days=7"

    

    print(f"\nRequest: GET {url}")

    

    try:

        response = requests.get(url)

        print(f"Status Code: {response.status_code}")

        

        if response.status_code == 200:

            data = response.json()

            print(f"\n??Success!")

            print(f"Symbol: {data['symbol']}")

            print(f"Average Score: {data['average_score']:.2f}")

            print(f"Article Count: {data['article_count']}")

            print(f"Sentiment Distribution: {data['sentiment_distribution']}")

            print(f"Recommendation: {data['recommendation']}")

            print(f"Confidence: {data['confidence']}")

            print(f"Related News: {len(data.get('related_news', []))} articles")

            print(f"Last Analyzed: {data.get('last_analyzed', 'N/A')}")

        elif response.status_code == 404:

            print(f"\n⚠️  No sentiment data found for symbol {symbol}")

            print("This is expected if no news has been collected and analyzed yet.")

        else:

            print(f"\n??Error: {response.json()}")

    except requests.exceptions.ConnectionError:

        print("\n??Connection Error: Is the FastAPI server running?")

        print("Start it with: python backend/main.py")

    except Exception as e:

        print(f"\n??Error: {e}")





def test_account_holdings():

    """Test GET /api/account/holdings"""

    print_section("Test 3: GET /api/account/holdings")

    

    url = f"{BASE_URL}/api/account/holdings"

    

    print(f"\nRequest: GET {url}")

    

    try:

        response = requests.get(url)

        print(f"Status Code: {response.status_code}")

        

        if response.status_code == 200:

            data = response.json()

            print(f"\n??Success!")

            print(f"Total Holdings: {data['total_holdings']}")

            print(f"Total Value: {data['total_value']}")

            print(f"Total Cost: {data['total_cost']}")

            print(f"Profit/Loss: {data['profit_loss']} ({data['profit_loss_percentage']:.2f}%)")

            print(f"Last Updated: {data['last_updated']}")

            

            if data['holdings']:

                print(f"\nHoldings:")

                for holding in data['holdings']:

                    cost = float(holding['average_price']) * holding['quantity']

                    current = float(holding.get('current_price', holding['average_price'])) * holding['quantity']

                    pl = current - cost

                    pl_pct = (pl / cost * 100) if cost > 0 else 0

                    

                    print(f"  - {holding['symbol']}: {holding['quantity']} shares")

                    print(f"    Avg Price: {holding['average_price']}, Current: {holding.get('current_price', 'N/A')}")

                    print(f"    P/L: {pl:.2f} ({pl_pct:.2f}%)")

            else:

                print("\nNo holdings found.")

        else:

            print(f"\n??Error: {response.json()}")

    except requests.exceptions.ConnectionError:

        print("\n??Connection Error: Is the FastAPI server running?")

        print("Start it with: python backend/main.py")

    except Exception as e:

        print(f"\n??Error: {e}")





def test_account_sync():

    """Test POST /api/account/sync"""

    print_section("Test 4: POST /api/account/sync")

    

    url = f"{BASE_URL}/api/account/sync"

    

    print(f"\nRequest: POST {url}")

    

    try:

        response = requests.post(url)

        print(f"Status Code: {response.status_code}")

        

        if response.status_code == 501:

            print(f"\n??Expected response (Not Implemented)")

            print(f"Message: {response.json()['detail']}")

        else:

            print(f"\n⚠️  Unexpected status code: {response.status_code}")

            print(f"Response: {response.json()}")

    except requests.exceptions.ConnectionError:

        print("\n??Connection Error: Is the FastAPI server running?")

        print("Start it with: python backend/main.py")

    except Exception as e:

        print(f"\n??Error: {e}")





def test_api_docs():

    """Test API documentation endpoints"""

    print_section("Test 5: API Documentation")

    

    # Test OpenAPI schema

    url = f"{BASE_URL}/openapi.json"

    print(f"\nRequest: GET {url}")

    

    try:

        response = requests.get(url)

        print(f"Status Code: {response.status_code}")

        

        if response.status_code == 200:

            schema = response.json()

            paths = schema.get('paths', {})

            

            # Check for our new endpoints

            stock_endpoints = [

                "/api/stocks/{symbol}",

                "/api/stocks/{symbol}/sentiment",

                "/api/account/holdings",

                "/api/account/sync"

            ]

            

            print(f"\n??OpenAPI schema retrieved")

            print(f"\nChecking for new endpoints:")

            for endpoint in stock_endpoints:

                if endpoint in paths:

                    print(f"  ??{endpoint}")

                else:

                    print(f"  ??{endpoint} - NOT FOUND")

            

            print(f"\n📚 Interactive API docs available at:")

            print(f"  - Swagger UI: {BASE_URL}/docs")

            print(f"  - ReDoc: {BASE_URL}/redoc")

        else:

            print(f"\n??Error: {response.json()}")

    except requests.exceptions.ConnectionError:

        print("\n??Connection Error: Is the FastAPI server running?")

        print("Start it with: python backend/main.py")

    except Exception as e:

        print(f"\n??Error: {e}")





def main():

    """Run all tests"""

    print("\n" + "=" * 80)

    print("  Task 15 API Endpoints Verification")

    print("=" * 80)

    print("\nThis script will test the three new stock-related API endpoints.")

    print("Make sure the FastAPI server is running before proceeding.")

    print("\nTo start the server, run:")

    print("  python backend/main.py")

    print("\n" + "=" * 80)

    

    input("\nPress Enter to continue...")

    

    # Run all tests

    test_stock_info()

    test_stock_sentiment()

    test_account_holdings()

    test_account_sync()

    test_api_docs()

    

    # Summary

    print_section("Verification Complete")

    print("\n??All endpoint tests completed!")

    print("\nNext steps:")

    print("1. If any endpoints returned 404, populate data using:")

    print("   - StockDataCollector for price data")

    print("   - StockNewsFilter for sentiment data")

    print("   - AccountSyncService for holdings data")

    print("\n2. Visit the interactive API docs:")

    print(f"   {BASE_URL}/docs")

    print("\n3. Proceed to Task 16: 주식 대시보드 UI 구현")

    print()





if __name__ == "__main__":

    main()

