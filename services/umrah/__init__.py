"""
LABBAIK AI v6.0 - Umrah Data Services
======================================
Hybrid data fetching for hotels, transport, and pricing.
"""

from services.umrah.data_fetcher import (
    HybridUmrahDataManager,
    HotelOffer,
    TransportOption,
    DataSource,
    LocationService,
    TransportService,
)

from services.umrah.cost_integration import (
    CostIntegrationService,
    LivePriceResult,
    get_cost_integration_service,
)

__all__ = [
    # Data fetcher
    "HybridUmrahDataManager",
    "HotelOffer",
    "TransportOption",
    "DataSource",
    "LocationService",
    "TransportService",
    "get_umrah_data_manager",
    # Cost integration
    "CostIntegrationService",
    "LivePriceResult",
    "get_cost_integration_service",
]


# Singleton instance
_manager_instance = None


def get_umrah_data_manager() -> HybridUmrahDataManager:
    """
    Get singleton instance of HybridUmrahDataManager.
    Configured from environment/Streamlit secrets.
    """
    global _manager_instance

    if _manager_instance is None:
        import os

        # Try to get API keys from environment or Streamlit secrets
        amadeus_key = None
        amadeus_secret = None
        rapidapi_key = None

        # Try environment variables
        amadeus_key = os.getenv("AMADEUS_API_KEY")
        amadeus_secret = os.getenv("AMADEUS_API_SECRET")
        rapidapi_key = os.getenv("RAPIDAPI_KEY")

        # Try Streamlit secrets
        if not amadeus_key:
            try:
                import streamlit as st
                if hasattr(st, 'secrets'):
                    amadeus_key = st.secrets.get("AMADEUS_API_KEY")
                    amadeus_secret = st.secrets.get("AMADEUS_API_SECRET")
                    rapidapi_key = st.secrets.get("RAPIDAPI_KEY")
            except Exception:
                pass

        _manager_instance = HybridUmrahDataManager(
            amadeus_key=amadeus_key,
            amadeus_secret=amadeus_secret,
            rapidapi_key=rapidapi_key,
            use_nusuk_scraping=True,
            use_cache=True,
        )

    return _manager_instance
