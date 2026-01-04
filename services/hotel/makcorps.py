"""
LABBAIK AI v7.1 - Makcorps Hotel API Integration
=================================================
Full integration with Makcorps Hotel Price API for real-time
hotel prices in Makkah and Madinah.

API Documentation: https://docs.makcorps.com/
Pricing: $350-500/month for 10k-50k requests

Author: MS Hadianto - LABBAIK.AI
"""

import os
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
import streamlit as st
from functools import lru_cache

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

# Makcorps City IDs for Umrah destinations
CITY_IDS = {
    "makkah": "60763",      # Mecca, Saudi Arabia
    "mecca": "60763",
    "madinah": "60764",     # Medina, Saudi Arabia
    "medina": "60764",
    "jeddah": "60761",      # Jeddah (arrival city)
}

# Currency
DEFAULT_CURRENCY = "SAR"  # Saudi Riyal
SAR_TO_IDR = 4200

# API Configuration
API_BASE_URL = "https://api.makcorps.com"
REQUEST_TIMEOUT = 30


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class MakcorpsHotel:
    """Hotel data from Makcorps API"""
    hotel_id: str
    hotel_name: str
    city: str
    city_id: str

    # Pricing (from cheapest vendor)
    price_per_night: float
    currency: str
    vendor_name: str
    vendor_price: float

    # All vendor prices
    vendors: List[Dict] = field(default_factory=list)

    # Hotel details
    rating: float = 0.0
    review_count: int = 0
    address: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    image_url: str = ""
    amenities: List[str] = field(default_factory=list)

    # Meta
    fetched_at: str = ""
    source: str = "makcorps"

    def __post_init__(self):
        if not self.fetched_at:
            self.fetched_at = datetime.now().isoformat()

    @property
    def price_idr(self) -> float:
        """Price in Indonesian Rupiah"""
        if self.currency == "SAR":
            return self.price_per_night * SAR_TO_IDR
        elif self.currency == "USD":
            return self.price_per_night * 16000  # Approximate USD to IDR
        return self.price_per_night

    @property
    def stars(self) -> int:
        """Convert rating to star count"""
        if self.rating >= 4.5:
            return 5
        elif self.rating >= 4.0:
            return 4
        elif self.rating >= 3.0:
            return 3
        elif self.rating >= 2.0:
            return 2
        return 1

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        result = asdict(self)
        result['price_idr'] = self.price_idr
        result['stars'] = self.stars
        return result


@dataclass
class HotelSearchResult:
    """Search result container"""
    hotels: List[MakcorpsHotel]
    city: str
    check_in: str
    check_out: str
    total_count: int
    page: int
    currency: str
    fetched_at: str = ""
    source: str = "makcorps"
    api_calls_used: int = 0

    def __post_init__(self):
        if not self.fetched_at:
            self.fetched_at = datetime.now().isoformat()


# =============================================================================
# MAKCORPS API CLIENT
# =============================================================================

class MakcorpsClient:
    """
    Makcorps Hotel Price API Client

    Endpoints:
    - /mapping - Get city/hotel IDs
    - /city - Search hotels by city ID
    - /hotel - Get hotel details by ID

    Rate Limits:
    - Basic: 10,000 requests/month, 5 concurrent
    - Advance: 50,000 requests/month, 5 concurrent
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize with API key from env or secrets"""
        self.api_key = api_key or self._get_api_key()
        self.request_count = 0
        self.last_request_time = None

        if not self.api_key:
            logger.warning("Makcorps API key not configured")

    def _get_api_key(self) -> Optional[str]:
        """Get API key from environment or Streamlit secrets"""
        # Try environment variable
        key = os.getenv("MAKCORPS_API_KEY")
        if key:
            return key

        # Try Streamlit secrets
        try:
            if hasattr(st, 'secrets'):
                return st.secrets.get("MAKCORPS_API_KEY")
        except:
            pass

        return None

    @property
    def is_configured(self) -> bool:
        """Check if API is properly configured"""
        return bool(self.api_key)

    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make API request with error handling"""
        if not self.is_configured:
            logger.error("Makcorps API key not configured")
            return None

        url = f"{API_BASE_URL}/{endpoint}"

        # Add API key to params
        if params is None:
            params = {}
        params['api_key'] = self.api_key

        try:
            response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            self.request_count += 1
            self.last_request_time = datetime.now()

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 403:
                logger.error("Makcorps: Connection limit exceeded (403)")
                return None
            elif response.status_code == 404:
                logger.warning(f"Makcorps: No data or invalid key (404) - {endpoint}")
                return None
            else:
                logger.error(f"Makcorps API error: {response.status_code}")
                return None

        except requests.Timeout:
            logger.error(f"Makcorps request timeout: {endpoint}")
            return None
        except Exception as e:
            logger.error(f"Makcorps request failed: {str(e)}")
            return None

    # =========================================================================
    # MAPPING API
    # =========================================================================

    def get_city_id(self, city_name: str) -> Optional[str]:
        """
        Get city ID for a location.
        Uses cached IDs for known Umrah cities.
        """
        # Check cached IDs first
        city_lower = city_name.lower().strip()
        if city_lower in CITY_IDS:
            return CITY_IDS[city_lower]

        # Query mapping API
        data = self._make_request("mapping", {"name": city_name})
        if data and isinstance(data, list):
            for item in data:
                if item.get('type') == 'GEO':
                    return str(item.get('document_id'))

        return None

    def get_hotel_id(self, hotel_name: str) -> Optional[str]:
        """Get hotel ID by name"""
        data = self._make_request("mapping", {"name": hotel_name})
        if data and isinstance(data, list):
            for item in data:
                if item.get('type') == 'HOTEL':
                    return str(item.get('document_id'))

        return None

    # =========================================================================
    # HOTEL SEARCH API
    # =========================================================================

    def search_hotels_by_city(
        self,
        city: str,
        check_in: str,
        check_out: str,
        rooms: int = 1,
        adults: int = 2,
        currency: str = DEFAULT_CURRENCY,
        page: int = 0
    ) -> Optional[HotelSearchResult]:
        """
        Search hotels in a city.

        Args:
            city: City name (Makkah, Madinah, etc)
            check_in: Check-in date (YYYY-MM-DD)
            check_out: Check-out date (YYYY-MM-DD)
            rooms: Number of rooms
            adults: Number of adults
            currency: Currency code (SAR, USD, etc)
            page: Pagination (0-indexed, 30 hotels per page)

        Returns:
            HotelSearchResult with up to 30 hotels
        """
        # Get city ID
        city_id = self.get_city_id(city)
        if not city_id:
            logger.error(f"City ID not found for: {city}")
            return None

        # Make request
        params = {
            'cityid': city_id,
            'pagination': str(page),
            'cur': currency,
            'rooms': str(rooms),
            'adults': str(adults),
            'checkin': check_in,
            'checkout': check_out,
        }

        data = self._make_request("city", params)
        if not data:
            return None

        # Parse hotels
        hotels = []
        for hotel_data in data if isinstance(data, list) else []:
            hotel = self._parse_hotel(hotel_data, city, city_id, currency)
            if hotel:
                hotels.append(hotel)

        return HotelSearchResult(
            hotels=hotels,
            city=city,
            check_in=check_in,
            check_out=check_out,
            total_count=len(hotels),
            page=page,
            currency=currency,
            api_calls_used=self.request_count,
        )

    def search_hotels_by_city_name(
        self,
        city: str,
        check_in: str,
        check_out: str,
        rooms: int = 1,
        adults: int = 2,
        currency: str = DEFAULT_CURRENCY,
        page: int = 0
    ) -> Optional[HotelSearchResult]:
        """
        Alternative: Search by city name directly.
        URL format: /citysearch/{city}/{page}/{currency}/{rooms}/{adults}/{checkin}/{checkout}
        """
        endpoint = f"citysearch/{city}/{page}/{currency}/{rooms}/{adults}/{check_in}/{check_out}"

        data = self._make_request(endpoint)
        if not data:
            return None

        # Parse response
        hotels = []
        city_id = CITY_IDS.get(city.lower(), "unknown")

        for hotel_data in data if isinstance(data, list) else []:
            hotel = self._parse_hotel(hotel_data, city, city_id, currency)
            if hotel:
                hotels.append(hotel)

        return HotelSearchResult(
            hotels=hotels,
            city=city,
            check_in=check_in,
            check_out=check_out,
            total_count=len(hotels),
            page=page,
            currency=currency,
            api_calls_used=self.request_count,
        )

    def _parse_hotel(
        self,
        data: Dict,
        city: str,
        city_id: str,
        currency: str
    ) -> Optional[MakcorpsHotel]:
        """Parse hotel data from API response"""
        try:
            # Extract vendor prices (top 4 cheapest)
            vendors = []
            cheapest_price = float('inf')
            cheapest_vendor = ""

            # Vendor keys: vendor1, vendor2, vendor3, vendor4
            for i in range(1, 5):
                vendor_key = f"vendor{i}"
                price_key = f"price{i}"

                vendor_name = data.get(vendor_key, "")
                price = data.get(price_key, 0)

                if vendor_name and price:
                    try:
                        price_float = float(str(price).replace(',', ''))
                        vendors.append({
                            'name': vendor_name,
                            'price': price_float,
                        })

                        if price_float < cheapest_price:
                            cheapest_price = price_float
                            cheapest_vendor = vendor_name
                    except:
                        pass

            if cheapest_price == float('inf'):
                cheapest_price = 0

            return MakcorpsHotel(
                hotel_id=str(data.get('hotelId', data.get('hotel_id', ''))),
                hotel_name=data.get('name', data.get('hotel_name', 'Unknown')),
                city=city,
                city_id=city_id,
                price_per_night=cheapest_price,
                currency=currency,
                vendor_name=cheapest_vendor,
                vendor_price=cheapest_price,
                vendors=vendors,
                rating=float(data.get('reviews', {}).get('rating', 0) if isinstance(data.get('reviews'), dict) else 0),
                review_count=int(data.get('reviews', {}).get('count', 0) if isinstance(data.get('reviews'), dict) else 0),
                address=data.get('address', ''),
                latitude=float(data.get('geo', {}).get('lat', 0) if isinstance(data.get('geo'), dict) else 0),
                longitude=float(data.get('geo', {}).get('lon', 0) if isinstance(data.get('geo'), dict) else 0),
                image_url=data.get('image_url', data.get('img', '')),
            )

        except Exception as e:
            logger.error(f"Failed to parse hotel data: {str(e)}")
            return None

    # =========================================================================
    # HOTEL DETAILS API
    # =========================================================================

    def get_hotel_details(
        self,
        hotel_id: str,
        check_in: str,
        check_out: str,
        rooms: int = 1,
        adults: int = 2,
        currency: str = DEFAULT_CURRENCY
    ) -> Optional[MakcorpsHotel]:
        """
        Get detailed hotel info with room types and all vendor prices.
        """
        params = {
            'hotelid': hotel_id,
            'cur': currency,
            'rooms': str(rooms),
            'adults': str(adults),
            'checkin': check_in,
            'checkout': check_out,
        }

        data = self._make_request("hotel", params)
        if not data:
            return None

        return self._parse_hotel(data, "", "", currency)

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def get_usage_stats(self) -> Dict:
        """Get API usage statistics"""
        return {
            'requests_made': self.request_count,
            'last_request': self.last_request_time.isoformat() if self.last_request_time else None,
            'is_configured': self.is_configured,
        }


# =============================================================================
# CACHED CLIENT (Singleton with Streamlit caching)
# =============================================================================

@st.cache_resource(ttl=3600)  # Cache for 1 hour
def get_makcorps_client() -> MakcorpsClient:
    """Get cached Makcorps client instance"""
    return MakcorpsClient()


@st.cache_data(ttl=1800)  # Cache for 30 minutes
def search_umrah_hotels(
    city: str,
    check_in: str,
    check_out: str,
    rooms: int = 1,
    adults: int = 2,
    currency: str = "SAR"
) -> Optional[Dict]:
    """
    Cached hotel search for Umrah destinations.
    Returns dictionary for Streamlit caching compatibility.
    """
    client = get_makcorps_client()

    if not client.is_configured:
        logger.warning("Makcorps not configured, returning demo data")
        return _get_demo_hotels(city, check_in, check_out)

    result = client.search_hotels_by_city(
        city=city,
        check_in=check_in,
        check_out=check_out,
        rooms=rooms,
        adults=adults,
        currency=currency,
    )

    if result:
        return {
            'hotels': [h.to_dict() for h in result.hotels],
            'city': result.city,
            'check_in': result.check_in,
            'check_out': result.check_out,
            'total_count': result.total_count,
            'currency': result.currency,
            'fetched_at': result.fetched_at,
            'source': 'makcorps',
        }

    return _get_demo_hotels(city, check_in, check_out)


def _get_demo_hotels(city: str, check_in: str, check_out: str) -> Dict:
    """Demo hotel data when API is not available"""

    if city.lower() in ['makkah', 'mecca']:
        hotels = [
            {
                'hotel_id': 'demo_1',
                'hotel_name': 'Hilton Suites Makkah',
                'city': 'Makkah',
                'price_per_night': 450,
                'currency': 'SAR',
                'rating': 4.5,
                'stars': 5,
                'distance_to_haram': '200m',
                'source': 'demo',
            },
            {
                'hotel_id': 'demo_2',
                'hotel_name': 'Movenpick Hotel & Residence Hajar Tower',
                'city': 'Makkah',
                'price_per_night': 380,
                'currency': 'SAR',
                'rating': 4.3,
                'stars': 5,
                'distance_to_haram': '300m',
                'source': 'demo',
            },
            {
                'hotel_id': 'demo_3',
                'hotel_name': 'Elaf Ajyad Hotel',
                'city': 'Makkah',
                'price_per_night': 250,
                'currency': 'SAR',
                'rating': 4.0,
                'stars': 4,
                'distance_to_haram': '500m',
                'source': 'demo',
            },
        ]
    else:  # Madinah
        hotels = [
            {
                'hotel_id': 'demo_4',
                'hotel_name': 'Dar Al Taqwa Hotel',
                'city': 'Madinah',
                'price_per_night': 350,
                'currency': 'SAR',
                'rating': 4.4,
                'stars': 5,
                'distance_to_haram': '100m',
                'source': 'demo',
            },
            {
                'hotel_id': 'demo_5',
                'hotel_name': 'Shaza Al Madina',
                'city': 'Madinah',
                'price_per_night': 300,
                'currency': 'SAR',
                'rating': 4.2,
                'stars': 4,
                'distance_to_haram': '200m',
                'source': 'demo',
            },
        ]

    return {
        'hotels': hotels,
        'city': city,
        'check_in': check_in,
        'check_out': check_out,
        'total_count': len(hotels),
        'currency': 'SAR',
        'fetched_at': datetime.now().isoformat(),
        'source': 'demo',
    }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'MakcorpsClient',
    'MakcorpsHotel',
    'HotelSearchResult',
    'get_makcorps_client',
    'search_umrah_hotels',
    'CITY_IDS',
]
