"""
LABBAIK Smart Planner - Dynamic Version Management
===================================================
Centralized version control for the entire application.
"""

from typing import Dict, Any

# =============================================================================
# VERSION INFO
# =============================================================================

MAJOR = 7
MINOR = 1
PATCH = 1
RELEASE_TYPE = "stable"  # stable, beta, alpha, dev

# Build info
BUILD_DATE = "2026-01-03"
BUILD_NUMBER = 1

# =============================================================================
# VERSION STRINGS
# =============================================================================

def get_version() -> str:
    """Get semantic version string."""
    return f"{MAJOR}.{MINOR}.{PATCH}"


def get_full_version() -> str:
    """Get full version with release type."""
    version = get_version()
    if RELEASE_TYPE != "stable":
        version += f"-{RELEASE_TYPE}"
    return version


def get_display_version() -> str:
    """Get version for display in UI."""
    return f"v{get_version()}"


def get_version_info() -> Dict[str, Any]:
    """Get complete version information."""
    return {
        "version": get_version(),
        "full_version": get_full_version(),
        "display_version": get_display_version(),
        "major": MAJOR,
        "minor": MINOR,
        "patch": PATCH,
        "release_type": RELEASE_TYPE,
        "build_date": BUILD_DATE,
        "build_number": BUILD_NUMBER,
        "app_name": "LABBAIK Smart Planner",
        "tagline": "Satu-satunya AI Companion untuk Umrah Anda",
    }


# =============================================================================
# VERSION CONSTANTS (for backward compatibility)
# =============================================================================

APP_VERSION = get_version()
APP_FULL_VERSION = get_full_version()
APP_DISPLAY_VERSION = get_display_version()
APP_NAME = "LABBAIK Smart Planner"
APP_TAGLINE = "Satu-satunya AI Companion untuk Umrah Anda"


# =============================================================================
# CHANGELOG
# =============================================================================

CHANGELOG = [
    {
        "version": "7.1.1",
        "date": "2026-01-03",
        "changes": [
            "Premium brand refresh: LABBAIK Smart Planner",
            "New Smart Pillars: Smart Prep, Smart Savings, Smart Journey",
            "Updated tagline: Satu-satunya AI Companion untuk Umrah Anda",
            "Refined UI messaging with premium positioning",
            "3-Pillar navigation refactored to Smart Planner framework",
        ]
    },
    {
        "version": "7.1.0",
        "date": "2026-01-02",
        "changes": [
            "3-Pillar sidebar navigation structure",
            "Smart nudge in Budget Optimizer for Umrah Bareng",
            "Domain migration to labbaik.io",
            "GLM-4 (Zhipu AI) integration for chat",
            "Live price updates for Umrah packages",
            "Scenario planning with Monte Carlo simulation",
            "WhatsApp bot integration",
            "Enhanced Umrah guide from official Saudi Ministry",
            "Dynamic version management",
        ]
    },
    {
        "version": "7.0.0",
        "date": "2025-12-26",
        "changes": [
            "Role-based access control for all pages and features",
            "Premium subscription system with multiple plans",
            "Referral system for viral growth with rewards",
            "Chat rate limiting based on user role",
            "User registration and login system",
            "User access levels (Guest, Free, Premium, Partner, Admin)",
            "User analytics dashboard for tracking potential customers",
            "Complete Umrah guide with 20+ doas",
            "Audio doa with male/female Arabic voices",
        ]
    },
    {
        "version": "6.0.0",
        "date": "2024-12-20",
        "changes": [
            "PWA support for offline access",
            "SOS emergency system",
            "Group tracking feature",
            "Crowd prediction widget",
            "Smart package comparison",
            "Ecosystem strategy and API specification",
            "Historical sites database",
        ]
    },
]


def get_latest_changelog() -> Dict[str, Any]:
    """Get the latest changelog entry."""
    return CHANGELOG[0] if CHANGELOG else {}


def get_all_changelogs() -> list:
    """Get all changelog entries."""
    return CHANGELOG


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "MAJOR",
    "MINOR",
    "PATCH",
    "RELEASE_TYPE",
    "BUILD_DATE",
    "BUILD_NUMBER",
    "APP_VERSION",
    "APP_FULL_VERSION",
    "APP_DISPLAY_VERSION",
    "APP_NAME",
    "APP_TAGLINE",
    "get_version",
    "get_full_version",
    "get_display_version",
    "get_version_info",
    "get_latest_changelog",
    "get_all_changelogs",
    "CHANGELOG",
]
