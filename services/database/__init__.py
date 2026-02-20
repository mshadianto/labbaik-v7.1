"""
LABBAIK AI v6.0 - Database Services Package
============================================
Database connection and repository classes.
"""

from services.database.repository import (
    DatabaseConnection,
    get_db,
    BaseRepository,
    UserRepository,
    ChatRepository,
    BookingRepository,
)

# Alias for backward compatibility (used by CRM, price_aggregation, seed_loader)
get_db_connection = get_db

__all__ = [
    'DatabaseConnection',
    'get_db',
    'get_db_connection',
    'BaseRepository',
    'UserRepository',
    'ChatRepository',
    'BookingRepository',
]
