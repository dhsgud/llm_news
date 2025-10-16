#!/usr/bin/env python
"""
Brokerage API Integration Test Runner

This script provides an easy way to run brokerage API integration tests
with different configurations.

Usage:
    python run_brokerage_tests.py --mock-only          # Run only mock tests
    python run_brokerage_tests.py --integration-only   # Run only real API tests
    python run_brokerage_tests.py --all                # Run all tests
    python run_brokerage_tests.py --check-credentials  # Check if credentials are configured
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path
from dotenv import load_dotenv


def setup_environment():
    """Setup Python path and load environment variables"""
    # Get project root (two levels up from this script)
    project_root = Path(__file__).parent.parent.parent
    
    # Add project root to Python path
    sys.path.insert(0, str(project_root))
    os.environ['PYTHONPATH'] = str(project_root)
    
    # Load environment variables
    env_file = project_root / 'backend' / '.env'
    if env_file.exists():
        load_dotenv(env_file)
        return True
    return False


def check_credentials():
    """Check if real API credentials are configured"""
    app_key = os.getenv('KOREA_INVESTMENT_APP_KEY', '')
    app_secret = os.getenv('KOREA_INVESTMENT_APP_SECRET', '')
    account_number = os.getenv('KOREA_INVESTMENT_ACCOUNT_NUMBER', '')
    
    has_credentials = bool(app_key and app_secret and account_number)
    
    print("\n" + "="*70)
    print("BROKERAGE API CREDENTIALS CHECK")
    print("="*70)
    
    if has_credentials:
        print("??Credentials found in environment")
        print(f"  - App Key: {app_key[:10]}..." if len(app_key) > 10 else f"  - App Key: {app_key}")
        print(f"  - App Secret: {app_secret[:10]}..." if len(app_secret) > 10 else f"  - App Secret: {app_secret}")
        print(f"  - Account Number: {account_number}")
        print(f"  - Virtual Trading: {os.getenv('USE_VIRTUAL_TRADING', 'true')}")
        print("\n??Real API integration tests can be run")
    else:
        print("??Credentials NOT found in environment")
        print("\nMissing:")
        if not app_key:
            print("  - KOREA_INVESTMENT_APP_KEY")
        if not app_secret:
            print("  - KOREA_INVESTMENT_APP_SECRET")
        if not account_number:
            print("  - KOREA_INVESTMENT_ACCOUNT_NUMBER")
        print("\n??Real API integration tests will be skipped")
        print("\nTo configure credentials, add them to backend/.env file:")
        print("  KOREA_INVESTMENT_APP_KEY=your_app_key_here")
        print("  KOREA_INVESTMENT_APP_SECRET=your_app_secret_here")
        print("  KOREA_INVESTMENT_ACCOUNT_NUMBER=12345678")
        print("  USE_VIRTUAL_TRADING=true")
    
    print("="*70 + "\n")
    return has_credentials


def run_tests(test_type='mock'):
    """
    Run brokerage API integration tests
    
    Args:
        test_type: 'mock', 'integration', or 'all'
    """
    # Setup environment
    env_loaded = setup_environment()
    
    if not env_loaded:
        print("Warning: .env file not found. Using system environment variables.")
    
    # Determine pytest markers
    if test_type == 'mock':
        markers = '-m "not integration"'
        description = "Mock API Integration Tests"
    elif test_type == 'integration':
        markers = '-m integration'
        description = "Real API Integration Tests"
    else:  # all
        markers = ''
        description = "All Integration Tests"
    
    # Build pytest command
    test_file = Path(__file__).parent / 'test_brokerage_integration.py'
    cmd = f'python -m pytest "{test_file}" -v {markers} --tb=short'
    
    print("\n" + "="*70)
    print(f"RUNNING: {description}")
    print("="*70)
    print(f"Command: {cmd}")
    print("="*70 + "\n")
    
    # Run tests
    result = subprocess.run(cmd, shell=True)
    
    return result.returncode


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Run brokerage API integration tests',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_brokerage_tests.py --mock-only
      Run only mock tests (no credentials required)
  
  python run_brokerage_tests.py --integration-only
      Run only real API tests (requires credentials)
  
  python run_brokerage_tests.py --all
      Run all tests (mock + real API)
  
  python run_brokerage_tests.py --check-credentials
      Check if API credentials are configured
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--mock-only',
        action='store_true',
        help='Run only mock API tests (no credentials required)'
    )
    group.add_argument(
        '--integration-only',
        action='store_true',
        help='Run only real API integration tests (requires credentials)'
    )
    group.add_argument(
        '--all',
        action='store_true',
        help='Run all tests (mock + real API)'
    )
    group.add_argument(
        '--check-credentials',
        action='store_true',
        help='Check if API credentials are configured'
    )
    
    args = parser.parse_args()
    
    # Setup environment first
    setup_environment()
    
    # Handle check credentials
    if args.check_credentials:
        check_credentials()
        return 0
    
    # Determine test type
    if args.mock_only:
        test_type = 'mock'
    elif args.integration_only:
        test_type = 'integration'
        # Check credentials before running
        if not check_credentials():
            print("\n??Warning: Credentials not found. Tests will be skipped.\n")
    else:  # all
        test_type = 'all'
        check_credentials()
    
    # Run tests
    exit_code = run_tests(test_type)
    
    # Print summary
    print("\n" + "="*70)
    if exit_code == 0:
        print("??ALL TESTS PASSED")
    else:
        print("??SOME TESTS FAILED")
    print("="*70 + "\n")
    
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
