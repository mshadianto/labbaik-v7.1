"""
LABBAIK AI v6.0 - Hybrid Umrah Data Fetcher
============================================
Menggabungkan FREE APIs + scraping untuk data Umrah terlengkap.

Data Sources (Priority Order):
1. Amadeus Hotel API (free tier)
2. Xotelo API (RapidAPI - $0 plan, 1000/month)
3. MakCorps Free API (30 calls/month)
4. PostgreSQL Cache (24h)
5. Demo Data (final fallback)

Transport & Distance:
- Haramain Railway (official timetable)
- SAPTCO (bus schedule)
- Nominatim + OSRM (geocoding + routing)

Author: MS Hadianto (Sopian) - LABBAIK.AI
"""

import requests
import time

# Module-level session for connection pooling across API calls
_http_session = requests.Session()
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass, asdict, field
from enum import Enum
from math import radians, sin, cos, sqrt, atan2

logger = logging.getLogger(__name__)


# ==========================================
# ENUMS & CONSTANTS
# ==========================================

class DataSource(Enum):
    """Data source priority"""
    AMADEUS = "amadeus_api"
    XOTELO = "xotelo_api"
    MAKCORPS = "makcorps_api"
    CACHE = "cached_data"
    DEMO = "demo_fallback"


class HotelRating(Enum):
    """Hotel classification"""
    LUXURY = "5_star"
    PREMIUM = "4_star"
    STANDARD = "3_star"
    BUDGET = "2_star"


# SAR to IDR conversion rate
from core.constants import CostConstants
SAR_TO_IDR = CostConstants.SAR_TO_IDR


# ==========================================
# DATA MODELS
# ==========================================

@dataclass
class HotelOffer:
    """Unified hotel offer model"""
    hotel_id: str
    hotel_name: str
    city: str  # Makkah / Madinah
    rating: str  # Luxury / Premium / Standard
    stars: int  # 2-5
    price_per_night_sar: float
    total_price_sar: float
    distance_to_haram_km: float
    walking_time_minutes: int
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    availability: str = "Available"
    amenities: List[str] = field(default_factory=list)
    source: str = "unknown"
    scraped_at: str = ""

    def __post_init__(self):
        if not self.scraped_at:
            self.scraped_at = datetime.now().isoformat()

    @property
    def price_per_night_idr(self) -> float:
        """Price per night in IDR"""
        return self.price_per_night_sar * SAR_TO_IDR

    @property
    def total_price_idr(self) -> float:
        """Total price in IDR"""
        return self.total_price_sar * SAR_TO_IDR

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        result = asdict(self)
        result['price_per_night_idr'] = self.price_per_night_idr
        result['total_price_idr'] = self.total_price_idr
        return result


@dataclass
class TransportOption:
    """Transport option model"""
    type: str  # train / bus / car / taxi
    operator: str  # Haramain / SAPTCO / etc
    route: str  # "Makkah - Madinah"
    price_sar: float
    duration_hours: float
    schedule: List[str] = field(default_factory=list)
    capacity: int = 0
    source: str = "official"

    @property
    def price_idr(self) -> float:
        """Price in IDR"""
        return self.price_sar * SAR_TO_IDR

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        result = asdict(self)
        result['price_idr'] = self.price_idr
        return result


# ==========================================
# API CLIENT 1: AMADEUS
# ==========================================

class AmadeusHotelAPI:
    """
    Amadeus Self-Service API for Hotel Search
    - Free quota: Production has free tier
    - Best for: Availability (booking-grade data)
    """

    BASE_URL = "https://test.api.amadeus.com"  # Test environment

    def __init__(self, api_key: str = None, api_secret: str = None):
        self.api_key = api_key
        self.api_secret = api_secret
        self._access_token = None
        self._token_expires_at = None

    def _get_access_token(self) -> Optional[str]:
        """Get OAuth2 access token"""
        if self._access_token and self._token_expires_at > datetime.now():
            return self._access_token

        if not self.api_key or not self.api_secret:
            logger.debug("Amadeus credentials not provided")
            return None

        try:
            response = _http_session.post(
                f"{self.BASE_URL}/v1/security/oauth2/token",
                data={
                    'grant_type': 'client_credentials',
                    'client_id': self.api_key,
                    'client_secret': self.api_secret
                },
                timeout=10
            )
            response.raise_for_status()

            data = response.json()
            self._access_token = data['access_token']
            self._token_expires_at = datetime.now() + timedelta(seconds=data['expires_in'] - 60)

            logger.info("Amadeus access token obtained")
            return self._access_token

        except Exception as e:
            logger.error(f"Amadeus auth failed: {str(e)}")
            return None

    def search_hotels_by_city(
        self,
        city_code: str,
        check_in: str,
        check_out: str,
        adults: int = 2
    ) -> List[HotelOffer]:
        """Search hotels in a city"""
        token = self._get_access_token()
        if not token:
            return []

        try:
            # Step 1: Get hotel list by city
            response = _http_session.get(
                f"{self.BASE_URL}/v1/reference-data/locations/hotels/by-city",
                headers={'Authorization': f'Bearer {token}'},
                params={'cityCode': city_code},
                timeout=15
            )
            response.raise_for_status()
            hotels_data = response.json()

            hotel_ids = [h['hotelId'] for h in hotels_data.get('data', [])][:20]

            if not hotel_ids:
                logger.warning(f"No hotels found for city {city_code}")
                return []

            # Step 2: Get offers for hotels
            response = _http_session.get(
                f"{self.BASE_URL}/v3/shopping/hotel-offers",
                headers={'Authorization': f'Bearer {token}'},
                params={
                    'hotelIds': ','.join(hotel_ids),
                    'checkInDate': check_in,
                    'checkOutDate': check_out,
                    'adults': adults,
                    'currency': 'SAR'
                },
                timeout=15
            )
            response.raise_for_status()
            offers_data = response.json()

            offers = []
            for hotel in offers_data.get('data', []):
                hotel_info = hotel.get('hotel', {})
                offer = hotel.get('offers', [{}])[0]
                price = offer.get('price', {})

                rating = self._estimate_rating(hotel_info.get('name', ''))

                offers.append(HotelOffer(
                    hotel_id=hotel_info.get('hotelId', ''),
                    hotel_name=hotel_info.get('name', 'Unknown Hotel'),
                    city="Makkah" if city_code == "MKK" else "Madinah",
                    rating=rating,
                    stars=self._rating_to_stars(rating),
                    price_per_night_sar=float(price.get('total', 0)),
                    total_price_sar=float(price.get('total', 0)),
                    distance_to_haram_km=0.0,
                    walking_time_minutes=0,
                    address=hotel_info.get('address', {}).get('lines', [''])[0],
                    latitude=hotel_info.get('latitude'),
                    longitude=hotel_info.get('longitude'),
                    availability="Available",
                    source=DataSource.AMADEUS.value
                ))

            logger.info(f"Amadeus returned {len(offers)} hotel offers")
            return offers

        except Exception as e:
            logger.error(f"Amadeus search failed: {str(e)}")
            return []

    def _estimate_rating(self, hotel_name: str) -> str:
        """Estimate hotel rating from name"""
        name_lower = hotel_name.lower()
        luxury_keywords = ['hilton', 'marriott', 'sheraton', 'fairmont', 'pullman', 'swissotel', 'raffles', 'conrad']
        premium_keywords = ['holiday inn', 'crowne plaza', 'movenpick', 'anjum', 'millennium', 'intercontinental']

        if any(keyword in name_lower for keyword in luxury_keywords):
            return "Luxury"
        elif any(keyword in name_lower for keyword in premium_keywords):
            return "Premium"
        else:
            return "Standard"

    def _rating_to_stars(self, rating: str) -> int:
        """Convert rating to stars"""
        mapping = {"Luxury": 5, "Premium": 4, "Standard": 3, "Budget": 2}
        return mapping.get(rating, 3)


# ==========================================
# API CLIENT 2: XOTELO (RapidAPI)
# ==========================================

class XoteloAPI:
    """
    Xotelo via RapidAPI
    - Plan: $0 with 1,000 requests/month
    """

    BASE_URL = "https://xotelo.p.rapidapi.com"

    def __init__(self, rapidapi_key: str = None):
        self.api_key = rapidapi_key
        self.headers = {
            'X-RapidAPI-Key': rapidapi_key or '',
            'X-RapidAPI-Host': 'xotelo.p.rapidapi.com'
        }

    def search_hotels(
        self,
        city: str,
        check_in: str,
        check_out: str,
        adults: int = 2
    ) -> List[HotelOffer]:
        """Search hotels via Xotelo"""
        if not self.api_key:
            logger.debug("Xotelo API key not provided")
            return []

        try:
            response = _http_session.get(
                f"{self.BASE_URL}/search",
                headers=self.headers,
                params={
                    'location': city,
                    'checkin': check_in,
                    'checkout': check_out,
                    'adults': adults
                },
                timeout=15
            )
            response.raise_for_status()
            data = response.json()

            offers = []
            for hotel in data.get('hotels', []):
                offers.append(HotelOffer(
                    hotel_id=str(hotel.get('id', '')),
                    hotel_name=hotel.get('name', 'Unknown'),
                    city=city,
                    rating=self._classify_rating(hotel.get('stars', 3)),
                    stars=hotel.get('stars', 3),
                    price_per_night_sar=float(hotel.get('price', 0)),
                    total_price_sar=float(hotel.get('price', 0)),
                    distance_to_haram_km=hotel.get('distance', 0.0),
                    walking_time_minutes=int(hotel.get('distance', 0) * 15),
                    address=hotel.get('address', ''),
                    source=DataSource.XOTELO.value
                ))

            logger.info(f"Xotelo returned {len(offers)} offers")
            return offers

        except Exception as e:
            logger.error(f"Xotelo search failed: {str(e)}")
            return []

    def _classify_rating(self, stars: int) -> str:
        """Convert stars to rating"""
        if stars >= 5:
            return "Luxury"
        elif stars >= 4:
            return "Premium"
        else:
            return "Standard"


# ==========================================
# API CLIENT 3: MAKCORPS
# ==========================================

class MakCorpsAPI:
    """
    MakCorps Free Hotel API
    - Free tier: 30 API calls
    """

    BASE_URL = "https://api.makcorps.com/free"

    def __init__(self):
        self.request_count = 0
        self.max_free_calls = 30

    def search_hotels(
        self,
        city: str,
        check_in: str = None,
        check_out: str = None
    ) -> List[HotelOffer]:
        """Get hotel list for city"""
        if self.request_count >= self.max_free_calls:
            logger.warning(f"MakCorps free quota exhausted ({self.max_free_calls} calls)")
            return []

        try:
            response = _http_session.get(
                f"{self.BASE_URL}/hotels",
                params={'city': city},
                timeout=15
            )
            response.raise_for_status()
            data = response.json()

            self.request_count += 1

            offers = []
            for hotel in data.get('hotels', []):
                offers.append(HotelOffer(
                    hotel_id=str(hotel.get('id', '')),
                    hotel_name=hotel.get('name', 'Unknown'),
                    city=city,
                    rating="Standard",
                    stars=3,
                    price_per_night_sar=float(hotel.get('price', 0)),
                    total_price_sar=float(hotel.get('price', 0)),
                    distance_to_haram_km=0.0,
                    walking_time_minutes=0,
                    address=hotel.get('address', ''),
                    source=DataSource.MAKCORPS.value
                ))

            logger.info(f"MakCorps returned {len(offers)} hotels ({self.request_count}/{self.max_free_calls} calls used)")
            return offers

        except Exception as e:
            logger.error(f"MakCorps search failed: {str(e)}")
            return []


# ==========================================
# GEOCODING & ROUTING
# ==========================================

class LocationService:
    """
    Free geocoding & routing services
    - Nominatim (OSM) for geocoding
    - OSRM for routing
    """

    # Coordinates for key locations
    HARAM_SHARIF = (21.4225, 39.8262)  # Kaaba
    MASJID_NABAWI = (24.4672, 39.6111)  # Prophet's Mosque

    def __init__(self):
        self._geocode_cache = {}

    def geocode_address(self, address: str, city: str) -> Optional[Tuple[float, float]]:
        """Geocode address using Nominatim (OSM)"""
        cache_key = f"{city}:{address}"

        if cache_key in self._geocode_cache:
            return self._geocode_cache[cache_key]

        try:
            response = _http_session.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    'q': f"{address}, {city}, Saudi Arabia",
                    'format': 'json',
                    'limit': 1
                },
                headers={'User-Agent': 'LABBAIK.AI Umrah Planner'},
                timeout=10
            )

            time.sleep(1)  # Rate limiting - MANDATORY for Nominatim

            response.raise_for_status()
            data = response.json()

            if data:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                coords = (lat, lon)
                self._geocode_cache[cache_key] = coords
                logger.debug(f"Geocoded: {address} -> ({lat}, {lon})")
                return coords

        except Exception as e:
            logger.error(f"Geocoding failed for {address}: {str(e)}")

        return None

    def calculate_distance_and_time(
        self,
        hotel_coords: Tuple[float, float],
        destination: str
    ) -> Tuple[float, int]:
        """Calculate walking distance and time using OSRM"""
        dest_coords = self.HARAM_SHARIF if destination == "haram" else self.MASJID_NABAWI

        try:
            url = f"http://router.project-osrm.org/route/v1/foot/{hotel_coords[1]},{hotel_coords[0]};{dest_coords[1]},{dest_coords[0]}"

            response = _http_session.get(url, params={'overview': 'false'}, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('routes'):
                route = data['routes'][0]
                distance_km = route['distance'] / 1000
                duration_min = int(route['duration'] / 60)
                return (distance_km, duration_min)

        except Exception as e:
            logger.error(f"OSRM routing failed: {str(e)}")

        # Fallback: Haversine distance estimate
        distance_km = self._haversine_distance(hotel_coords, dest_coords)
        walking_time = int(distance_km * 15)  # 15 min per km

        return (distance_km, walking_time)

    def _haversine_distance(self, coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """Calculate distance between two coordinates using Haversine formula"""
        lat1, lon1 = radians(coord1[0]), radians(coord1[1])
        lat2, lon2 = radians(coord2[0]), radians(coord2[1])

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))

        R = 6371  # Earth radius in km
        return R * c


# ==========================================
# TRANSPORT DATA
# ==========================================

class TransportService:
    """
    Transport data for Makkah-Madinah routes
    - Haramain High Speed Railway
    - SAPTCO Bus
    """

    HARAMAIN_SCHEDULE = [
        TransportOption(
            type="train",
            operator="Haramain Railway",
            route="Makkah - Madinah",
            price_sar=100.0,
            duration_hours=2.5,
            schedule=["06:00", "10:00", "14:00", "18:00"],
            capacity=400,
            source="official_haramain"
        ),
        TransportOption(
            type="train",
            operator="Haramain Railway",
            route="Madinah - Makkah",
            price_sar=100.0,
            duration_hours=2.5,
            schedule=["07:00", "11:00", "15:00", "19:00"],
            capacity=400,
            source="official_haramain"
        )
    ]

    SAPTCO_SCHEDULE = [
        TransportOption(
            type="bus",
            operator="SAPTCO",
            route="Makkah - Madinah",
            price_sar=50.0,
            duration_hours=5.0,
            schedule=["05:00", "09:00", "13:00", "17:00", "21:00"],
            capacity=45,
            source="official_saptco"
        ),
        TransportOption(
            type="bus",
            operator="SAPTCO",
            route="Madinah - Makkah",
            price_sar=50.0,
            duration_hours=5.0,
            schedule=["06:00", "10:00", "14:00", "18:00", "22:00"],
            capacity=45,
            source="official_saptco"
        )
    ]

    def get_transport_options(self, route: str) -> List[TransportOption]:
        """Get transport options for a route"""
        route_normalized = route.replace(" ", "").replace("-", "").lower()

        options = []

        # Haramain Train
        for train in self.HARAMAIN_SCHEDULE:
            train_route = train.route.replace(" ", "").replace("-", "").lower()
            if train_route == route_normalized:
                options.append(train)

        # SAPTCO Bus
        for bus in self.SAPTCO_SCHEDULE:
            bus_route = bus.route.replace(" ", "").replace("-", "").lower()
            if bus_route == route_normalized:
                options.append(bus)

        # Add taxi/private car option
        options.append(TransportOption(
            type="private_car",
            operator="Private Car/Taxi",
            route=route,
            price_sar=200.0,
            duration_hours=4.5,
            schedule=["Anytime"],
            capacity=4,
            source="estimated"
        ))

        return options


# ==========================================
# DEMO DATA
# ==========================================

class DemoDataProvider:
    """Fallback demo data when APIs are unavailable"""

    MAKKAH_HOTELS = [
        HotelOffer(
            hotel_id="demo_makkah_1",
            hotel_name="Swissotel Al Maqam Makkah",
            city="Makkah",
            rating="Luxury",
            stars=5,
            price_per_night_sar=850.0,
            total_price_sar=850.0,
            distance_to_haram_km=0.1,
            walking_time_minutes=2,
            address="Ibrahim Al Khalil St, Makkah",
            latitude=21.4195,
            longitude=39.8265,
            source=DataSource.DEMO.value
        ),
        HotelOffer(
            hotel_id="demo_makkah_2",
            hotel_name="Hilton Makkah Convention Hotel",
            city="Makkah",
            rating="Luxury",
            stars=5,
            price_per_night_sar=750.0,
            total_price_sar=750.0,
            distance_to_haram_km=0.3,
            walking_time_minutes=5,
            address="Jabal Omar, Makkah",
            latitude=21.4180,
            longitude=39.8230,
            source=DataSource.DEMO.value
        ),
        HotelOffer(
            hotel_id="demo_makkah_3",
            hotel_name="Anjum Hotel Makkah",
            city="Makkah",
            rating="Premium",
            stars=4,
            price_per_night_sar=450.0,
            total_price_sar=450.0,
            distance_to_haram_km=0.5,
            walking_time_minutes=8,
            address="King Abdul Aziz Rd, Makkah",
            latitude=21.4200,
            longitude=39.8220,
            source=DataSource.DEMO.value
        ),
        HotelOffer(
            hotel_id="demo_makkah_4",
            hotel_name="Al Shohada Hotel",
            city="Makkah",
            rating="Standard",
            stars=3,
            price_per_night_sar=250.0,
            total_price_sar=250.0,
            distance_to_haram_km=0.8,
            walking_time_minutes=12,
            address="Al Masjid Al Haram Rd, Makkah",
            latitude=21.4230,
            longitude=39.8200,
            source=DataSource.DEMO.value
        ),
    ]

    MADINAH_HOTELS = [
        HotelOffer(
            hotel_id="demo_madinah_1",
            hotel_name="Dar Al Taqwa Hotel",
            city="Madinah",
            rating="Luxury",
            stars=5,
            price_per_night_sar=650.0,
            total_price_sar=650.0,
            distance_to_haram_km=0.1,
            walking_time_minutes=2,
            address="Central Area, Madinah",
            latitude=24.4680,
            longitude=39.6110,
            source=DataSource.DEMO.value
        ),
        HotelOffer(
            hotel_id="demo_madinah_2",
            hotel_name="Madinah Hilton Hotel",
            city="Madinah",
            rating="Luxury",
            stars=5,
            price_per_night_sar=550.0,
            total_price_sar=550.0,
            distance_to_haram_km=0.3,
            walking_time_minutes=5,
            address="King Faisal Rd, Madinah",
            latitude=24.4690,
            longitude=39.6100,
            source=DataSource.DEMO.value
        ),
        HotelOffer(
            hotel_id="demo_madinah_3",
            hotel_name="Millennium Al Aqeeq Hotel",
            city="Madinah",
            rating="Premium",
            stars=4,
            price_per_night_sar=350.0,
            total_price_sar=350.0,
            distance_to_haram_km=0.5,
            walking_time_minutes=8,
            address="Al Aqeeq District, Madinah",
            latitude=24.4700,
            longitude=39.6080,
            source=DataSource.DEMO.value
        ),
        HotelOffer(
            hotel_id="demo_madinah_4",
            hotel_name="Al Noor Hotel Madinah",
            city="Madinah",
            rating="Standard",
            stars=3,
            price_per_night_sar=200.0,
            total_price_sar=200.0,
            distance_to_haram_km=0.7,
            walking_time_minutes=10,
            address="Central Madinah",
            latitude=24.4660,
            longitude=39.6120,
            source=DataSource.DEMO.value
        ),
    ]

    @classmethod
    def get_hotels(cls, city: str) -> List[HotelOffer]:
        """Get demo hotels for a city"""
        if city.lower() in ["makkah", "mecca"]:
            return cls.MAKKAH_HOTELS.copy()
        else:
            return cls.MADINAH_HOTELS.copy()


# ==========================================
# HYBRID DATA MANAGER
# ==========================================

class HybridUmrahDataManager:
    """
    Main orchestrator combining all data sources

    Priority:
    1. Amadeus (if configured)
    2. Xotelo (if quota available)
    3. MakCorps (if quota available)
    4. Cache
    5. Demo data
    """

    def __init__(
        self,
        amadeus_key: str = None,
        amadeus_secret: str = None,
        rapidapi_key: str = None,
        use_nusuk_scraping: bool = True,
        use_cache: bool = True
    ):
        # Initialize APIs
        self.amadeus = AmadeusHotelAPI(amadeus_key, amadeus_secret) if amadeus_key else None
        self.xotelo = XoteloAPI(rapidapi_key) if rapidapi_key else None
        self.makcorps = MakCorpsAPI()

        # Initialize services
        self.location = LocationService()
        self.transport = TransportService()

        # Caching
        self.use_cache = use_cache
        self._cache: Dict[str, Tuple[List[HotelOffer], datetime]] = {}
        self.cache_duration = timedelta(hours=24)

    def search_hotels(
        self,
        city: str,
        check_in: str = None,
        check_out: str = None,
        adults: int = 2,
        max_results: int = 50
    ) -> List[HotelOffer]:
        """Search hotels with multi-source fallback"""
        logger.info(f"Searching hotels in {city}...")

        # Check cache first
        cache_key = f"{city}:{check_in}:{check_out}"
        if self.use_cache and cache_key in self._cache:
            cached_offers, cached_at = self._cache[cache_key]
            if datetime.now() - cached_at < self.cache_duration:
                logger.info(f"Returning {len(cached_offers)} cached offers for {city}")
                return cached_offers

        all_offers = []
        sources_tried = []

        # Set default dates if not provided
        if not check_in:
            check_in = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        if not check_out:
            check_out = (datetime.now() + timedelta(days=35)).strftime("%Y-%m-%d")

        # Try Amadeus first
        if self.amadeus:
            try:
                city_code = "MKK" if city.lower() in ["makkah", "mecca"] else "MED"
                offers = self.amadeus.search_hotels_by_city(city_code, check_in, check_out, adults)
                if offers:
                    all_offers.extend(offers)
                    sources_tried.append("Amadeus")
            except Exception as e:
                logger.warning(f"Amadeus failed: {str(e)}")

        # Try Xotelo
        if self.xotelo and len(all_offers) < max_results:
            try:
                city_name = "Mecca" if city.lower() in ["makkah", "mecca"] else "Medina"
                offers = self.xotelo.search_hotels(city_name, check_in, check_out, adults)
                if offers:
                    all_offers.extend(offers)
                    sources_tried.append("Xotelo")
            except Exception as e:
                logger.warning(f"Xotelo failed: {str(e)}")

        # Try MakCorps
        if len(all_offers) < max_results:
            try:
                offers = self.makcorps.search_hotels(city, check_in, check_out)
                if offers:
                    all_offers.extend(offers)
                    sources_tried.append("MakCorps")
            except Exception as e:
                logger.warning(f"MakCorps failed: {str(e)}")

        # Fallback to demo data
        if len(all_offers) < 5:
            logger.info("Insufficient API data, using demo data")
            demo_offers = DemoDataProvider.get_hotels(city)
            all_offers.extend(demo_offers)
            sources_tried.append("Demo")

        # Enrich with distance/location data
        for offer in all_offers:
            if not offer.latitude or not offer.longitude:
                coords = self.location.geocode_address(offer.address, offer.city)
                if coords:
                    offer.latitude, offer.longitude = coords

            if offer.latitude and offer.longitude and offer.distance_to_haram_km == 0:
                dest = "haram" if city.lower() in ["makkah", "mecca"] else "nabawi"
                distance, walk_time = self.location.calculate_distance_and_time(
                    (offer.latitude, offer.longitude), dest
                )
                offer.distance_to_haram_km = distance
                offer.walking_time_minutes = walk_time

        # Remove duplicates and sort
        unique_offers = self._deduplicate_offers(all_offers)
        sorted_offers = sorted(unique_offers, key=lambda x: x.distance_to_haram_km)[:max_results]

        # Cache results
        if self.use_cache:
            self._cache[cache_key] = (sorted_offers, datetime.now())

        logger.info(f"Total: {len(sorted_offers)} unique offers from {', '.join(sources_tried) or 'cache'}")
        return sorted_offers

    def _deduplicate_offers(self, offers: List[HotelOffer]) -> List[HotelOffer]:
        """Remove duplicate hotels"""
        seen = set()
        unique = []

        for offer in offers:
            key = f"{offer.hotel_name.lower()}:{offer.city}"
            if key not in seen:
                seen.add(key)
                unique.append(offer)

        return unique

    def get_transport_options(self, from_city: str, to_city: str) -> List[TransportOption]:
        """Get transport options between cities"""
        route = f"{from_city} - {to_city}"
        return self.transport.get_transport_options(route)

    def calculate_umrah_cost(
        self,
        duration_days: int,
        num_persons: int,
        hotel_preference: str = "Premium",
        cities: List[str] = None
    ) -> Dict:
        """Calculate realistic Umrah cost using live data"""
        if cities is None:
            cities = ["Makkah", "Madinah"]

        logger.info(f"Calculating cost for {num_persons} persons, {duration_days} days, {hotel_preference}")

        nights_per_city = duration_days // len(cities)
        selected_hotels = {}
        total_accommodation_sar = 0

        for city in cities:
            offers = self.search_hotels(city, max_results=20)

            # Filter by preference
            filtered = [o for o in offers if o.rating == hotel_preference]

            if not filtered:
                # Fallback to any available
                filtered = offers

            if filtered:
                # Select hotel closest to Haram
                selected = min(filtered, key=lambda x: x.distance_to_haram_km)
                selected_hotels[city] = selected
                total_accommodation_sar += selected.price_per_night_sar * nights_per_city * num_persons

        # Transport costs
        transport_cost_sar = 0
        if len(cities) > 1:
            transport_options = self.get_transport_options(cities[0], cities[1])
            if transport_options:
                train_option = next((t for t in transport_options if t.type == "train"), transport_options[0])
                transport_cost_sar = train_option.price_sar * num_persons

        # Other costs (SAR)
        meals_cost_sar = 50 * duration_days * num_persons
        visa_cost_sar = 500 * num_persons
        misc_cost_sar = 300 * num_persons

        # Totals
        total_sar = total_accommodation_sar + transport_cost_sar + meals_cost_sar + visa_cost_sar + misc_cost_sar
        total_idr = total_sar * SAR_TO_IDR

        return {
            'breakdown': {
                'accommodation_sar': total_accommodation_sar,
                'accommodation_idr': total_accommodation_sar * SAR_TO_IDR,
                'transport_sar': transport_cost_sar,
                'transport_idr': transport_cost_sar * SAR_TO_IDR,
                'meals_sar': meals_cost_sar,
                'meals_idr': meals_cost_sar * SAR_TO_IDR,
                'visa_sar': visa_cost_sar,
                'visa_idr': visa_cost_sar * SAR_TO_IDR,
                'misc_sar': misc_cost_sar,
                'misc_idr': misc_cost_sar * SAR_TO_IDR,
                'total_sar': total_sar,
                'total_idr': total_idr,
                'per_person_sar': total_sar / num_persons,
                'per_person_idr': total_idr / num_persons
            },
            'hotels_selected': {city: hotel.to_dict() for city, hotel in selected_hotels.items()},
            'data_sources': list(set(h.source for h in selected_hotels.values())),
            'last_updated': datetime.now().isoformat()
        }
