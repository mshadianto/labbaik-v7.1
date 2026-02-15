"""
================================================================================
LABBAIK AI - CRM SHARED HELPERS
================================================================================
Shared utility functions used across CRM pages.
Eliminates duplication of format_rupiah, format_date, etc.
================================================================================
"""


def format_rupiah(amount, default="-"):
    """Format amount as Indonesian Rupiah string.

    Args:
        amount: Numeric amount to format, or None.
        default: String to return when amount is None.
    """
    if amount is None:
        return default
    return f"Rp {amount:,.0f}".replace(",", ".")


def format_date(dt, default="-"):
    """Format a date/datetime value for display.

    Handles datetime objects, date strings, and None.

    Args:
        dt: Date value (datetime, str, or None).
        default: String to return when dt is None.
    """
    if dt is None:
        return default
    if isinstance(dt, str):
        return dt[:10]
    return dt.strftime("%d %b %Y")


__all__ = ["format_rupiah", "format_date"]
