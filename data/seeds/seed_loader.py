"""
LABBAIK AI - Seed Data Loader
=============================
Script to load test datasets into the database.

Usage:
    python -m data.seeds.seed_loader --all
    python -m data.seeds.seed_loader --packages
    python -m data.seeds.seed_loader --hotels
    python -m data.seeds.seed_loader --flights
    python -m data.seeds.seed_loader --agents
    python -m data.seeds.seed_loader --users
    python -m data.seeds.seed_loader --faq
"""

import json
import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Seed files directory
SEEDS_DIR = Path(__file__).parent


def load_json(filename: str) -> Dict[str, Any]:
    """Load JSON file from seeds directory."""
    filepath = SEEDS_DIR / filename
    if not filepath.exists():
        logger.error(f"File not found: {filepath}")
        return {}

    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_db_connection():
    """Get database connection."""
    try:
        from services.database import get_db_connection
        return get_db_connection()
    except Exception as e:
        logger.error(f"Failed to get database connection: {e}")
        return None


class SeedLoader:
    """Load seed data into database."""

    def __init__(self, db=None):
        self.db = db or get_db_connection()
        self.stats = {
            "packages": 0,
            "hotels": 0,
            "flights": 0,
            "agents": 0,
            "users": 0,
            "faq": 0
        }

    def load_all(self) -> Dict[str, int]:
        """Load all seed data."""
        logger.info("Loading all seed data...")

        self.load_packages()
        self.load_hotels()
        self.load_flights()
        self.load_travel_agents()
        self.load_users()
        self.load_faq()

        logger.info(f"Seed loading complete: {self.stats}")
        return self.stats

    def load_packages(self) -> int:
        """Load Umrah packages."""
        logger.info("Loading Umrah packages...")
        data = load_json("umrah_packages.json")

        if not data or "packages" not in data:
            logger.warning("No packages data found")
            return 0

        packages = data["packages"]
        count = 0

        if self.db:
            try:
                cursor = self.db.cursor()
                try:
                    for pkg in packages:
                        # Insert into prices_packages table (n8n format)
                        try:
                            cursor.execute("""
                                INSERT INTO prices_packages (
                                    id, source_id, package_name, price_idr,
                                    duration_days, departure_city, airline,
                                    hotel_makkah, hotel_makkah_stars,
                                    hotel_madinah, hotel_madinah_stars,
                                    includes, is_available, source_url, scraped_at
                                ) VALUES (
                                    gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                                )
                                ON CONFLICT DO NOTHING
                            """, (
                                pkg.get("travel_agent_id", "demo"),
                                pkg["name"],
                                pkg["price_idr"],
                                pkg["duration_days"],
                                pkg["departure_city"],
                                pkg.get("airline"),
                                pkg.get("hotel_makkah", {}).get("name") if isinstance(pkg.get("hotel_makkah"), dict) else pkg.get("hotel_makkah"),
                                pkg.get("hotel_makkah", {}).get("stars", 4) if isinstance(pkg.get("hotel_makkah"), dict) else 4,
                                pkg.get("hotel_madinah", {}).get("name") if isinstance(pkg.get("hotel_madinah"), dict) else pkg.get("hotel_madinah"),
                                pkg.get("hotel_madinah", {}).get("stars", 4) if isinstance(pkg.get("hotel_madinah"), dict) else 4,
                                json.dumps(pkg.get("inclusions", [])),
                                pkg.get("is_available", True),
                                f"https://labbaik.ai/packages/{pkg['id']}"
                            ))
                            count += 1
                        except Exception as e:
                            logger.warning(f"Failed to insert package {pkg['id']}: {e}")

                    self.db.commit()
                finally:
                    cursor.close()

            except Exception as e:
                logger.error(f"Database error loading packages: {e}")
        else:
            count = len(packages)

        self.stats["packages"] = count
        logger.info(f"Loaded {count} packages")
        return count

    def load_hotels(self) -> int:
        """Load hotels."""
        logger.info("Loading hotels...")
        data = load_json("hotels.json")

        if not data or "hotels" not in data:
            logger.warning("No hotels data found")
            return 0

        hotels = data["hotels"]
        count = 0

        if self.db:
            try:
                cursor = self.db.cursor()
                try:
                    for hotel in hotels:
                        # Get first room type price
                        room_types = hotel.get("room_types", [])
                        price = room_types[0]["price_per_night_idr"] if room_types else 1000000

                        try:
                            cursor.execute("""
                                INSERT INTO prices_hotels (
                                    id, source_id, hotel_name, city, star_rating,
                                    distance_to_haram, distance_meters, rating_score,
                                    room_type, room_capacity, price_per_night_idr,
                                    includes_breakfast, meal_plan, is_available,
                                    view_type, source_url, scraped_at
                                ) VALUES (
                                    gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                                )
                                ON CONFLICT DO NOTHING
                            """, (
                                "seed-data",
                                hotel["name"],
                                hotel["city"],
                                hotel["stars"],
                                f"{hotel['distance_to_haram_m']}m",
                                hotel["distance_to_haram_m"],
                                hotel.get("rating", 4.5),
                                room_types[0]["type"] if room_types else "Standard",
                                room_types[0]["capacity"] if room_types else 2,
                                price,
                                "breakfast" in str(hotel.get("amenities", [])).lower(),
                                "breakfast",
                                hotel.get("is_available", True),
                                room_types[0].get("view", "city") if room_types else "city",
                                f"https://labbaik.ai/hotels/{hotel['id']}"
                            ))
                            count += 1
                        except Exception as e:
                            logger.warning(f"Failed to insert hotel {hotel['id']}: {e}")

                    self.db.commit()
                finally:
                    cursor.close()

            except Exception as e:
                logger.error(f"Database error loading hotels: {e}")
        else:
            count = len(hotels)

        self.stats["hotels"] = count
        logger.info(f"Loaded {count} hotels")
        return count

    def load_flights(self) -> int:
        """Load flights."""
        logger.info("Loading flights...")
        data = load_json("flights.json")

        if not data or "flights" not in data:
            logger.warning("No flights data found")
            return 0

        flights = data["flights"]
        count = 0

        if self.db:
            try:
                cursor = self.db.cursor()
                try:
                    for flight in flights:
                        try:
                            cursor.execute("""
                                INSERT INTO prices_flights (
                                    id, source_id, airline, airline_code, flight_code,
                                    origin_city, origin_airport, destination_city, destination_airport,
                                    departure_date, departure_time, arrival_time,
                                    duration_minutes, is_direct, transit_cities,
                                    price_idr, ticket_class, fare_type,
                                    is_available, source_url, scraped_at
                                ) VALUES (
                                    gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                                )
                                ON CONFLICT DO NOTHING
                            """, (
                                "seed-data",
                                flight["airline"],
                                flight["airline_code"],
                                flight["flight_number"],
                                flight["origin_city"],
                                flight["origin_airport"],
                                flight["destination_city"],
                                flight["destination_airport"],
                                flight.get("departure_dates", ["2025-03-15"])[0],
                                flight["departure_time"],
                                flight["arrival_time"],
                                flight["duration_minutes"],
                                flight["is_direct"],
                                json.dumps(flight.get("transit_cities", [])) if flight.get("transit_cities") else None,
                                flight["price_economy_idr"],
                                "economy",
                                "estimated",
                                flight.get("is_available", True),
                                f"https://labbaik.ai/flights/{flight['id']}"
                            ))
                            count += 1
                        except Exception as e:
                            logger.warning(f"Failed to insert flight {flight['id']}: {e}")

                    self.db.commit()
                finally:
                    cursor.close()

            except Exception as e:
                logger.error(f"Database error loading flights: {e}")
        else:
            count = len(flights)

        self.stats["flights"] = count
        logger.info(f"Loaded {count} flights")
        return count

    def load_travel_agents(self) -> int:
        """Load travel agents."""
        logger.info("Loading travel agents...")
        data = load_json("travel_agents.json")

        if not data or "travel_agents" not in data:
            logger.warning("No travel agents data found")
            return 0

        agents = data["travel_agents"]
        count = len(agents)

        # Note: Travel agents would be loaded into a partners table
        # For now, just count them

        self.stats["agents"] = count
        logger.info(f"Loaded {count} travel agents (to memory)")
        return count

    def load_users(self) -> int:
        """Load test users."""
        logger.info("Loading test users...")
        data = load_json("users.json")

        if not data or "users" not in data:
            logger.warning("No users data found")
            return 0

        users = data["users"]
        count = len(users)

        # Note: Users would be loaded with proper authentication
        # For now, just count them

        self.stats["users"] = count
        logger.info(f"Loaded {count} users (to memory)")
        return count

    def load_faq(self) -> int:
        """Load FAQ & knowledge base."""
        logger.info("Loading FAQ & knowledge base...")
        data = load_json("faq_knowledge.json")

        if not data or "faqs" not in data:
            logger.warning("No FAQ data found")
            return 0

        faqs = data["faqs"]
        count = len(faqs)

        # Note: FAQs would be loaded into knowledge base / vector store
        # For now, just count them

        self.stats["faq"] = count
        logger.info(f"Loaded {count} FAQs (to memory)")
        return count

    def get_summary(self) -> str:
        """Get summary of loaded data."""
        return f"""
=== Seed Data Summary ===
Packages: {self.stats['packages']}
Hotels: {self.stats['hotels']}
Flights: {self.stats['flights']}
Travel Agents: {self.stats['agents']}
Users: {self.stats['users']}
FAQs: {self.stats['faq']}
========================
Total: {sum(self.stats.values())} records
"""


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Load seed data into database")
    parser.add_argument("--all", action="store_true", help="Load all seed data")
    parser.add_argument("--packages", action="store_true", help="Load packages")
    parser.add_argument("--hotels", action="store_true", help="Load hotels")
    parser.add_argument("--flights", action="store_true", help="Load flights")
    parser.add_argument("--agents", action="store_true", help="Load travel agents")
    parser.add_argument("--users", action="store_true", help="Load users")
    parser.add_argument("--faq", action="store_true", help="Load FAQ")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually write to DB")

    args = parser.parse_args()

    # If no specific option, load all
    if not any([args.all, args.packages, args.hotels, args.flights,
                args.agents, args.users, args.faq]):
        args.all = True

    loader = SeedLoader(db=None if args.dry_run else get_db_connection())

    if args.all:
        loader.load_all()
    else:
        if args.packages:
            loader.load_packages()
        if args.hotels:
            loader.load_hotels()
        if args.flights:
            loader.load_flights()
        if args.agents:
            loader.load_travel_agents()
        if args.users:
            loader.load_users()
        if args.faq:
            loader.load_faq()

    print(loader.get_summary())


if __name__ == "__main__":
    main()
