"""
Test Makcorps Hotel API Connection
Usage: python scripts/test_makcorps.py
"""
import os
import sys
import requests

# Try to load from Streamlit secrets
try:
    import streamlit as st
    API_KEY = st.secrets.get("MAKCORPS_API_KEY") or os.getenv("MAKCORPS_API_KEY")
except:
    API_KEY = os.getenv("MAKCORPS_API_KEY")

API_BASE_URL = "https://api.makcorps.com"

# Makkah city ID
MAKKAH_CITY_ID = "293993"

def test_makcorps_api():
    """Test Makcorps API connection and hotel search."""

    print(f"\n{'='*50}")
    print("Testing Makcorps Hotel API")
    print(f"{'='*50}")

    if not API_KEY:
        print("ERROR: MAKCORPS_API_KEY not set!")
        return False

    print(f"API Key: {API_KEY[:8]}...{API_KEY[-4:]}")
    print()

    # Test 1: Mapping API (get city ID)
    print("Test 1: Mapping API (City ID lookup)")
    print("-" * 40)

    try:
        url = f"{API_BASE_URL}/mapping"
        params = {"name": "Mecca", "api_key": API_KEY}

        response = requests.get(url, params=params, timeout=30)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data[:2] if isinstance(data, list) else data}")
            print("Mapping API: OK")
        elif response.status_code == 403:
            print("ERROR: Connection limit exceeded (403)")
            print("Possible: Too many concurrent requests or invalid key")
            return False
        elif response.status_code == 404:
            print("ERROR: Invalid API key or no data (404)")
            return False
        else:
            print(f"ERROR: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"ERROR: {e}")
        return False

    print()

    # Test 2: City Search API (hotel prices)
    print("Test 2: City Search API (Hotel Prices)")
    print("-" * 40)

    try:
        from datetime import datetime, timedelta

        check_in = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        check_out = (datetime.now() + timedelta(days=32)).strftime("%Y-%m-%d")

        url = f"{API_BASE_URL}/city"
        params = {
            "cityid": MAKKAH_CITY_ID,
            "pagination": "0",
            "cur": "SAR",
            "rooms": "1",
            "adults": "2",
            "checkin": check_in,
            "checkout": check_out,
            "api_key": API_KEY,
        }

        print(f"Search: Makkah, {check_in} to {check_out}")

        response = requests.get(url, params=params, timeout=30)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            if isinstance(data, list) and len(data) > 0:
                print(f"Hotels found: {len(data)}")

                # Show first hotel with price
                hotel = data[0]
                print(f"\nFirst hotel:")
                print(f"  Name: {hotel.get('name', 'N/A')}")
                print(f"  Vendor1: {hotel.get('vendor1', 'N/A')}")
                print(f"  Price1: {hotel.get('price1', 'N/A')}")
                print(f"  Vendor2: {hotel.get('vendor2', 'N/A')}")
                print(f"  Price2: {hotel.get('price2', 'N/A')}")

                # Check if prices exist
                has_prices = any(hotel.get(f'price{i}') for i in range(1, 5))
                if has_prices:
                    print("\nPrices: AVAILABLE")
                else:
                    print("\nWARNING: Hotels found but NO PRICES!")
                    print("This might be due to:")
                    print("  - Dates too far in future")
                    print("  - No availability for these dates")
                    print("  - API plan limitations")

                return True
            else:
                print("No hotels returned")
                print(f"Response: {data}")
                return False
        else:
            print(f"ERROR: {response.text[:300]}")
            return False

    except Exception as e:
        print(f"ERROR: {e}")
        return False


if __name__ == "__main__":
    success = test_makcorps_api()

    print(f"\n{'='*50}")
    if success:
        print("Makcorps API: CONNECTED")
    else:
        print("Makcorps API: FAILED")
        print("\nTroubleshooting:")
        print("1. Verify API key di Railway")
        print("2. Check Makcorps dashboard untuk usage/limits")
        print("3. Pastikan subscription aktif")
    print(f"{'='*50}\n")

    sys.exit(0 if success else 1)
