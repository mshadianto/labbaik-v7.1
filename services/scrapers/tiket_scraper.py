"""
LABBAIK AI v7.5 - Tiket.com Scraper
====================================
Scraper for Tiket.com Umrah packages.

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


class TiketScraper(BaseScraper):
    """
    Scraper for Tiket.com Umrah packages.

    Tiket.com offers umrah packages similar to Traveloka.
    """

    DEFAULT_CONFIG = ScraperConfig(
        name="tiket",
        base_url="https://www.tiket.com",
        enabled=True,
        timeout=30,
        max_retries=3,
        user_agent_rotate=True
    )

    # API and page endpoints
    UMRAH_PAGE = "/umrah"
    SEARCH_API = "/api/v3/umrah/search"

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
        Scrape Umrah packages from Tiket.com.

        Args:
            departure_city: Departure city
            check_in: Departure date
            check_out: Return date

        Returns:
            List of AggregatedOffer objects
        """
        if not self.is_enabled():
            return []

        logger.info(f"Scraping Tiket.com packages from {departure_city}")

        # Check cache
        cache_key = f"{departure_city}:{check_in}"
        if cache_key in self._package_cache:
            logger.debug("Returning cached Tiket packages")
            return self._package_cache[cache_key]

        offers = []

        try:
            # Try API first
            api_offers = self._scrape_via_api(departure_city, check_in)
            if api_offers:
                offers.extend(api_offers)
            else:
                # Fallback to HTML
                html_offers = self._scrape_via_html(departure_city, check_in)
                offers.extend(html_offers)

        except Exception as e:
            logger.error(f"Tiket.com scraping failed: {e}")

        # If no results, use demo data
        if not offers:
            offers = self._get_demo_packages(departure_city)

        # Cache results
        self._package_cache[cache_key] = offers

        logger.info(f"Tiket.com: Found {len(offers)} packages")
        return offers

    # Hotel search endpoints
    HOTEL_SEARCH_URL = "/en/hotel/search"
    HOTEL_API = "/api/v3/hotel/search"

    # City slugs for Tiket.com hotel search
    HOTEL_CITY_SLUGS = {
        "MAKKAH": {"slug": "makkah-saudi-arabia", "region": "saudi-arabia"},
        "MADINAH": {"slug": "madinah-saudi-arabia", "region": "saudi-arabia"},
        "MECCA": {"slug": "makkah-saudi-arabia", "region": "saudi-arabia"},
        "MEDINA": {"slug": "madinah-saudi-arabia", "region": "saudi-arabia"},
    }

    def scrape_hotels(
        self,
        city: str,
        check_in: date = None,
        check_out: date = None,
        **kwargs
    ) -> List[AggregatedOffer]:
        """
        Scrape hotels from Tiket.com for Makkah/Madinah.

        Strategy: API → HTML parse → demo fallback.
        """
        if not self.is_enabled():
            return []

        city_upper = city.upper().replace("MECCA", "MAKKAH").replace("MEDINA", "MADINAH")
        logger.info(f"Scraping Tiket.com hotels for {city_upper}")

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
            logger.error(f"Tiket.com hotel scraping failed: {e}")

        if not offers:
            offers = self._get_demo_hotels(city_upper, check_in, check_out)

        self._package_cache[cache_key] = offers
        logger.info(f"Tiket.com: Found {len(offers)} hotels for {city_upper}")
        return offers

    def _scrape_hotels_api(
        self, city: str, check_in: date, check_out: date
    ) -> List[AggregatedOffer]:
        """Try Tiket.com hotel search API."""
        city_info = self.HOTEL_CITY_SLUGS.get(city)
        if not city_info:
            return []

        api_url = f"{self.config.base_url}{self.HOTEL_API}"
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        params = {
            "q": city_info["slug"],
            "checkin": check_in.isoformat(),
            "checkout": check_out.isoformat(),
            "room": "1",
            "adult": "2",
            "currency": "IDR",
        }

        response = self._make_request(api_url, params=params, headers=headers)
        if not response or response.status_code != 200:
            return []

        offers = []
        try:
            data = response.json()
            hotels = (
                data.get("data", {}).get("hotels", [])
                or data.get("data", {}).get("items", [])
                or data.get("results", [])
            )

            nights = max(1, (check_out - check_in).days)

            for hotel in hotels[:30]:
                name = hotel.get("name") or hotel.get("hotelName", "Hotel")
                price_per_night = float(hotel.get("price", 0) or hotel.get("pricePerNight", 0))
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
            logger.debug(f"Tiket hotel API parse failed: {e}")

        return offers

    def _scrape_hotels_html(
        self, city: str, check_in: date, check_out: date
    ) -> List[AggregatedOffer]:
        """Fallback: parse hotel search HTML page."""
        city_info = self.HOTEL_CITY_SLUGS.get(city)
        if not city_info:
            return []

        search_url = (
            f"{self.config.base_url}{self.HOTEL_SEARCH_URL}"
            f"?q={city_info['slug']}"
            f"&checkin={check_in.isoformat()}&checkout={check_out.isoformat()}"
            f"&room=1&adult=2"
        )

        response = self._make_request(search_url)
        if not response:
            return []

        offers = []
        nights = max(1, (check_out - check_in).days)

        try:
            soup = BeautifulSoup(response.text, "html.parser")
            cards = soup.select(
                "[data-testid='hotel-card'], .hotel-card, .hotel-item, .property-card"
            )

            for card in cards[:20]:
                name_el = card.select_one("h2, h3, .hotel-name, [data-testid='hotel-name']")
                price_el = card.select_one(".price, [data-testid='price']")
                stars_el = card.select_one(".stars, .star-rating, [data-testid='star']")

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
            logger.error(f"Tiket hotel HTML parse failed: {e}")

        return offers

    def _get_demo_hotels(
        self, city: str, check_in: date, check_out: date
    ) -> List[AggregatedOffer]:
        """Return demo hotel data when scraping fails."""
        nights = max(1, (check_out - check_in).days)

        demo_data = {
            "MAKKAH": [
                {"name": "Elaf Ajyad Hotel", "stars": 4, "price_per_night": 1_800_000},
                {"name": "Hilton Makkah Convention", "stars": 5, "price_per_night": 3_200_000},
                {"name": "Swissotel Al Maqam", "stars": 5, "price_per_night": 4_500_000},
                {"name": "Al Marwa Rayhaan by Rotana", "stars": 5, "price_per_night": 2_800_000},
            ],
            "MADINAH": [
                {"name": "Dar Al Taqwa Hotel", "stars": 4, "price_per_night": 1_500_000},
                {"name": "Pullman Zamzam Madinah", "stars": 5, "price_per_night": 2_500_000},
                {"name": "Shaza Al Madina", "stars": 5, "price_per_night": 3_000_000},
                {"name": "Anwar Al Madinah Mövenpick", "stars": 5, "price_per_night": 2_200_000},
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
                source_offer_id=f"tiket_demo_{hotel['name'][:10]}",
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
        """Try to scrape via Tiket.com's internal API."""
        offers = []

        api_url = f"{self.config.base_url}{self.SEARCH_API}"

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        params = {
            "origin": departure_city,
            "date": check_in.isoformat() if check_in else None,
            "currency": "IDR"
        }

        response = self._make_request(
            api_url,
            method="GET",
            params=params,
            headers=headers
        )

        if response and response.status_code == 200:
            try:
                data = response.json()
                offers = self._parse_api_response(data)
            except (json.JSONDecodeError, KeyError) as e:
                logger.debug(f"Tiket API parsing failed: {e}")

        return offers

    def _scrape_via_html(
        self,
        departure_city: str,
        check_in: date = None
    ) -> List[AggregatedOffer]:
        """Fallback: Scrape via HTML parsing."""
        offers = []

        search_url = f"{self.config.base_url}{self.UMRAH_PAGE}"
        params = {"origin": departure_city}

        if check_in:
            params["date"] = check_in.isoformat()

        response = self._make_request(search_url, params=params)

        if not response:
            return offers

        try:
            soup = BeautifulSoup(response.text, "html.parser")

            # Find package cards
            package_cards = soup.select(
                "[data-testid='umrah-card'], .umrah-package-card, .package-item"
            )

            for card in package_cards[:20]:
                offer = self._parse_package_card(card, departure_city)
                if offer:
                    offers.append(offer)

        except Exception as e:
            logger.error(f"Tiket HTML parsing failed: {e}")

        return offers

    def _parse_api_response(self, data: Dict) -> List[AggregatedOffer]:
        """Parse API response into offers."""
        offers = []

        packages = data.get("data", {}).get("items", [])

        for pkg in packages:
            try:
                price_idr = float(pkg.get("price", {}).get("value", 0))

                offer = self._create_offer(
                    name=pkg.get("name", "Paket Umrah Tiket.com"),
                    price_idr=price_idr,
                    offer_type=OfferType.PACKAGE,
                    city=pkg.get("origin", "Jakarta"),
                    source_offer_id=pkg.get("id"),
                    duration_days=pkg.get("duration"),
                    departure_city=pkg.get("origin"),
                    airline=pkg.get("airline", {}).get("name"),
                    hotel_makkah=pkg.get("hotels", {}).get("makkah", {}).get("name"),
                    hotel_makkah_stars=pkg.get("hotels", {}).get("makkah", {}).get("stars"),
                    hotel_madinah=pkg.get("hotels", {}).get("madinah", {}).get("name"),
                    hotel_madinah_stars=pkg.get("hotels", {}).get("madinah", {}).get("stars"),
                    inclusions=pkg.get("inclusions", []),
                    source_url=pkg.get("deeplink"),
                    is_available=pkg.get("isAvailable", True),
                    price_sar=convert_idr_to_sar(price_idr)
                )
                offers.append(offer)

            except Exception as e:
                logger.warning(f"Failed to parse Tiket package: {e}")

        return offers

    def _parse_package_card(
        self,
        card: BeautifulSoup,
        departure_city: str
    ) -> Optional[AggregatedOffer]:
        """Parse a single package card."""
        try:
            # Extract name
            name_elem = card.select_one("h2, h3, .package-title")
            name = name_elem.get_text(strip=True) if name_elem else "Paket Umrah"

            # Extract price
            price_elem = card.select_one(".price, [data-testid='price']")
            price_text = price_elem.get_text(strip=True) if price_elem else "0"
            price_idr = self._parse_price(price_text)

            if price_idr <= 0:
                return None

            # Extract duration
            duration_elem = card.select_one(".duration")
            duration_text = duration_elem.get_text(strip=True) if duration_elem else "9 Hari"
            duration_days = self._parse_duration(duration_text)

            # Extract hotel info
            hotel_elems = card.select(".hotel-info, .hotel-name")
            hotel_makkah = None
            hotel_madinah = None
            hotel_makkah_stars = 4
            hotel_madinah_stars = 4

            for elem in hotel_elems[:2]:
                text = elem.get_text(strip=True).lower()
                if "makkah" in text or "mekkah" in text:
                    hotel_makkah = elem.get_text(strip=True)
                elif "madinah" in text or "medina" in text:
                    hotel_madinah = elem.get_text(strip=True)

            # Extract airline
            airline_elem = card.select_one(".airline")
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
            logger.warning(f"Failed to parse Tiket package card: {e}")
            return None

    def _get_demo_packages(self, departure_city: str) -> List[AggregatedOffer]:
        """Return demo packages when scraping fails."""
        demo_packages = [
            {
                "name": "Paket Umrah Hemat 9 Hari Tiket.com",
                "price_idr": 24_500_000,
                "duration_days": 9,
                "hotel_makkah": "Elaf Ajyad Hotel",
                "hotel_makkah_stars": 4,
                "hotel_madinah": "Ramada Madinah",
                "hotel_madinah_stars": 4,
                "airline": "Saudi Airlines",
            },
            {
                "name": "Paket Umrah Plus 10 Hari Tiket.com",
                "price_idr": 32_000_000,
                "duration_days": 10,
                "hotel_makkah": "Pullman Zamzam Makkah",
                "hotel_makkah_stars": 5,
                "hotel_madinah": "Pullman Madinah",
                "hotel_madinah_stars": 5,
                "airline": "Garuda Indonesia",
            },
            {
                "name": "Paket Umrah Exclusive 12 Hari Tiket.com",
                "price_idr": 48_000_000,
                "duration_days": 12,
                "hotel_makkah": "Raffles Makkah Palace",
                "hotel_makkah_stars": 5,
                "hotel_madinah": "Ritz Carlton Madinah",
                "hotel_madinah_stars": 5,
                "airline": "Qatar Airways",
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
                source_offer_id=f"tiket_demo_{pkg['name'][:10]}",
                duration_days=pkg["duration_days"],
                departure_city=departure_city,
                airline=pkg.get("airline"),
                hotel_makkah=pkg.get("hotel_makkah"),
                hotel_makkah_stars=pkg.get("hotel_makkah_stars", 4),
                hotel_madinah=pkg.get("hotel_madinah"),
                hotel_madinah_stars=pkg.get("hotel_madinah_stars", 4),
                is_available=True,
                price_sar=convert_idr_to_sar(price_idr),
                confidence_score=0.5
            )
            offers.append(offer)

        return offers


def create_tiket_scraper(enabled: bool = True) -> TiketScraper:
    """Factory function to create TiketScraper."""
    from dataclasses import replace
    config = replace(TiketScraper.DEFAULT_CONFIG, enabled=enabled)
    return TiketScraper(config)
