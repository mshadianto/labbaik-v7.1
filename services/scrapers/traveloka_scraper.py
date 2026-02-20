"""
LABBAIK AI v7.5 - Traveloka Scraper
====================================
Scraper for Traveloka Umrah packages.

Note: This is a respectful scraper that:
- Honors robots.txt
- Uses conservative rate limits (5 req/min)
- Rotates user agents
- Caches results to minimize requests
"""

import re
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from bs4 import BeautifulSoup

from services.price_aggregation.models import (
    AggregatedOffer, SourceType, OfferType, AvailabilityStatus,
    convert_idr_to_sar
)
from services.scrapers.base_scraper import BaseScraper, ScraperConfig

logger = logging.getLogger(__name__)


class TravelokaScraper(BaseScraper):
    """
    Scraper for Traveloka Umrah packages.

    Traveloka has umrah package listings that we can scrape.
    We use their API endpoints when available, falling back to HTML parsing.
    """

    DEFAULT_CONFIG = ScraperConfig(
        name="traveloka",
        base_url="https://www.traveloka.com",
        enabled=True,
        timeout=30,
        max_retries=3,
        user_agent_rotate=True
    )

    # Traveloka API endpoints (may change)
    SEARCH_API = "/api/v2/umrah/search"
    PACKAGE_API = "/api/v2/umrah/package"

    # Search page URLs
    UMRAH_PAGE = "/id-id/umrah"

    def __init__(self, config: ScraperConfig = None):
        super().__init__(config or self.DEFAULT_CONFIG)
        self._package_cache: Dict[str, List[AggregatedOffer]] = {}

    def scrape_packages(
        self,
        departure_city: str = "Jakarta",
        check_in: date = None,
        check_out: date = None,
        **kwargs
    ) -> List[AggregatedOffer]:
        """
        Scrape Umrah packages from Traveloka.

        Args:
            departure_city: Departure city (Jakarta, Surabaya, etc.)
            check_in: Departure date
            check_out: Return date (optional)

        Returns:
            List of AggregatedOffer objects
        """
        if not self.is_enabled():
            return []

        logger.info(f"Scraping Traveloka packages from {departure_city}")

        # Check cache
        cache_key = f"{departure_city}:{check_in}"
        if cache_key in self._package_cache:
            logger.debug("Returning cached Traveloka packages")
            return self._package_cache[cache_key]

        offers = []

        try:
            # Try API first
            api_offers = self._scrape_via_api(departure_city, check_in)
            if api_offers:
                offers.extend(api_offers)
            else:
                # Fallback to HTML scraping
                html_offers = self._scrape_via_html(departure_city, check_in)
                offers.extend(html_offers)

        except Exception as e:
            logger.error(f"Traveloka scraping failed: {e}")

        # If no results, use demo data
        if not offers:
            offers = self._get_demo_packages(departure_city)

        # Cache results
        self._package_cache[cache_key] = offers

        logger.info(f"Traveloka: Found {len(offers)} packages")
        return offers

    # Hotel search endpoints
    HOTEL_SEARCH_URL = "/en-id/hotel/area"
    HOTEL_API = "/api/v2/hotel/search"

    # City slugs for Traveloka hotel search
    HOTEL_CITY_SLUGS = {
        "MAKKAH": {"slug": "makkah", "region_id": "108613"},
        "MADINAH": {"slug": "madinah", "region_id": "108614"},
        "MECCA": {"slug": "makkah", "region_id": "108613"},
        "MEDINA": {"slug": "madinah", "region_id": "108614"},
    }

    def scrape_hotels(
        self,
        city: str,
        check_in: date = None,
        check_out: date = None,
        **kwargs
    ) -> List[AggregatedOffer]:
        """
        Scrape hotels from Traveloka for Makkah/Madinah.

        Strategy: API → HTML parse → demo fallback.
        """
        if not self.is_enabled():
            return []

        city_upper = city.upper().replace("MECCA", "MAKKAH").replace("MEDINA", "MADINAH")
        logger.info(f"Scraping Traveloka hotels for {city_upper}")

        if not check_in:
            check_in = date.today() + timedelta(days=30)
        if not check_out:
            check_out = check_in + timedelta(days=3)

        cache_key = f"hotel:{city_upper}:{check_in}"
        if cache_key in self._package_cache:
            return self._package_cache[cache_key]

        offers = []

        try:
            offers = self._scrape_hotels_api(city_upper, check_in, check_out)
            if not offers:
                offers = self._scrape_hotels_html(city_upper, check_in, check_out)
        except Exception as e:
            logger.error(f"Traveloka hotel scraping failed: {e}")

        if not offers:
            offers = self._get_demo_hotels(city_upper, check_in, check_out)

        self._package_cache[cache_key] = offers
        logger.info(f"Traveloka: Found {len(offers)} hotels for {city_upper}")
        return offers

    def _scrape_hotels_api(
        self, city: str, check_in: date, check_out: date
    ) -> List[AggregatedOffer]:
        """Try Traveloka hotel search API."""
        city_info = self.HOTEL_CITY_SLUGS.get(city)
        if not city_info:
            return []

        api_url = f"{self.config.base_url}{self.HOTEL_API}"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Domain": "hotel",
        }
        payload = {
            "regionId": city_info["region_id"],
            "checkIn": check_in.isoformat(),
            "checkOut": check_out.isoformat(),
            "rooms": 1,
            "adults": 2,
            "currency": "IDR",
        }

        response = self._make_request(
            api_url, method="POST", json_data=payload, headers=headers
        )
        if not response or response.status_code != 200:
            return []

        offers = []
        nights = max(1, (check_out - check_in).days)

        try:
            data = response.json()
            hotels = (
                data.get("data", {}).get("hotels", [])
                or data.get("data", {}).get("properties", [])
                or data.get("results", [])
            )

            for hotel in hotels[:30]:
                name = hotel.get("name") or hotel.get("hotelName", "Hotel")
                price_per_night = float(hotel.get("price", 0) or hotel.get("nightlyPrice", 0))
                if price_per_night <= 0:
                    continue

                stars = int(hotel.get("star", 0) or hotel.get("starRating", 0))
                price_total = price_per_night * nights

                offer = self._create_offer(
                    name=name,
                    price_idr=price_total,
                    offer_type=OfferType.HOTEL,
                    city=city,
                    source_offer_id=str(hotel.get("id", "")),
                    stars=stars or None,
                    source_url=hotel.get("url") or hotel.get("deeplink"),
                    is_available=True,
                    price_sar=convert_idr_to_sar(price_total),
                )
                offers.append(offer)
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.debug(f"Traveloka hotel API parse failed: {e}")

        return offers

    def _scrape_hotels_html(
        self, city: str, check_in: date, check_out: date
    ) -> List[AggregatedOffer]:
        """Fallback: parse Traveloka hotel search HTML page."""
        city_info = self.HOTEL_CITY_SLUGS.get(city)
        if not city_info:
            return []

        search_url = (
            f"{self.config.base_url}{self.HOTEL_SEARCH_URL}"
            f"/{city_info['slug']}"
            f"?checkin={check_in.isoformat()}&checkout={check_out.isoformat()}"
            f"&rooms=1&adults=2"
        )

        response = self._make_request(search_url)
        if not response:
            return []

        offers = []
        nights = max(1, (check_out - check_in).days)

        try:
            soup = BeautifulSoup(response.text, "html.parser")
            cards = soup.select(
                "[data-testid='hotel-card'], .hotel-card, .property-card, "
                "[data-testid='PropertyCard']"
            )

            for card in cards[:20]:
                name_el = card.select_one(
                    "h2, h3, .hotel-name, [data-testid='hotel-name'], "
                    "[data-testid='PropertyName']"
                )
                price_el = card.select_one(
                    ".price, [data-testid='price'], [data-testid='PropertyPrice']"
                )
                stars_el = card.select_one(
                    ".stars, .star-rating, [data-testid='star-rating']"
                )

                if not name_el or not price_el:
                    continue

                name = name_el.get_text(strip=True)
                price_per_night = self._parse_price(price_el.get_text(strip=True))
                if price_per_night <= 0:
                    continue

                stars = self._parse_stars(stars_el.get_text(strip=True)) if stars_el else None
                price_total = price_per_night * nights

                link_el = card.select_one("a[href]")
                source_url = None
                if link_el:
                    href = link_el.get("href", "")
                    if href.startswith("/"):
                        source_url = f"{self.config.base_url}{href}"
                    elif href.startswith("http"):
                        source_url = href

                offer = self._create_offer(
                    name=name,
                    price_idr=price_total,
                    offer_type=OfferType.HOTEL,
                    city=city,
                    stars=stars,
                    source_url=source_url,
                    is_available=True,
                    price_sar=convert_idr_to_sar(price_total),
                )
                offers.append(offer)
        except Exception as e:
            logger.error(f"Traveloka hotel HTML parse failed: {e}")

        return offers

    def _get_demo_hotels(
        self, city: str, check_in: date, check_out: date
    ) -> List[AggregatedOffer]:
        """Return demo hotel data when scraping fails."""
        nights = max(1, (check_out - check_in).days)

        demo_data = {
            "MAKKAH": [
                {"name": "Grand Zam Zam Tower", "stars": 4, "price_per_night": 1_900_000},
                {"name": "Hilton Makkah Convention Hotel", "stars": 5, "price_per_night": 3_500_000},
                {"name": "Raffles Makkah Palace", "stars": 5, "price_per_night": 5_000_000},
                {"name": "Makkah Clock Royal Tower", "stars": 5, "price_per_night": 4_200_000},
            ],
            "MADINAH": [
                {"name": "Dar Al Taqwa Hotel Madinah", "stars": 4, "price_per_night": 1_600_000},
                {"name": "Madinah Hilton Hotel", "stars": 5, "price_per_night": 2_600_000},
                {"name": "Oberoi Madinah", "stars": 5, "price_per_night": 3_500_000},
                {"name": "Crowne Plaza Madinah", "stars": 5, "price_per_night": 2_400_000},
            ],
        }

        hotels = demo_data.get(city, demo_data["MAKKAH"])
        offers = []

        for hotel in hotels:
            price_total = hotel["price_per_night"] * nights
            offer = self._create_offer(
                name=hotel["name"],
                price_idr=price_total,
                offer_type=OfferType.HOTEL,
                city=city,
                source_offer_id=f"traveloka_demo_{hotel['name'][:10]}",
                stars=hotel["stars"],
                is_available=True,
                price_sar=convert_idr_to_sar(price_total),
                confidence_score=0.5,
            )
            offers.append(offer)

        return offers

    def _scrape_via_api(
        self,
        departure_city: str,
        check_in: date = None
    ) -> List[AggregatedOffer]:
        """Try to scrape via Traveloka's internal API."""
        offers = []

        # Traveloka uses a GraphQL-like API
        # This is a best-effort attempt - may need adjustment
        api_url = f"{self.config.base_url}{self.SEARCH_API}"

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Domain": "umrah",
        }

        payload = {
            "departureCity": departure_city,
            "departureDate": check_in.isoformat() if check_in else None,
            "pax": 1,
            "currency": "IDR"
        }

        response = self._make_request(
            api_url,
            method="POST",
            json_data=payload,
            headers=headers
        )

        if response and response.status_code == 200:
            try:
                data = response.json()
                offers = self._parse_api_response(data)
            except (json.JSONDecodeError, KeyError) as e:
                logger.debug(f"API response parsing failed: {e}")

        return offers

    def _scrape_via_html(
        self,
        departure_city: str,
        check_in: date = None
    ) -> List[AggregatedOffer]:
        """Fallback: Scrape via HTML page parsing."""
        offers = []

        # Build search URL
        city_slug = departure_city.lower().replace(" ", "-")
        search_url = f"{self.config.base_url}{self.UMRAH_PAGE}?from={city_slug}"

        if check_in:
            search_url += f"&date={check_in.isoformat()}"

        response = self._make_request(search_url)

        if not response:
            return offers

        try:
            soup = BeautifulSoup(response.text, "html.parser")

            # Find package cards (selector may change)
            package_cards = soup.select("div[data-testid='umrah-package-card']")

            if not package_cards:
                # Try alternative selector
                package_cards = soup.select(".package-card, .umrah-package")

            for card in package_cards[:20]:  # Limit to 20
                offer = self._parse_package_card(card, departure_city)
                if offer:
                    offers.append(offer)

        except Exception as e:
            logger.error(f"HTML parsing failed: {e}")

        return offers

    def _parse_api_response(self, data: Dict) -> List[AggregatedOffer]:
        """Parse API JSON response into offers."""
        offers = []

        packages = data.get("data", {}).get("packages", [])

        for pkg in packages:
            try:
                price_idr = float(pkg.get("price", 0))

                offer = self._create_offer(
                    name=pkg.get("name", "Paket Umrah Traveloka"),
                    price_idr=price_idr,
                    offer_type=OfferType.PACKAGE,
                    city=pkg.get("departureCity", "Jakarta"),
                    source_offer_id=pkg.get("id"),
                    duration_days=pkg.get("duration", 9),
                    departure_city=pkg.get("departureCity"),
                    airline=pkg.get("airline"),
                    hotel_makkah=pkg.get("hotelMakkah"),
                    hotel_makkah_stars=pkg.get("hotelMakkahStars", 4),
                    hotel_madinah=pkg.get("hotelMadinah"),
                    hotel_madinah_stars=pkg.get("hotelMadinahStars", 4),
                    inclusions=pkg.get("inclusions", []),
                    source_url=pkg.get("url"),
                    is_available=pkg.get("available", True),
                    price_sar=convert_idr_to_sar(price_idr)
                )
                offers.append(offer)

            except Exception as e:
                logger.warning(f"Failed to parse package: {e}")

        return offers

    def _parse_package_card(
        self,
        card: BeautifulSoup,
        departure_city: str
    ) -> Optional[AggregatedOffer]:
        """Parse a single package card HTML element."""
        try:
            # Extract name
            name_elem = card.select_one(".package-name, h3, [data-testid='package-name']")
            name = name_elem.get_text(strip=True) if name_elem else "Paket Umrah"

            # Extract price
            price_elem = card.select_one(".price, [data-testid='price']")
            price_text = price_elem.get_text(strip=True) if price_elem else "0"
            price_idr = self._parse_price(price_text)

            if price_idr <= 0:
                return None

            # Extract duration
            duration_elem = card.select_one(".duration, [data-testid='duration']")
            duration_text = duration_elem.get_text(strip=True) if duration_elem else "9 Hari"
            duration_days = self._parse_duration(duration_text)

            # Extract hotels
            hotel_makkah = None
            hotel_madinah = None
            hotel_makkah_stars = 4
            hotel_madinah_stars = 4

            hotel_elems = card.select(".hotel-name, [data-testid='hotel']")
            for i, hotel_elem in enumerate(hotel_elems[:2]):
                hotel_text = hotel_elem.get_text(strip=True)
                if i == 0:
                    hotel_makkah = hotel_text
                else:
                    hotel_madinah = hotel_text

            # Extract stars
            stars_elems = card.select(".stars, .rating")
            for i, stars_elem in enumerate(stars_elems[:2]):
                stars = self._parse_stars(stars_elem.get_text(strip=True))
                if i == 0:
                    hotel_makkah_stars = stars
                else:
                    hotel_madinah_stars = stars

            # Extract airline
            airline_elem = card.select_one(".airline, [data-testid='airline']")
            airline = airline_elem.get_text(strip=True) if airline_elem else None

            # Extract URL
            link_elem = card.select_one("a[href]")
            source_url = None
            if link_elem:
                href = link_elem.get("href", "")
                if href.startswith("/"):
                    source_url = f"{self.config.base_url}{href}"
                elif href.startswith("http"):
                    source_url = href

            return self._create_offer(
                name=name,
                price_idr=price_idr,
                offer_type=OfferType.PACKAGE,
                city=departure_city,
                duration_days=duration_days,
                departure_city=departure_city,
                airline=airline,
                hotel_makkah=hotel_makkah,
                hotel_makkah_stars=hotel_makkah_stars,
                hotel_madinah=hotel_madinah,
                hotel_madinah_stars=hotel_madinah_stars,
                source_url=source_url,
                is_available=True,
                price_sar=convert_idr_to_sar(price_idr)
            )

        except Exception as e:
            logger.warning(f"Failed to parse package card: {e}")
            return None

    def _get_demo_packages(self, departure_city: str) -> List[AggregatedOffer]:
        """Return demo packages when scraping fails."""
        demo_packages = [
            {
                "name": "Paket Umrah Ekonomi 9 Hari",
                "price_idr": 25_000_000,
                "duration_days": 9,
                "hotel_makkah": "Grand Zam Zam Tower",
                "hotel_makkah_stars": 4,
                "hotel_madinah": "Dar Al Taqwa",
                "hotel_madinah_stars": 4,
                "airline": "Saudi Airlines",
            },
            {
                "name": "Paket Umrah Premium 9 Hari",
                "price_idr": 35_000_000,
                "duration_days": 9,
                "hotel_makkah": "Hilton Makkah Convention",
                "hotel_makkah_stars": 5,
                "hotel_madinah": "Madinah Hilton",
                "hotel_madinah_stars": 5,
                "airline": "Garuda Indonesia",
            },
            {
                "name": "Paket Umrah VIP 12 Hari",
                "price_idr": 55_000_000,
                "duration_days": 12,
                "hotel_makkah": "Swissotel Al Maqam",
                "hotel_makkah_stars": 5,
                "hotel_madinah": "Oberoi Madinah",
                "hotel_madinah_stars": 5,
                "airline": "Emirates",
            },
        ]

        offers = []
        for pkg in demo_packages:
            price_idr = pkg["price_idr"]
            offer = self._create_offer(
                name=pkg["name"],
                price_idr=price_idr,
                offer_type=OfferType.PACKAGE,
                city=departure_city,
                source_offer_id=f"traveloka_demo_{pkg['name'][:10]}",
                duration_days=pkg["duration_days"],
                departure_city=departure_city,
                airline=pkg.get("airline"),
                hotel_makkah=pkg.get("hotel_makkah"),
                hotel_makkah_stars=pkg.get("hotel_makkah_stars", 4),
                hotel_madinah=pkg.get("hotel_madinah"),
                hotel_madinah_stars=pkg.get("hotel_madinah_stars", 4),
                is_available=True,
                price_sar=convert_idr_to_sar(price_idr),
                confidence_score=0.5  # Lower confidence for demo
            )
            offers.append(offer)

        return offers


def create_traveloka_scraper(enabled: bool = True) -> TravelokaScraper:
    """Factory function to create TravelokaScraper."""
    config = TravelokaScraper.DEFAULT_CONFIG
    config.enabled = enabled
    return TravelokaScraper(config)
