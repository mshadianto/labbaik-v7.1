"""
LABBAIK AI v6.0 - Core Package
==============================
Core business logic, configuration, and utilities.
"""

from core.config import (
    Settings,
    ConfigManager,
    get_config,
    get_settings,
    Environment,
)

from core.constants import (
    APP_NAME,
    APP_VERSION,
    UserRole,
    SubscriptionTier,
    BookingStatus,
    ChatRole,
    UmrahPackageType,
    Limits,
    CostConstants,
    UIConstants,
    Messages,
)

from core.exceptions import (
    LABBAIKException,
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    DatabaseError,
    AIServiceError,
    BookingError,
    PluginError,
    handle_exception,
)

from core.logging_config import (
    setup_logging,
    get_logger,
    init_logging,
    log_execution,
    log_error,
    audit_logger,
    perf_logger,
)

__all__ = [
    # Config
    "Settings",
    "ConfigManager",
    "get_config",
    "get_settings",
    "Environment",
    # Constants
    "APP_NAME",
    "APP_VERSION",
    "UserRole",
    "SubscriptionTier",
    "BookingStatus",
    "ChatRole",
    "UmrahPackageType",
    "Limits",
    "CostConstants",
    "UIConstants",
    "Messages",
    # Exceptions
    "LABBAIKException",
    "AuthenticationError",
    "AuthorizationError",
    "ValidationError",
    "DatabaseError",
    "AIServiceError",
    "BookingError",
    "PluginError",
    "handle_exception",
    # Logging
    "setup_logging",
    "get_logger",
    "init_logging",
    "log_execution",
    "log_error",
    "audit_logger",
    "perf_logger",
]
