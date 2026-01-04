"""
LABBAIK AI v7.1 - Hotel Services
================================
Hotel price aggregation and comparison services.
"""

from services.hotel.makcorps import (
    MakcorpsClient,
    MakcorpsHotel,
    HotelSearchResult,
    get_makcorps_client,
    search_umrah_hotels,
    CITY_IDS,
)

__all__ = [
    'MakcorpsClient',
    'MakcorpsHotel',
    'HotelSearchResult',
    'get_makcorps_client',
    'search_umrah_hotels',
    'CITY_IDS',
]
