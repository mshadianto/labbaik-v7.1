"""
LABBAIK AI - Partner API Endpoints
===================================
REST API endpoint handlers for partner integration.
"""

import json
import secrets
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from services.partner_api.api_service import get_partner_api, APIKey

# Partner commission rate (fraction, e.g. 0.15 = 15%)
PARTNER_COMMISSION_RATE = 0.15

# API Endpoints documentation
API_ENDPOINTS = {
    "packages": {
        "GET /api/v1/packages": {
            "description": "Get all packages",
            "permissions": ["packages:read"],
            "params": {
                "page": "Page number (default: 1)",
                "limit": "Items per page (default: 20, max: 100)",
                "departure_city": "Filter by departure city",
                "min_price": "Minimum price filter",
                "max_price": "Maximum price filter",
            },
            "response": {
                "success": True,
                "data": [],
                "pagination": {"page": 1, "limit": 20, "total": 0}
            }
        },
        "GET /api/v1/packages/{id}": {
            "description": "Get package by ID",
            "permissions": ["packages:read"],
            "response": {"success": True, "data": {}}
        },
        "POST /api/v1/packages": {
            "description": "Create new package",
            "permissions": ["packages:write"],
            "body": {
                "name": "Package name (required)",
                "description": "Package description",
                "price": "Price in IDR (required)",
                "duration_days": "Duration in days",
                "departure_city": "Departure city",
                "departure_dates": "List of departure dates",
                "hotel_makkah": "Hotel name in Makkah",
                "hotel_madinah": "Hotel name in Madinah",
                "airline": "Airline name",
                "inclusions": "List of inclusions",
                "exclusions": "List of exclusions",
                "quota": "Available quota"
            }
        },
        "PUT /api/v1/packages/{id}": {
            "description": "Update package",
            "permissions": ["packages:write"]
        },
        "DELETE /api/v1/packages/{id}": {
            "description": "Delete package",
            "permissions": ["packages:write"]
        }
    },
    "bookings": {
        "GET /api/v1/bookings": {
            "description": "Get all bookings",
            "permissions": ["bookings:read"],
            "params": {
                "status": "Filter by status (pending, confirmed, completed, cancelled)",
                "from_date": "Filter from date (YYYY-MM-DD)",
                "to_date": "Filter to date (YYYY-MM-DD)"
            }
        },
        "GET /api/v1/bookings/{code}": {
            "description": "Get booking by code",
            "permissions": ["bookings:read"]
        },
        "POST /api/v1/bookings": {
            "description": "Create new booking",
            "permissions": ["bookings:write"],
            "body": {
                "package_id": "Package ID (required)",
                "customer_name": "Customer name (required)",
                "customer_email": "Customer email",
                "customer_phone": "Customer phone (required)",
                "num_pax": "Number of passengers",
                "notes": "Additional notes"
            }
        },
        "PUT /api/v1/bookings/{code}/status": {
            "description": "Update booking status",
            "permissions": ["bookings:write"],
            "body": {"status": "New status"}
        }
    },
    "webhooks": {
        "GET /api/v1/webhooks": {
            "description": "Get configured webhooks",
            "permissions": ["webhooks:read"]
        },
        "POST /api/v1/webhooks": {
            "description": "Create webhook",
            "permissions": ["webhooks:write"],
            "body": {
                "url": "Webhook URL (required)",
                "events": "List of events to subscribe"
            },
            "events": [
                "booking.created",
                "booking.confirmed",
                "booking.cancelled",
                "payment.received",
                "package.updated"
            ]
        },
        "DELETE /api/v1/webhooks/{id}": {
            "description": "Delete webhook",
            "permissions": ["webhooks:write"]
        }
    },
    "analytics": {
        "GET /api/v1/analytics/overview": {
            "description": "Get analytics overview",
            "permissions": ["analytics:read"]
        },
        "GET /api/v1/analytics/bookings": {
            "description": "Get booking analytics",
            "permissions": ["analytics:read"],
            "params": {
                "period": "Time period (7d, 30d, 90d)"
            }
        }
    }
}


@dataclass
class APIResponse:
    """Standard API response"""
    success: bool
    data: Any = None
    error: str = None
    message: str = None
    pagination: Dict = None

    def to_dict(self) -> Dict:
        result = {"success": self.success}
        if self.data is not None:
            result["data"] = self.data
        if self.error:
            result["error"] = self.error
        if self.message:
            result["message"] = self.message
        if self.pagination:
            result["pagination"] = self.pagination
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)


class APIHandler:
    """Handle API requests"""

    def __init__(self, partner_id: int, api_key: APIKey):
        self.partner_id = partner_id
        self.api_key = api_key
        self.api = get_partner_api()

    def _check_permission(self, required: str) -> Optional[APIResponse]:
        """Check if API key has required permission"""
        if not self.api_key.has_permission(required):
            return APIResponse(
                success=False,
                error="permission_denied",
                message=f"API key does not have '{required}' permission"
            )
        return None

    # =========================================================================
    # PACKAGES
    # =========================================================================

    def get_packages(self, params: Dict = None) -> APIResponse:
        """Get all packages for partner"""
        perm_error = self._check_permission("packages:read")
        if perm_error:
            return perm_error

        params = params or {}
        page = int(params.get("page", 1))
        limit = min(int(params.get("limit", 20)), 100)
        offset = (page - 1) * limit

        with self.api._get_connection() as conn:
            cursor = conn.cursor()

            # Build query
            query = "SELECT * FROM partner_packages WHERE partner_id = ? AND is_active = 1"
            query_params = [self.partner_id]

            if params.get("departure_city"):
                query += " AND departure_city = ?"
                query_params.append(params["departure_city"])

            if params.get("min_price"):
                query += " AND price >= ?"
                query_params.append(int(params["min_price"]))

            if params.get("max_price"):
                query += " AND price <= ?"
                query_params.append(int(params["max_price"]))

            # Count total
            count_query = query.replace("SELECT *", "SELECT COUNT(*)")
            cursor.execute(count_query, query_params)
            total = cursor.fetchone()[0]

            # Get data
            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            query_params.extend([limit, offset])
            cursor.execute(query, query_params)

            packages = [dict(row) for row in cursor.fetchall()]

        return APIResponse(
            success=True,
            data=packages,
            pagination={
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit
            }
        )

    def get_package(self, package_id: int) -> APIResponse:
        """Get single package"""
        perm_error = self._check_permission("packages:read")
        if perm_error:
            return perm_error

        with self.api._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM partner_packages
                WHERE id = ? AND partner_id = ?
            """, (package_id, self.partner_id))
            row = cursor.fetchone()

            if not row:
                return APIResponse(success=False, error="not_found", message="Package not found")

            return APIResponse(success=True, data=dict(row))

    def create_package(self, data: Dict) -> APIResponse:
        """Create new package"""
        perm_error = self._check_permission("packages:write")
        if perm_error:
            return perm_error

        # Validate required fields
        required = ["name", "price"]
        for field in required:
            if not data.get(field):
                return APIResponse(success=False, error="validation_error",
                                   message=f"Field '{field}' is required")

        with self.api._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO partner_packages (
                    partner_id, name, description, price, duration_days,
                    departure_city, departure_dates, hotel_makkah, hotel_madinah,
                    airline, inclusions, exclusions, quota
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.partner_id,
                data["name"],
                data.get("description", ""),
                int(data["price"]),
                data.get("duration_days", 9),
                data.get("departure_city", ""),
                json.dumps(data.get("departure_dates", [])),
                data.get("hotel_makkah", ""),
                data.get("hotel_madinah", ""),
                data.get("airline", ""),
                json.dumps(data.get("inclusions", [])),
                json.dumps(data.get("exclusions", [])),
                data.get("quota", 0)
            ))
            conn.commit()

            return APIResponse(
                success=True,
                message="Package created successfully",
                data={"id": cursor.lastrowid}
            )

    def update_package(self, package_id: int, data: Dict) -> APIResponse:
        """Update package"""
        perm_error = self._check_permission("packages:write")
        if perm_error:
            return perm_error

        # Check ownership
        with self.api._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id FROM partner_packages WHERE id = ? AND partner_id = ?
            """, (package_id, self.partner_id))

            if not cursor.fetchone():
                return APIResponse(success=False, error="not_found", message="Package not found")

            # Build update query - only allow whitelisted column names
            ALLOWED_FIELDS = frozenset([
                "name", "description", "price", "duration_days",
                "departure_city", "hotel_makkah", "hotel_madinah",
                "airline", "quota", "is_active",
            ])

            updates = []
            params = []

            import re
            _SAFE_IDENT = re.compile(r"^[a-z_][a-z0-9_]*$")
            for field_name in ALLOWED_FIELDS:
                if field_name in data:
                    if not _SAFE_IDENT.match(field_name):
                        continue
                    updates.append(f"{field_name} = ?")
                    params.append(data[field_name])

            if not updates:
                return APIResponse(success=False, error="validation_error",
                                   message="No valid fields to update")

            updates.append("updated_at = datetime('now')")
            params.extend([package_id, self.partner_id])

            set_clause = ", ".join(updates)
            cursor.execute(
                f"UPDATE partner_packages SET {set_clause} WHERE id = ? AND partner_id = ?",
                params,
            )
            conn.commit()

            return APIResponse(success=True, message="Package updated successfully")

    def delete_package(self, package_id: int) -> APIResponse:
        """Delete (deactivate) package"""
        perm_error = self._check_permission("packages:write")
        if perm_error:
            return perm_error

        with self.api._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE partner_packages SET is_active = 0, updated_at = datetime('now')
                WHERE id = ? AND partner_id = ?
            """, (package_id, self.partner_id))
            conn.commit()

            if cursor.rowcount == 0:
                return APIResponse(success=False, error="not_found", message="Package not found")

            return APIResponse(success=True, message="Package deleted successfully")

    # =========================================================================
    # BOOKINGS
    # =========================================================================

    def get_bookings(self, params: Dict = None) -> APIResponse:
        """Get all bookings"""
        perm_error = self._check_permission("bookings:read")
        if perm_error:
            return perm_error

        params = params or {}

        with self.api._get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT b.*, p.name as package_name
                FROM partner_bookings b
                LEFT JOIN partner_packages p ON b.package_id = p.id
                WHERE b.partner_id = ?
            """
            query_params = [self.partner_id]

            if params.get("status"):
                query += " AND b.status = ?"
                query_params.append(params["status"])

            if params.get("from_date"):
                query += " AND DATE(b.created_at) >= ?"
                query_params.append(params["from_date"])

            if params.get("to_date"):
                query += " AND DATE(b.created_at) <= ?"
                query_params.append(params["to_date"])

            query += " ORDER BY b.created_at DESC LIMIT 100"
            cursor.execute(query, query_params)

            bookings = [dict(row) for row in cursor.fetchall()]

            return APIResponse(success=True, data=bookings)

    def get_booking(self, booking_code: str) -> APIResponse:
        """Get single booking by code"""
        perm_error = self._check_permission("bookings:read")
        if perm_error:
            return perm_error

        with self.api._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT b.*, p.name as package_name
                FROM partner_bookings b
                LEFT JOIN partner_packages p ON b.package_id = p.id
                WHERE b.booking_code = ? AND b.partner_id = ?
            """, (booking_code, self.partner_id))
            row = cursor.fetchone()

            if not row:
                return APIResponse(success=False, error="not_found", message="Booking not found")

            return APIResponse(success=True, data=dict(row))

    def create_booking(self, data: Dict) -> APIResponse:
        """Create new booking"""
        perm_error = self._check_permission("bookings:write")
        if perm_error:
            return perm_error

        required = ["package_id", "customer_name", "customer_phone"]
        for field in required:
            if not data.get(field):
                return APIResponse(success=False, error="validation_error",
                                   message=f"Field '{field}' is required")

        with self.api._get_connection() as conn:
            cursor = conn.cursor()

            # Verify package exists and belongs to partner
            cursor.execute("""
                SELECT id, price, quota, booked FROM partner_packages
                WHERE id = ? AND partner_id = ? AND is_active = 1
            """, (data["package_id"], self.partner_id))
            package = cursor.fetchone()

            if not package:
                return APIResponse(success=False, error="not_found", message="Package not found")

            # Check quota
            num_pax = int(data.get("num_pax", 1))
            if package["quota"] > 0 and package["booked"] + num_pax > package["quota"]:
                return APIResponse(success=False, error="quota_exceeded",
                                   message="Not enough quota available")

            # Generate booking code
            booking_code = f"LBK-{secrets.token_hex(4).upper()}"

            # Calculate price and commission
            total_price = package["price"] * num_pax
            commission_amount = int(total_price * PARTNER_COMMISSION_RATE)

            cursor.execute("""
                INSERT INTO partner_bookings (
                    booking_code, partner_id, package_id,
                    customer_name, customer_email, customer_phone,
                    num_pax, total_price, commission_amount, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                booking_code, self.partner_id, data["package_id"],
                data["customer_name"], data.get("customer_email", ""),
                data["customer_phone"], num_pax,
                total_price, commission_amount, data.get("notes", "")
            ))

            # Update package booked count
            cursor.execute("""
                UPDATE partner_packages SET booked = booked + ?
                WHERE id = ?
            """, (num_pax, data["package_id"]))

            conn.commit()

            return APIResponse(
                success=True,
                message="Booking created successfully",
                data={
                    "booking_code": booking_code,
                    "total_price": total_price,
                    "commission_amount": commission_amount
                }
            )

    def update_booking_status(self, booking_code: str, status: str) -> APIResponse:
        """Update booking status"""
        perm_error = self._check_permission("bookings:write")
        if perm_error:
            return perm_error

        valid_statuses = ["pending", "confirmed", "completed", "cancelled"]
        if status not in valid_statuses:
            return APIResponse(success=False, error="validation_error",
                               message=f"Invalid status. Must be one of: {valid_statuses}")

        with self.api._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE partner_bookings
                SET status = ?, updated_at = datetime('now')
                WHERE booking_code = ? AND partner_id = ?
            """, (status, booking_code, self.partner_id))
            conn.commit()

            if cursor.rowcount == 0:
                return APIResponse(success=False, error="not_found", message="Booking not found")

            return APIResponse(success=True, message=f"Booking status updated to '{status}'")

    # =========================================================================
    # ANALYTICS
    # =========================================================================

    def get_analytics_overview(self) -> APIResponse:
        """Get analytics overview"""
        perm_error = self._check_permission("analytics:read")
        if perm_error:
            return perm_error

        with self.api._get_connection() as conn:
            cursor = conn.cursor()

            stats = {}

            # Total packages
            cursor.execute("""
                SELECT COUNT(*) FROM partner_packages
                WHERE partner_id = ? AND is_active = 1
            """, (self.partner_id,))
            stats["total_packages"] = cursor.fetchone()[0]

            # Total bookings
            cursor.execute("""
                SELECT COUNT(*) FROM partner_bookings WHERE partner_id = ?
            """, (self.partner_id,))
            stats["total_bookings"] = cursor.fetchone()[0]

            # Bookings by status
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM partner_bookings
                WHERE partner_id = ?
                GROUP BY status
            """, (self.partner_id,))
            stats["bookings_by_status"] = {row["status"]: row["count"] for row in cursor.fetchall()}

            # Total revenue
            cursor.execute("""
                SELECT COALESCE(SUM(total_price), 0) FROM partner_bookings
                WHERE partner_id = ? AND status IN ('confirmed', 'completed')
            """, (self.partner_id,))
            stats["total_revenue"] = cursor.fetchone()[0]

            # Total commission
            cursor.execute("""
                SELECT COALESCE(SUM(commission_amount), 0) FROM partner_bookings
                WHERE partner_id = ? AND status IN ('confirmed', 'completed')
            """, (self.partner_id,))
            stats["total_commission"] = cursor.fetchone()[0]

            # This month
            cursor.execute("""
                SELECT
                    COUNT(*) as bookings,
                    COALESCE(SUM(total_price), 0) as revenue,
                    COALESCE(SUM(commission_amount), 0) as commission
                FROM partner_bookings
                WHERE partner_id = ?
                AND strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')
            """, (self.partner_id,))
            row = cursor.fetchone()
            stats["this_month"] = {
                "bookings": row["bookings"],
                "revenue": row["revenue"],
                "commission": row["commission"]
            }

            return APIResponse(success=True, data=stats)


def handle_api_request(
    api_key: str,
    endpoint: str,
    method: str = "GET",
    data: Dict = None,
    params: Dict = None
) -> APIResponse:
    """
    Main entry point for handling API requests.

    Args:
        api_key: API key string
        endpoint: API endpoint (e.g., "/api/v1/packages")
        method: HTTP method
        data: Request body data
        params: Query parameters

    Returns:
        APIResponse object
    """
    api = get_partner_api()

    # Validate API key
    is_valid, error, key_obj = api.validate_api_key(api_key)
    if not is_valid:
        return APIResponse(success=False, error="unauthorized", message=error)

    # Create handler
    handler = APIHandler(key_obj.partner_id, key_obj)

    # Route request
    endpoint = endpoint.lower().strip("/")

    try:
        # Packages
        if endpoint == "api/v1/packages":
            if method == "GET":
                return handler.get_packages(params)
            elif method == "POST":
                return handler.create_package(data or {})

        elif endpoint.startswith("api/v1/packages/"):
            package_id = int(endpoint.split("/")[-1])
            if method == "GET":
                return handler.get_package(package_id)
            elif method == "PUT":
                return handler.update_package(package_id, data or {})
            elif method == "DELETE":
                return handler.delete_package(package_id)

        # Bookings
        elif endpoint == "api/v1/bookings":
            if method == "GET":
                return handler.get_bookings(params)
            elif method == "POST":
                return handler.create_booking(data or {})

        elif endpoint.startswith("api/v1/bookings/"):
            parts = endpoint.split("/")
            booking_code = parts[3]

            if len(parts) == 4:
                if method == "GET":
                    return handler.get_booking(booking_code)

            elif len(parts) == 5 and parts[4] == "status":
                if method == "PUT":
                    return handler.update_booking_status(booking_code, data.get("status", ""))

        # Analytics
        elif endpoint == "api/v1/analytics/overview":
            if method == "GET":
                return handler.get_analytics_overview()

        # Not found
        return APIResponse(success=False, error="not_found", message="Endpoint not found")

    except Exception as e:
        return APIResponse(success=False, error="internal_error", message=str(e))
