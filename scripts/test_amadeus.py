"""
Test Amadeus API Connection
Usage: python scripts/test_amadeus.py
"""
import os
import sys
import requests

# Try to load from Streamlit secrets
try:
    import streamlit as st
    API_KEY = st.secrets.get("AMADEUS_API_KEY") or os.getenv("AMADEUS_API_KEY")
    API_SECRET = st.secrets.get("AMADEUS_API_SECRET") or os.getenv("AMADEUS_API_SECRET")
except:
    API_KEY = os.getenv("AMADEUS_API_KEY") or os.getenv("AMADEUS_CLIENT_ID")
    API_SECRET = os.getenv("AMADEUS_API_SECRET") or os.getenv("AMADEUS_CLIENT_SECRET")

# Amadeus URLs
TEST_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
PROD_URL = "https://api.amadeus.com/v1/security/oauth2/token"

def test_amadeus_auth(use_prod=False):
    """Test Amadeus OAuth2 authentication."""
    url = PROD_URL if use_prod else TEST_URL
    env_name = "PRODUCTION" if use_prod else "TEST"

    print(f"\n{'='*50}")
    print(f"Testing Amadeus API ({env_name})")
    print(f"{'='*50}")

    if not API_KEY or not API_SECRET:
        print("ERROR: Missing API credentials!")
        print(f"  AMADEUS_API_KEY: {'Set' if API_KEY else 'NOT SET'}")
        print(f"  AMADEUS_API_SECRET: {'Set' if API_SECRET else 'NOT SET'}")
        return False

    print(f"API Key: {API_KEY[:8]}...{API_KEY[-4:]}")
    print(f"API Secret: {API_SECRET[:4]}...{API_SECRET[-4:]}")
    print(f"URL: {url}")
    print()

    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "client_credentials",
                "client_id": API_KEY,
                "client_secret": API_SECRET
            },
            timeout=30
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token", "")
            expires = data.get("expires_in", 0)
            print(f"SUCCESS! Token obtained")
            print(f"  Token: {token[:20]}...{token[-10:]}")
            print(f"  Expires in: {expires} seconds")
            return True
        else:
            print(f"FAILED!")
            print(f"  Response: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print("ERROR: Request timeout")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"ERROR: Connection failed - {e}")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    # Test both environments
    use_prod = "--prod" in sys.argv

    success = test_amadeus_auth(use_prod=use_prod)

    print(f"\n{'='*50}")
    if success:
        print("Amadeus API connection: OK")
    else:
        print("Amadeus API connection: FAILED")
        print("\nTroubleshooting:")
        print("1. Check API key/secret di Railway variables")
        print("2. Pastikan pakai Test credentials untuk test.api.amadeus.com")
        print("3. Pastikan pakai Production credentials untuk api.amadeus.com")
    print(f"{'='*50}\n")

    sys.exit(0 if success else 1)
