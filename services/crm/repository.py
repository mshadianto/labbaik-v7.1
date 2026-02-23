"""
LABBAIK AI - CRM Repository
============================
Database operations for CRM entities.
"""

import logging
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import asdict
import json

from .models import (
    Lead, LeadActivity, Jamaah, Booking, Payment,
    Document, Quote, Invoice, Broadcast, CompetitorPrice, CRMStats
)
from .security import (
    validate_column_names, validate_uuid,
    ALLOWED_LEAD_COLUMNS, ALLOWED_JAMAAH_COLUMNS,
    ALLOWED_BOOKING_COLUMNS, ALLOWED_DOCUMENT_COLUMNS,
    sanitize_for_logging
)

logger = logging.getLogger(__name__)


def get_db():
    """Get database connection."""
    try:
        from services.database.repository import DatabaseConnection
        return DatabaseConnection()
    except Exception as e:
        logger.error(f"Failed to get database: {e}")
        return None


class CRMRepository:
    """Repository for CRM database operations."""

    def __init__(self):
        self.db = get_db()

    def _execute(self, query: str, params: tuple = None) -> Optional[List[Dict]]:
        """Execute query and return results as list of dicts."""
        if not self.db:
            logger.error("Database not available")
            return None
        try:
            return self.db.fetch_all(query, params)
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return None

    def _execute_write(self, query: str, params: tuple = None) -> int:
        """Execute write query (INSERT/UPDATE/DELETE) and return affected rows."""
        if not self.db:
            logger.error("Database not available")
            return 0
        try:
            return self.db.execute(query, params)
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return 0

    def _execute_one(self, query: str, params: tuple = None) -> Optional[Dict]:
        """Execute query and return single result."""
        if not self.db:
            logger.error("Database not available")
            return None
        try:
            return self.db.fetch_one(query, params)
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return None

    # =========================================================================
    # LEADS
    # =========================================================================

    def create_lead(self, lead: Lead) -> Optional[str]:
        """Create a new lead."""
        query = """
            INSERT INTO leads (
                name, phone, email, whatsapp, source, status, priority,
                interested_package, budget_min, budget_max, preferred_month,
                group_size, notes, next_followup_date
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        result = self._execute_one(query, (
            lead.name, lead.phone, lead.email, lead.whatsapp,
            lead.source, lead.status, lead.priority,
            lead.interested_package, lead.budget_min, lead.budget_max,
            lead.preferred_month, lead.group_size, lead.notes,
            lead.next_followup_date
        ))
        return result.get("id") if result else None

    def get_lead(self, lead_id: str) -> Optional[Lead]:
        """Get lead by ID."""
        query = "SELECT * FROM leads WHERE id = %s"
        result = self._execute_one(query, (lead_id,))
        if result:
            return Lead(**result)
        return None

    def get_leads(
        self,
        status: Optional[str] = None,
        source: Optional[str] = None,
        priority: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Lead]:
        """Get leads with filters."""
        conditions = []
        params = []

        if status:
            conditions.append("status = %s")
            params.append(status)
        if source:
            conditions.append("source = %s")
            params.append(source)
        if priority:
            conditions.append("priority = %s")
            params.append(priority)
        if search:
            conditions.append("(name ILIKE %s OR phone ILIKE %s)")
            params.extend([f"%{search}%", f"%{search}%"])

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        params.extend([limit, offset])

        query = f"""
            SELECT * FROM leads
            WHERE {where_clause}
            ORDER BY
                CASE priority
                    WHEN 'urgent' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    ELSE 4
                END,
                created_at DESC
            LIMIT %s OFFSET %s
        """
        results = self._execute(query, tuple(params)) or []
        return [Lead(**r) for r in results]

    def update_lead(self, lead_id: str, updates: Dict[str, Any]) -> bool:
        """Update lead with SQL injection prevention."""
        if not updates:
            return False

        # Validate column names against whitelist (SQL injection prevention)
        safe_updates = validate_column_names(updates, ALLOWED_LEAD_COLUMNS)
        if not safe_updates:
            logger.warning(f"No valid columns to update for lead {lead_id}")
            return False

        set_clause = ", ".join([f"{k} = %s" for k in safe_updates.keys()])
        params = list(safe_updates.values()) + [lead_id]

        query = f"UPDATE leads SET {set_clause}, updated_at = NOW() WHERE id = %s"
        self._execute_write(query, tuple(params))
        return True

    def update_lead_status(self, lead_id: str, status: str) -> bool:
        """Update lead status."""
        return self.update_lead(lead_id, {"status": status})

    def get_leads_for_followup(self, days_ahead: int = 1) -> List[Lead]:
        """Get leads needing follow-up."""
        target_date = date.today() + timedelta(days=days_ahead)
        query = """
            SELECT * FROM leads
            WHERE next_followup_date <= %s
            AND status NOT IN ('won', 'lost')
            ORDER BY next_followup_date, priority DESC
        """
        results = self._execute(query, (target_date,)) or []
        return [Lead(**r) for r in results]

    def count_leads_by_status(self) -> Dict[str, int]:
        """Count leads by status."""
        query = """
            SELECT status, COUNT(*) as count
            FROM leads
            GROUP BY status
        """
        results = self._execute(query) or []
        return {r["status"]: r["count"] for r in results}

    # =========================================================================
    # LEAD ACTIVITIES
    # =========================================================================

    def create_activity(self, activity: LeadActivity) -> Optional[str]:
        """Create lead activity."""
        query = """
            INSERT INTO lead_activities (lead_id, activity_type, description, outcome)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """
        result = self._execute_one(query, (
            activity.lead_id, activity.activity_type,
            activity.description, activity.outcome
        ))

        # Update last contact date
        if result:
            self.update_lead(activity.lead_id, {"last_contact_date": datetime.now()})

        return result.get("id") if result else None

    def get_lead_activities(self, lead_id: str, limit: int = 20) -> List[LeadActivity]:
        """Get activities for a lead."""
        query = """
            SELECT * FROM lead_activities
            WHERE lead_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """
        results = self._execute(query, (lead_id, limit)) or []
        return [LeadActivity(**r) for r in results]

    # =========================================================================
    # JAMAAH
    # =========================================================================

    def create_jamaah(self, jamaah: Jamaah) -> Optional[str]:
        """Create new jamaah."""
        query = """
            INSERT INTO jamaah (
                full_name, nik, passport_number, passport_expiry,
                phone, whatsapp, email, address, city, province,
                birth_date, birth_place, gender, blood_type,
                emergency_name, emergency_phone, emergency_relation,
                health_notes, special_needs, referred_by
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        result = self._execute_one(query, (
            jamaah.full_name, jamaah.nik, jamaah.passport_number, jamaah.passport_expiry,
            jamaah.phone, jamaah.whatsapp, jamaah.email, jamaah.address,
            jamaah.city, jamaah.province, jamaah.birth_date, jamaah.birth_place,
            jamaah.gender, jamaah.blood_type, jamaah.emergency_name,
            jamaah.emergency_phone, jamaah.emergency_relation,
            jamaah.health_notes, jamaah.special_needs, jamaah.referred_by
        ))
        return result.get("id") if result else None

    def get_jamaah(self, jamaah_id: str) -> Optional[Jamaah]:
        """Get jamaah by ID."""
        query = "SELECT * FROM jamaah WHERE id = %s"
        result = self._execute_one(query, (jamaah_id,))
        if result:
            return Jamaah(**result)
        return None

    def get_jamaah_list(
        self,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Jamaah]:
        """Get jamaah list with optional search."""
        if search:
            query = """
                SELECT * FROM jamaah
                WHERE full_name ILIKE %s OR phone ILIKE %s OR passport_number ILIKE %s
                ORDER BY full_name
                LIMIT %s OFFSET %s
            """
            params = (f"%{search}%", f"%{search}%", f"%{search}%", limit, offset)
        else:
            query = "SELECT * FROM jamaah ORDER BY full_name LIMIT %s OFFSET %s"
            params = (limit, offset)

        results = self._execute(query, params) or []
        return [Jamaah(**r) for r in results]

    def update_jamaah(self, jamaah_id: str, updates: Dict[str, Any]) -> bool:
        """Update jamaah with SQL injection prevention."""
        if not updates:
            return False

        # Validate column names against whitelist (SQL injection prevention)
        safe_updates = validate_column_names(updates, ALLOWED_JAMAAH_COLUMNS)
        if not safe_updates:
            logger.warning(f"No valid columns to update for jamaah {jamaah_id}")
            return False

        set_clause = ", ".join([f"{k} = %s" for k in safe_updates.keys()])
        params = list(safe_updates.values()) + [jamaah_id]

        query = f"UPDATE jamaah SET {set_clause}, updated_at = NOW() WHERE id = %s"
        self._execute_write(query, tuple(params))
        return True

    def find_jamaah_by_phone(self, phone: str) -> Optional[Jamaah]:
        """Find jamaah by phone number."""
        query = "SELECT * FROM jamaah WHERE phone = %s OR whatsapp = %s"
        result = self._execute_one(query, (phone, phone))
        if result:
            return Jamaah(**result)
        return None

    # =========================================================================
    # BOOKINGS
    # =========================================================================

    def generate_booking_code(self) -> str:
        """Generate unique booking code."""
        import random
        today = date.today().strftime("%Y%m%d")
        random_part = str(random.randint(1000, 9999))
        return f"LBK{today}{random_part}"

    def create_booking(self, booking: Booking) -> Optional[str]:
        """Create new booking."""
        if not booking.booking_code:
            booking.booking_code = self.generate_booking_code()

        booking.amount_remaining = booking.total_price - booking.amount_paid

        query = """
            INSERT INTO bookings (
                booking_code, lead_id, jamaah_id, package_name, package_type,
                departure_date, return_date, duration_days, package_price,
                discount_amount, discount_reason, total_price, payment_status,
                amount_paid, amount_remaining, status, group_code, room_type,
                roommate_preference, notes, internal_notes
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        result = self._execute_one(query, (
            booking.booking_code, booking.lead_id, booking.jamaah_id,
            booking.package_name, booking.package_type, booking.departure_date,
            booking.return_date, booking.duration_days, booking.package_price,
            booking.discount_amount, booking.discount_reason, booking.total_price,
            booking.payment_status, booking.amount_paid, booking.amount_remaining,
            booking.status, booking.group_code, booking.room_type,
            booking.roommate_preference, booking.notes, booking.internal_notes
        ))
        return result.get("id") if result else None

    def get_booking(self, booking_id: str) -> Optional[Booking]:
        """Get booking by ID."""
        query = "SELECT * FROM bookings WHERE id = %s"
        result = self._execute_one(query, (booking_id,))
        if result:
            return Booking(**result)
        return None

    def get_booking_by_code(self, booking_code: str) -> Optional[Booking]:
        """Get booking by code."""
        query = "SELECT * FROM bookings WHERE booking_code = %s"
        result = self._execute_one(query, (booking_code,))
        if result:
            return Booking(**result)
        return None

    def get_bookings(
        self,
        status: Optional[str] = None,
        payment_status: Optional[str] = None,
        departure_from: Optional[date] = None,
        departure_to: Optional[date] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Booking]:
        """Get bookings with filters."""
        conditions = []
        params = []

        if status:
            conditions.append("status = %s")
            params.append(status)
        if payment_status:
            conditions.append("payment_status = %s")
            params.append(payment_status)
        if departure_from:
            conditions.append("departure_date >= %s")
            params.append(departure_from)
        if departure_to:
            conditions.append("departure_date <= %s")
            params.append(departure_to)

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        params.extend([limit, offset])

        query = f"""
            SELECT * FROM bookings
            WHERE {where_clause}
            ORDER BY departure_date DESC, created_at DESC
            LIMIT %s OFFSET %s
        """
        results = self._execute(query, tuple(params)) or []
        return [Booking(**r) for r in results]

    def update_booking(self, booking_id: str, updates: Dict[str, Any]) -> bool:
        """Update booking with SQL injection prevention."""
        if not updates:
            return False

        # Validate column names against whitelist (SQL injection prevention)
        safe_updates = validate_column_names(updates, ALLOWED_BOOKING_COLUMNS)
        if not safe_updates:
            logger.warning(f"No valid columns to update for booking {booking_id}")
            return False

        set_clause = ", ".join([f"{k} = %s" for k in safe_updates.keys()])
        params = list(safe_updates.values()) + [booking_id]

        query = f"UPDATE bookings SET {set_clause}, updated_at = NOW() WHERE id = %s"
        self._execute_write(query, tuple(params))
        return True

    def update_booking_payment(self, booking_id: str, amount_paid: int, payment_status: str) -> bool:
        """Update booking payment status."""
        booking = self.get_booking(booking_id)
        if not booking:
            return False

        amount_remaining = booking.total_price - amount_paid
        return self.update_booking(booking_id, {
            "amount_paid": amount_paid,
            "amount_remaining": amount_remaining,
            "payment_status": payment_status
        })

    # =========================================================================
    # PAYMENTS
    # =========================================================================

    def create_payment(self, payment: Payment) -> Optional[str]:
        """Create payment record."""
        query = """
            INSERT INTO payments (
                booking_id, payment_type, installment_number, amount,
                payment_method, bank_name, status, due_date, notes
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        result = self._execute_one(query, (
            payment.booking_id, payment.payment_type, payment.installment_number,
            payment.amount, payment.payment_method, payment.bank_name,
            payment.status, payment.due_date, payment.notes
        ))
        return result.get("id") if result else None

    def get_payments_for_booking(self, booking_id: str) -> List[Payment]:
        """Get payments for a booking."""
        query = """
            SELECT * FROM payments
            WHERE booking_id = %s
            ORDER BY created_at
        """
        results = self._execute(query, (booking_id,)) or []
        return [Payment(**r) for r in results]

    def confirm_payment(self, payment_id: str, confirmed_by: Optional[str] = None) -> bool:
        """Confirm a payment."""
        query = """
            UPDATE payments
            SET status = 'confirmed', paid_at = NOW(), confirmed_at = NOW(), confirmed_by = %s
            WHERE id = %s
        """
        self._execute_write(query, (confirmed_by, payment_id))

        # Update booking payment totals
        payment_query = "SELECT booking_id, amount FROM payments WHERE id = %s"
        payment = self._execute_one(payment_query, (payment_id,))
        if payment:
            self._recalculate_booking_payment(payment["booking_id"])

        return True

    def _recalculate_booking_payment(self, booking_id: str):
        """Recalculate booking payment totals."""
        query = """
            SELECT COALESCE(SUM(amount), 0) as total_paid
            FROM payments
            WHERE booking_id = %s AND status = 'confirmed'
        """
        result = self._execute_one(query, (booking_id,))
        if result:
            total_paid = result["total_paid"]
            booking = self.get_booking(booking_id)
            if booking:
                remaining = booking.total_price - total_paid
                if remaining <= 0:
                    status = "paid"
                elif total_paid > 0:
                    status = "partial"
                else:
                    status = "pending"

                self.update_booking(booking_id, {
                    "amount_paid": total_paid,
                    "amount_remaining": max(0, remaining),
                    "payment_status": status
                })

    def get_pending_payments(self) -> List[Payment]:
        """Get all pending payments."""
        query = """
            SELECT p.*, b.booking_code, j.full_name as jamaah_name
            FROM payments p
            JOIN bookings b ON p.booking_id = b.id
            LEFT JOIN jamaah j ON b.jamaah_id = j.id
            WHERE p.status = 'pending'
            ORDER BY p.due_date
        """
        return self._execute(query) or []

    def get_overdue_payments(self) -> List[Payment]:
        """Get overdue payments."""
        query = """
            SELECT p.*, b.booking_code, j.full_name as jamaah_name
            FROM payments p
            JOIN bookings b ON p.booking_id = b.id
            LEFT JOIN jamaah j ON b.jamaah_id = j.id
            WHERE p.status = 'pending' AND p.due_date < CURRENT_DATE
            ORDER BY p.due_date
        """
        return self._execute(query) or []

    # =========================================================================
    # DOCUMENTS
    # =========================================================================

    def create_document(self, doc: Document) -> Optional[str]:
        """Create document record."""
        query = """
            INSERT INTO documents (jamaah_id, booking_id, doc_type, doc_name, status, expiry_date)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        result = self._execute_one(query, (
            doc.jamaah_id, doc.booking_id, doc.doc_type,
            doc.doc_name, doc.status, doc.expiry_date
        ))
        return result.get("id") if result else None

    def get_documents_for_jamaah(self, jamaah_id: str) -> List[Document]:
        """Get documents for a jamaah."""
        query = "SELECT * FROM documents WHERE jamaah_id = %s ORDER BY doc_type"
        results = self._execute(query, (jamaah_id,)) or []
        return [Document(**r) for r in results]

    def update_document(self, doc_id: str, updates: Dict[str, Any]) -> bool:
        """Update document with SQL injection prevention."""
        if not updates:
            return False

        # Validate column names against whitelist (SQL injection prevention)
        safe_updates = validate_column_names(updates, ALLOWED_DOCUMENT_COLUMNS)
        if not safe_updates:
            logger.warning(f"No valid columns to update for document {doc_id}")
            return False

        set_clause = ", ".join([f"{k} = %s" for k in safe_updates.keys()])
        params = list(safe_updates.values()) + [doc_id]

        query = f"UPDATE documents SET {set_clause}, updated_at = NOW() WHERE id = %s"
        self._execute_write(query, tuple(params))
        return True

    def verify_document(self, doc_id: str, verified_by: str) -> bool:
        """Verify a document."""
        return self.update_document(doc_id, {
            "status": "verified",
            "verified_by": verified_by,
            "verified_at": datetime.now()
        })

    def get_document_checklist(self, jamaah_id: str) -> List[Dict[str, Any]]:
        """Get document checklist with status for a jamaah."""
        from .config import get_required_documents, get_optional_documents

        required = get_required_documents()
        optional = get_optional_documents()
        all_docs = required + optional

        existing = {d.doc_type: d for d in self.get_documents_for_jamaah(jamaah_id)}

        checklist = []
        for doc_config in all_docs:
            doc_type = doc_config["code"]
            existing_doc = existing.get(doc_type)

            checklist.append({
                "type": doc_type,
                "label": doc_config["label"],
                "description": doc_config.get("description", ""),
                "required": doc_config.get("required", False),
                "status": existing_doc.status if existing_doc else "pending",
                "file_url": existing_doc.file_url if existing_doc else None,
                "doc_id": existing_doc.id if existing_doc else None,
            })

        return checklist

    # =========================================================================
    # QUOTES
    # =========================================================================

    def generate_quote_number(self) -> str:
        """Generate unique quote number."""
        import random
        today = date.today().strftime("%Y%m%d")
        random_part = str(random.randint(1000, 9999))
        return f"QT{today}{random_part}"

    def create_quote(self, quote: Quote) -> Optional[str]:
        """Create new quote."""
        if not quote.quote_number:
            quote.quote_number = self.generate_quote_number()

        query = """
            INSERT INTO quotes (
                quote_number, lead_id, package_config, base_price,
                discount_amount, final_price, valid_until, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        result = self._execute_one(query, (
            quote.quote_number, quote.lead_id,
            json.dumps(quote.package_config), quote.base_price,
            quote.discount_amount, quote.final_price,
            quote.valid_until, quote.status
        ))
        return result.get("id") if result else None

    def get_quote(self, quote_id: str) -> Optional[Quote]:
        """Get quote by ID."""
        query = "SELECT * FROM quotes WHERE id = %s"
        result = self._execute_one(query, (quote_id,))
        if result:
            if isinstance(result.get("package_config"), str):
                result["package_config"] = json.loads(result["package_config"])
            return Quote(**result)
        return None

    def get_quotes_for_lead(self, lead_id: str) -> List[Quote]:
        """Get quotes for a lead."""
        query = "SELECT * FROM quotes WHERE lead_id = %s ORDER BY created_at DESC"
        results = self._execute(query, (lead_id,)) or []
        quotes = []
        for r in results:
            if isinstance(r.get("package_config"), str):
                r["package_config"] = json.loads(r["package_config"])
            quotes.append(Quote(**r))
        return quotes

    # =========================================================================
    # INVOICES
    # =========================================================================

    def generate_invoice_number(self) -> str:
        """Generate unique invoice number."""
        import random
        today = date.today().strftime("%Y%m%d")
        random_part = str(random.randint(1000, 9999))
        return f"INV{today}{random_part}"

    def create_invoice(self, invoice: Invoice) -> Optional[str]:
        """Create new invoice."""
        if not invoice.invoice_number:
            invoice.invoice_number = self.generate_invoice_number()

        query = """
            INSERT INTO invoices (
                invoice_number, booking_id, jamaah_id, invoice_type,
                subtotal, discount, tax, total, status, due_date
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        result = self._execute_one(query, (
            invoice.invoice_number, invoice.booking_id, invoice.jamaah_id,
            invoice.invoice_type, invoice.subtotal, invoice.discount,
            invoice.tax, invoice.total, invoice.status, invoice.due_date
        ))
        return result.get("id") if result else None

    def get_invoice(self, invoice_id: str) -> Optional[Invoice]:
        """Get invoice by ID."""
        query = "SELECT * FROM invoices WHERE id = %s"
        result = self._execute_one(query, (invoice_id,))
        if result:
            return Invoice(**result)
        return None

    def get_invoices_for_booking(self, booking_id: str) -> List[Invoice]:
        """Get invoices for a booking."""
        query = "SELECT * FROM invoices WHERE booking_id = %s ORDER BY created_at"
        results = self._execute(query, (booking_id,)) or []
        return [Invoice(**r) for r in results]

    # =========================================================================
    # BROADCASTS
    # =========================================================================

    def create_broadcast(self, broadcast: Broadcast) -> Optional[str]:
        """Create broadcast campaign."""
        query = """
            INSERT INTO broadcasts (
                name, message_template, target_type, target_filter, status
            ) VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """
        result = self._execute_one(query, (
            broadcast.name, broadcast.message_template,
            broadcast.target_type, json.dumps(broadcast.target_filter),
            broadcast.status
        ))
        return result.get("id") if result else None

    def get_broadcast(self, broadcast_id: str) -> Optional[Broadcast]:
        """Get broadcast by ID."""
        query = "SELECT * FROM broadcasts WHERE id = %s"
        result = self._execute_one(query, (broadcast_id,))
        if result:
            if isinstance(result.get("target_filter"), str):
                result["target_filter"] = json.loads(result["target_filter"])
            return Broadcast(**result)
        return None

    def get_broadcasts(self, status: Optional[str] = None, limit: int = 20) -> List[Broadcast]:
        """Get broadcasts."""
        if status:
            query = "SELECT * FROM broadcasts WHERE status = %s ORDER BY created_at DESC LIMIT %s"
            params = (status, limit)
        else:
            query = "SELECT * FROM broadcasts ORDER BY created_at DESC LIMIT %s"
            params = (limit,)

        results = self._execute(query, params) or []
        broadcasts = []
        for r in results:
            if isinstance(r.get("target_filter"), str):
                r["target_filter"] = json.loads(r["target_filter"])
            broadcasts.append(Broadcast(**r))
        return broadcasts

    # =========================================================================
    # COMPETITOR PRICES
    # =========================================================================

    def add_competitor_price(self, price: CompetitorPrice) -> Optional[str]:
        """Add competitor price."""
        query = """
            INSERT INTO competitor_prices (
                competitor_name, competitor_url, package_name, package_type,
                duration_days, hotel_makkah, hotel_madinah, airline,
                price, currency, source, scraped_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        result = self._execute_one(query, (
            price.competitor_name, price.competitor_url, price.package_name,
            price.package_type, price.duration_days, price.hotel_makkah,
            price.hotel_madinah, price.airline, price.price, price.currency,
            price.source, price.scraped_at or datetime.now()
        ))
        return result.get("id") if result else None

    def get_competitor_prices(
        self,
        competitor_name: Optional[str] = None,
        limit: int = 50
    ) -> List[CompetitorPrice]:
        """Get competitor prices."""
        if competitor_name:
            query = """
                SELECT * FROM competitor_prices
                WHERE competitor_name = %s
                ORDER BY scraped_at DESC
                LIMIT %s
            """
            params = (competitor_name, limit)
        else:
            query = "SELECT * FROM competitor_prices ORDER BY scraped_at DESC LIMIT %s"
            params = (limit,)

        results = self._execute(query, params) or []
        return [CompetitorPrice(**r) for r in results]

    def get_price_comparison(self, duration_days: int) -> List[Dict[str, Any]]:
        """Get price comparison for a duration."""
        query = """
            SELECT competitor_name, AVG(price) as avg_price, MIN(price) as min_price, MAX(price) as max_price
            FROM competitor_prices
            WHERE duration_days = %s
            AND scraped_at > NOW() - INTERVAL '30 days'
            GROUP BY competitor_name
            ORDER BY avg_price
        """
        return self._execute(query, (duration_days,)) or []

    # =========================================================================
    # ANALYTICS
    # =========================================================================

    def get_crm_stats(
        self,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None
    ) -> CRMStats:
        """Get CRM statistics."""
        if not period_start:
            period_start = date.today() - timedelta(days=30)
        if not period_end:
            period_end = date.today()

        stats = CRMStats(period_start=period_start, period_end=period_end)

        # Lead stats
        lead_query = """
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'new') as new_count,
                COUNT(*) FILTER (WHERE status = 'won') as won_count
            FROM leads
            WHERE created_at >= %s AND created_at <= %s
        """
        lead_result = self._execute_one(lead_query, (period_start, period_end))
        if lead_result:
            stats.total_leads = lead_result.get("total", 0)
            stats.new_leads = lead_result.get("new_count", 0)
            won_count = lead_result.get("won_count", 0)
            if stats.total_leads > 0:
                stats.conversion_rate = (won_count / stats.total_leads) * 100

        # Leads by status
        stats.leads_by_status = self.count_leads_by_status()

        # Booking stats
        booking_query = """
            SELECT
                COUNT(*) as total,
                COALESCE(SUM(total_price), 0) as revenue,
                COALESCE(SUM(amount_paid), 0) as paid,
                COALESCE(SUM(amount_remaining), 0) as pending
            FROM bookings
            WHERE created_at >= %s AND created_at <= %s
        """
        booking_result = self._execute_one(booking_query, (period_start, period_end))
        if booking_result:
            stats.total_bookings = booking_result.get("total", 0)
            stats.total_revenue = booking_result.get("revenue", 0)
            stats.total_paid = booking_result.get("paid", 0)
            stats.total_pending = booking_result.get("pending", 0)

        # Jamaah count
        jamaah_query = "SELECT COUNT(*) as total FROM jamaah"
        jamaah_result = self._execute_one(jamaah_query)
        if jamaah_result:
            stats.total_jamaah = jamaah_result.get("total", 0)

        return stats

    def get_revenue_trend(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get revenue trend over time."""
        query = """
            SELECT
                DATE(created_at) as date,
                COUNT(*) as bookings,
                COALESCE(SUM(total_price), 0) as revenue
            FROM bookings
            WHERE created_at >= NOW() - INTERVAL '1 day' * %s
            GROUP BY DATE(created_at)
            ORDER BY date
        """
        return self._execute(query, (days,)) or []

    def get_lead_trend(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get lead trend over time."""
        query = """
            SELECT
                DATE(created_at) as date,
                COUNT(*) as leads,
                COUNT(*) FILTER (WHERE status = 'won') as converted
            FROM leads
            WHERE created_at >= NOW() - INTERVAL '1 day' * %s
            GROUP BY DATE(created_at)
            ORDER BY date
        """
        return self._execute(query, (days,)) or []
