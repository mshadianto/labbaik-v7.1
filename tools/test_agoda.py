"""
LABBAIK AI - Agoda API Tester
==============================
Test Agoda RapidAPI endpoint to discover JSON structure.

Usage:
    # Set API key first
    export RAPIDAPI_KEY="your_key_here"

    # Run test
    python tools/test_agoda.py
"""

import os
import sys
import json

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import httpx
except ImportError:
    print("Installing httpx...")
    os.system("pip install httpx")
    import httpx


# =============================================================================
# CONFIG
# =============================================================================

RAPIDAPI_HOST = "agoda-com.p.rapidapi.com"
RAPIDAPI_URL = "https://agoda-com.p.rapidapi.com/hotels/search-overnight"

# Location IDs (to be discovered)
# Format: "type_id" where type=1 is city, type=2 is region, etc.
LOCATION_IDS = {
    "DEFAULT": "1_318",      # Default test ID
    # TODO: Discover Makkah & Madinah IDs
    # "MAKKAH": "1_xxx",
    # "MADINAH": "1_yyy",
}


def get_api_key() -> str:
    """Get RapidAPI key from environment."""
    # Try multiple sources
    key = os.getenv("RAPIDAPI_KEY")

    if not key:
        # Try .env file
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        if os.path.exists(env_file):
            with open(env_file) as f:
                for line in f:
                    if line.startswith("RAPIDAPI_KEY="):
                        key = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break

    if not key:
        # Try streamlit secrets
        try:
            import streamlit as st
            if hasattr(st, 'secrets'):
                key = st.secrets.get("RAPIDAPI_KEY")
        except Exception:
            pass

    return key


def test_agoda_search(location_id: str = None, verbose: bool = True):
    """
    Test Agoda search-overnight endpoint.

    Args:
        location_id: Location ID (default: 1_318)
        verbose: Print full response

    Returns:
        Response data dict
    """
    key = get_api_key()
    if not key:
        print("[ERROR] Missing RAPIDAPI_KEY!")
        print("Set it via:")
        print("  export RAPIDAPI_KEY='your_key_here'")
        print("  OR add to .env file: RAPIDAPI_KEY=your_key_here")
        return None

    location_id = location_id or LOCATION_IDS["DEFAULT"]

    headers = {
        "x-rapidapi-host": RAPIDAPI_HOST,
        "x-rapidapi-key": key,
        "Accept": "application/json",
        "User-Agent": "umrah-crawler/1.3"
    }

    params = {
        "id": location_id,
    }

    print(f"[INFO] Testing Agoda API...")
    print(f"[INFO] Location ID: {location_id}")
    print(f"[INFO] URL: {RAPIDAPI_URL}")
    print()

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.get(RAPIDAPI_URL, headers=headers, params=params)

            print(f"HTTP Status: {resp.status_code}")
            print(f"Content-Type: {resp.headers.get('content-type', 'N/A')}")
            print()

            if resp.status_code != 200:
                print(f"[ERROR] Request failed!")
                print(f"Response: {resp.text[:500]}")
                return None

            data = resp.json()

            # Analyze structure
            if isinstance(data, dict):
                print(f"Top-level keys: {list(data.keys())}")
                print()

                # Look for common patterns
                for key_name in ["data", "results", "hotels", "properties", "items"]:
                    if key_name in data:
                        val = data[key_name]
                        if isinstance(val, list):
                            print(f"  '{key_name}': List with {len(val)} items")
                            if val and isinstance(val[0], dict):
                                print(f"    First item keys: {list(val[0].keys())[:10]}")
                        elif isinstance(val, dict):
                            print(f"  '{key_name}': Dict with keys: {list(val.keys())[:10]}")
                        else:
                            print(f"  '{key_name}': {type(val).__name__}")

            elif isinstance(data, list):
                print(f"Response is a list with {len(data)} items")
                if data and isinstance(data[0], dict):
                    print(f"First item keys: {list(data[0].keys())}")

            print()
            print("=" * 60)
            print("FULL RESPONSE (first 4000 chars):")
            print("=" * 60)

            formatted = json.dumps(data, indent=2, ensure_ascii=False)
            print(formatted[:4000])

            if len(formatted) > 4000:
                print(f"\n... (truncated, total {len(formatted)} chars)")

            return data

    except httpx.TimeoutException:
        print("[ERROR] Request timeout!")
        return None
    except httpx.HTTPError as e:
        print(f"[ERROR] HTTP error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON parse error: {e}")
        print(f"Raw response: {resp.text[:500]}")
        return None
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return None


def discover_location_id(city_name: str):
    """
    Try to discover Agoda location ID for a city.

    This is a placeholder - actual discovery would require
    a separate API endpoint or manual lookup.
    """
    print(f"[INFO] Location ID discovery for '{city_name}'")
    print("[INFO] Check Agoda website or API docs for location IDs")
    print()
    print("Known patterns:")
    print("  1_xxx = City ID")
    print("  2_xxx = Region ID")
    print("  3_xxx = Country ID")
    print()
    print("For Makkah/Madinah, try searching on Agoda.com")
    print("and check the URL for the location ID.")


if __name__ == "__main__":
    print("=" * 60)
    print("LABBAIK AI - Agoda API Tester")
    print("=" * 60)
    print()

    # Check for command line args
    if len(sys.argv) > 1:
        location_id = sys.argv[1]
        print(f"Using location ID from args: {location_id}")
    else:
        location_id = None

    result = test_agoda_search(location_id)

    if result:
        print()
        print("=" * 60)
        print("TEST COMPLETE - Response received successfully!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Copy the JSON structure above")
        print("2. Identify hotel list path (e.g., data.hotels)")
        print("3. Find Makkah & Madinah location IDs")
        print("4. Create provider: app/providers/agoda_v13.py")
