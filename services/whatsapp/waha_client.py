"""
LABBAIK AI v6.0 - WAHA WhatsApp Integration
============================================
WhatsApp integration using WAHA (WhatsApp HTTP API)
for notifications, SOS alerts, and group messaging.

Features:
- SOS Emergency alerts
- Booking confirmations
- Group notifications (Umrah Bareng)
- Reminder messages
- Two-way chat support

WAHA Docs: https://waha.devlike.pro/
"""

import streamlit as st
import requests
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import os

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class WAHAConfig:
    """WAHA API Configuration."""
    base_url: str = ""
    api_key: str = ""
    session_name: str = "default"
    
    @classmethod
    def from_env(cls) -> "WAHAConfig":
        """Load config from environment/secrets."""
        return cls(
            base_url=os.getenv("WAHA_API_URL", ""),
            api_key=os.getenv("WAHA_API_KEY", ""),
            session_name=os.getenv("WAHA_SESSION", "default"),
        )
    
    @classmethod
    def from_streamlit_secrets(cls) -> "WAHAConfig":
        """Load config from Streamlit secrets."""
        try:
            return cls(
                base_url=st.secrets.get("WAHA_API_URL", ""),
                api_key=st.secrets.get("WAHA_API_KEY", ""),
                session_name=st.secrets.get("WAHA_SESSION", "default"),
            )
        except Exception:
            return cls.from_env()


class MessageType(str, Enum):
    """Types of WhatsApp messages."""
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    LOCATION = "location"
    BUTTONS = "buttons"
    LIST = "list"


# =============================================================================
# MESSAGE TEMPLATES
# =============================================================================

class MessageTemplates:
    """Pre-defined message templates for LABBAIK."""
    
    @staticmethod
    def sos_emergency(
        name: str,
        emergency_type: str,
        location: str,
        maps_url: str,
        details: str = ""
    ) -> str:
        """SOS Emergency alert template."""
        return f"""🚨 *DARURAT LABBAIK AI* 🚨

*{emergency_type.upper()}*

👤 Nama: {name}
📍 Lokasi: {location}
🗺️ Maps: {maps_url}
⏰ Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M')} WIB

📝 Detail:
{details or 'Tidak ada detail tambahan'}

---
_Pesan ini dikirim otomatis oleh sistem LABBAIK AI_
_Segera hubungi atau kirim bantuan!_"""

    @staticmethod
    def booking_confirmation(
        name: str,
        package_name: str,
        travel_agent: str,
        departure_date: str,
        total_price: str,
        booking_id: str
    ) -> str:
        """Booking confirmation template."""
        return f"""✅ *KONFIRMASI BOOKING UMRAH*

Assalamu'alaikum *{name}*,

Alhamdulillah, booking Anda telah berhasil!

📦 *Detail Paket:*
• Paket: {package_name}
• Travel: {travel_agent}
• Keberangkatan: {departure_date}
• Total: Rp {total_price}

🔖 *Kode Booking:* `{booking_id}`

📋 *Langkah Selanjutnya:*
1. Siapkan dokumen (paspor, foto, dll)
2. Lakukan pembayaran DP
3. Ikuti jadwal manasik

Jazakallahu khairan atas kepercayaan Anda! 🤲

---
_LABBAIK AI - Platform Umrah Cerdas_
_labbaik.io_"""

    @staticmethod
    def group_notification(
        group_name: str,
        message_type: str,
        content: str,
        sender: str = "Admin"
    ) -> str:
        """Group notification template."""
        return f"""📢 *NOTIFIKASI ROMBONGAN*

👥 Rombongan: {group_name}
👤 Dari: {sender}
📝 {message_type}:

{content}

---
_Dikirim via LABBAIK AI_"""

    @staticmethod
    def checkin_alert(
        member_name: str,
        location: str,
        group_name: str,
        time: str
    ) -> str:
        """Check-in location alert."""
        return f"""📍 *CHECK-IN ALERT*

👤 {member_name} telah check-in!
📍 Lokasi: {location}
👥 Rombongan: {group_name}
⏰ Waktu: {time}

---
_LABBAIK AI Group Tracking_"""

    @staticmethod
    def member_sos(
        member_name: str,
        group_name: str,
        location: str,
        maps_url: str
    ) -> str:
        """Member SOS alert to group."""
        return f"""🆘 *SOS ALERT - ANGGOTA BUTUH BANTUAN!*

👤 *{member_name}* membutuhkan bantuan!
👥 Rombongan: {group_name}
📍 Lokasi: {location}
🗺️ Maps: {maps_url}

⚠️ *Segera hubungi atau cari anggota tersebut!*

---
_LABBAIK AI Emergency System_"""

    @staticmethod
    def reminder(
        name: str,
        reminder_type: str,
        content: str,
        action_url: str = ""
    ) -> str:
        """General reminder template."""
        return f"""⏰ *PENGINGAT LABBAIK AI*

Assalamu'alaikum *{name}*,

📋 *{reminder_type}*

{content}

{f'🔗 {action_url}' if action_url else ''}

---
_LABBAIK AI Reminder System_"""

    @staticmethod
    def departure_reminder(
        name: str,
        days_left: int,
        departure_date: str,
        checklist: List[str]
    ) -> str:
        """Departure countdown reminder."""
        checklist_text = "\n".join([f"☐ {item}" for item in checklist])
        
        return f"""✈️ *PENGINGAT KEBERANGKATAN*

Assalamu'alaikum *{name}*,

🕐 *{days_left} hari lagi* menuju keberangkatan!
📅 Tanggal: {departure_date}

📋 *Checklist Persiapan:*
{checklist_text}

Pastikan semua dokumen dan persiapan sudah lengkap! 🤲

---
_LABBAIK AI - Countdown to Umrah_"""


# =============================================================================
# WAHA CLIENT
# =============================================================================

class WAHAClient:
    """Client for WAHA WhatsApp HTTP API."""
    
    def __init__(self, config: WAHAConfig = None):
        """Initialize WAHA client."""
        self.config = config or WAHAConfig.from_streamlit_secrets()
        self._session = None
    
    @property
    def is_configured(self) -> bool:
        """Check if WAHA is properly configured."""
        return bool(self.config.base_url)
    
    @property
    def headers(self) -> Dict[str, str]:
        """Get request headers."""
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["X-Api-Key"] = self.config.api_key
        return headers
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Dict = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """Make HTTP request to WAHA API."""
        if not self.is_configured:
            return {"success": False, "error": "WAHA not configured"}
        
        url = f"{self.config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, timeout=timeout)
            elif method.upper() == "POST":
                response = requests.post(
                    url, 
                    headers=self.headers, 
                    json=data, 
                    timeout=timeout
                )
            else:
                return {"success": False, "error": f"Unsupported method: {method}"}
            
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        
        except requests.exceptions.Timeout:
            logger.error(f"WAHA request timeout: {endpoint}")
            return {"success": False, "error": "Request timeout"}
        
        except requests.exceptions.RequestException as e:
            logger.error(f"WAHA request error: {e}")
            return {"success": False, "error": str(e)}
        
        except json.JSONDecodeError:
            return {"success": True, "data": response.text}
    
    # =========================================================================
    # SESSION MANAGEMENT
    # =========================================================================
    
    def get_sessions(self) -> Dict[str, Any]:
        """Get all WAHA sessions."""
        return self._make_request("GET", "/api/sessions")
    
    def get_session_status(self, session: str = None) -> Dict[str, Any]:
        """Get specific session status."""
        session = session or self.config.session_name
        return self._make_request("GET", f"/api/sessions/{session}")
    
    def start_session(self, session: str = None) -> Dict[str, Any]:
        """Start a WAHA session."""
        session = session or self.config.session_name
        return self._make_request("POST", f"/api/sessions/{session}/start")
    
    def stop_session(self, session: str = None) -> Dict[str, Any]:
        """Stop a WAHA session."""
        session = session or self.config.session_name
        return self._make_request("POST", f"/api/sessions/{session}/stop")
    
    # =========================================================================
    # MESSAGING
    # =========================================================================
    
    def send_text(
        self, 
        phone: str, 
        message: str, 
        session: str = None
    ) -> Dict[str, Any]:
        """
        Send text message.
        
        Args:
            phone: Phone number with country code (e.g., "6281234567890")
            message: Text message to send
            session: Session name (optional)
        """
        session = session or self.config.session_name
        
        # Clean phone number
        phone = self._clean_phone(phone)
        chat_id = f"{phone}@c.us"
        
        data = {
            "chatId": chat_id,
            "text": message,
            "session": session
        }
        
        return self._make_request("POST", "/api/sendText", data)
    
    def send_image(
        self,
        phone: str,
        image_url: str,
        caption: str = "",
        session: str = None
    ) -> Dict[str, Any]:
        """Send image message."""
        session = session or self.config.session_name
        phone = self._clean_phone(phone)
        chat_id = f"{phone}@c.us"
        
        data = {
            "chatId": chat_id,
            "file": {"url": image_url},
            "caption": caption,
            "session": session
        }
        
        return self._make_request("POST", "/api/sendImage", data)
    
    def send_location(
        self,
        phone: str,
        latitude: float,
        longitude: float,
        title: str = "",
        session: str = None
    ) -> Dict[str, Any]:
        """Send location message."""
        session = session or self.config.session_name
        phone = self._clean_phone(phone)
        chat_id = f"{phone}@c.us"
        
        data = {
            "chatId": chat_id,
            "latitude": latitude,
            "longitude": longitude,
            "title": title,
            "session": session
        }
        
        return self._make_request("POST", "/api/sendLocation", data)
    
    def send_buttons(
        self,
        phone: str,
        body: str,
        buttons: List[Dict[str, str]],
        title: str = "",
        footer: str = "",
        session: str = None
    ) -> Dict[str, Any]:
        """
        Send interactive button message.
        
        Args:
            phone: Phone number
            body: Message body
            buttons: List of buttons [{"id": "1", "text": "Button 1"}, ...]
            title: Optional title
            footer: Optional footer
        """
        session = session or self.config.session_name
        phone = self._clean_phone(phone)
        chat_id = f"{phone}@c.us"
        
        data = {
            "chatId": chat_id,
            "title": title,
            "body": body,
            "footer": footer,
            "buttons": buttons,
            "session": session
        }
        
        return self._make_request("POST", "/api/sendButtons", data)
    
    # =========================================================================
    # GROUP MESSAGING
    # =========================================================================
    
    def send_to_group(
        self,
        group_id: str,
        message: str,
        session: str = None
    ) -> Dict[str, Any]:
        """Send message to WhatsApp group."""
        session = session or self.config.session_name
        
        # Ensure group ID format
        if not group_id.endswith("@g.us"):
            group_id = f"{group_id}@g.us"
        
        data = {
            "chatId": group_id,
            "text": message,
            "session": session
        }
        
        return self._make_request("POST", "/api/sendText", data)
    
    def get_groups(self, session: str = None) -> Dict[str, Any]:
        """Get list of groups."""
        session = session or self.config.session_name
        return self._make_request("GET", f"/api/{session}/groups")
    
    # =========================================================================
    # BULK MESSAGING
    # =========================================================================
    
    def send_bulk(
        self,
        phones: List[str],
        message: str,
        delay_seconds: float = 1.0,
        session: str = None
    ) -> List[Dict[str, Any]]:
        """
        Send message to multiple recipients.
        
        Args:
            phones: List of phone numbers
            message: Message to send
            delay_seconds: Delay between messages (anti-spam)
        """
        import time
        
        results = []
        for phone in phones:
            result = self.send_text(phone, message, session)
            results.append({"phone": phone, **result})
            time.sleep(delay_seconds)
        
        return results
    
    # =========================================================================
    # HELPERS
    # =========================================================================
    
    def _clean_phone(self, phone: str) -> str:
        """Clean and normalize phone number."""
        # Remove common prefixes and characters
        phone = phone.replace("+", "").replace("-", "").replace(" ", "")
        
        # Handle Indonesian format
        if phone.startswith("08"):
            phone = "62" + phone[1:]
        elif phone.startswith("8"):
            phone = "62" + phone
        
        return phone
    
    def check_number(self, phone: str, session: str = None) -> Dict[str, Any]:
        """Check if number is registered on WhatsApp."""
        session = session or self.config.session_name
        phone = self._clean_phone(phone)
        
        data = {
            "phone": phone,
            "session": session
        }
        
        return self._make_request("POST", "/api/checkNumberStatus", data)


# =============================================================================
# HIGH-LEVEL SERVICE
# =============================================================================

class WhatsAppService:
    """High-level WhatsApp service for LABBAIK AI."""
    
    def __init__(self):
        """Initialize WhatsApp service."""
        self.client = WAHAClient()
        self.templates = MessageTemplates()
    
    @property
    def is_available(self) -> bool:
        """Check if WhatsApp service is available."""
        return self.client.is_configured
    
    def send_sos_alert(
        self,
        recipients: List[str],
        name: str,
        emergency_type: str,
        location: str,
        latitude: float = 0,
        longitude: float = 0,
        details: str = ""
    ) -> Dict[str, Any]:
        """Send SOS emergency alert to multiple recipients."""
        
        maps_url = f"https://www.google.com/maps?q={latitude},{longitude}" if latitude else "N/A"
        
        message = self.templates.sos_emergency(
            name=name,
            emergency_type=emergency_type,
            location=location,
            maps_url=maps_url,
            details=details
        )
        
        results = []
        for phone in recipients:
            # Send text alert
            text_result = self.client.send_text(phone, message)
            results.append(text_result)
            
            # Also send location if available
            if latitude and longitude:
                loc_result = self.client.send_location(
                    phone, latitude, longitude, 
                    title=f"Lokasi Darurat: {name}"
                )
                results.append(loc_result)
        
        success_count = sum(1 for r in results if r.get("success"))
        
        return {
            "success": success_count > 0,
            "sent": success_count,
            "total": len(results),
            "results": results
        }
    
    def send_booking_confirmation(
        self,
        phone: str,
        name: str,
        package_name: str,
        travel_agent: str,
        departure_date: str,
        total_price: str,
        booking_id: str
    ) -> Dict[str, Any]:
        """Send booking confirmation message."""
        
        message = self.templates.booking_confirmation(
            name=name,
            package_name=package_name,
            travel_agent=travel_agent,
            departure_date=departure_date,
            total_price=total_price,
            booking_id=booking_id
        )
        
        return self.client.send_text(phone, message)
    
    def send_group_notification(
        self,
        phones: List[str],
        group_name: str,
        notification_type: str,
        content: str,
        sender: str = "Admin"
    ) -> Dict[str, Any]:
        """Send notification to all group members."""
        
        message = self.templates.group_notification(
            group_name=group_name,
            message_type=notification_type,
            content=content,
            sender=sender
        )
        
        results = self.client.send_bulk(phones, message, delay_seconds=0.5)
        success_count = sum(1 for r in results if r.get("success"))
        
        return {
            "success": success_count > 0,
            "sent": success_count,
            "total": len(phones),
            "results": results
        }
    
    def send_checkin_notification(
        self,
        leader_phone: str,
        member_name: str,
        location: str,
        group_name: str
    ) -> Dict[str, Any]:
        """Notify group leader of member check-in."""
        
        message = self.templates.checkin_alert(
            member_name=member_name,
            location=location,
            group_name=group_name,
            time=datetime.now().strftime("%H:%M WIB")
        )
        
        return self.client.send_text(leader_phone, message)
    
    def send_departure_reminder(
        self,
        phone: str,
        name: str,
        days_left: int,
        departure_date: str
    ) -> Dict[str, Any]:
        """Send departure countdown reminder."""
        
        checklist = [
            "Paspor (min. 7 bulan berlaku)",
            "Visa Umrah",
            "Tiket pesawat",
            "Bukti booking hotel",
            "Sertifikat vaksin",
            "Pakaian ihram",
            "Obat-obatan pribadi",
            "Uang Saudi Riyal"
        ]
        
        message = self.templates.departure_reminder(
            name=name,
            days_left=days_left,
            departure_date=departure_date,
            checklist=checklist[:5]  # First 5 items
        )
        
        return self.client.send_text(phone, message)


# =============================================================================
# STREAMLIT UI COMPONENTS
# =============================================================================

def render_whatsapp_status():
    """Render WhatsApp connection status widget."""
    
    service = WhatsAppService()
    
    if not service.is_available:
        st.warning("⚠️ WhatsApp tidak terkonfigurasi")
        st.caption("Tambahkan WAHA_API_URL di Streamlit Secrets")
        return
    
    # Check session status
    status = service.client.get_session_status()
    
    if status.get("success"):
        data = status.get("data", {})
        session_status = data.get("status", "UNKNOWN")
        
        if session_status == "WORKING":
            st.success("✅ WhatsApp Terhubung")
        elif session_status == "SCAN_QR_CODE":
            st.warning("📱 Scan QR Code diperlukan")
        else:
            st.error(f"❌ Status: {session_status}")
    else:
        st.error("❌ Gagal cek status WhatsApp")


def render_whatsapp_test():
    """Render WhatsApp test form."""
    
    st.markdown("### 📱 Test WhatsApp")
    
    service = WhatsAppService()
    
    if not service.is_available:
        st.error("WhatsApp tidak tersedia")
        return
    
    phone = st.text_input("Nomor HP (08xxx)", placeholder="08123456789")
    message = st.text_area("Pesan", value="Test dari LABBAIK AI! 🕋")
    
    if st.button("📤 Kirim Test", type="primary"):
        if phone:
            with st.spinner("Mengirim..."):
                result = service.client.send_text(phone, message)
            
            if result.get("success"):
                st.success("✅ Pesan terkirim!")
            else:
                st.error(f"❌ Gagal: {result.get('error')}")
        else:
            st.warning("Masukkan nomor HP")


def render_whatsapp_settings():
    """Render WhatsApp settings page."""
    
    st.markdown("## 📱 Pengaturan WhatsApp")
    st.caption("Kelola integrasi WAHA WhatsApp")
    
    # Status
    render_whatsapp_status()
    
    st.divider()
    
    # Test
    render_whatsapp_test()
    
    st.divider()
    
    # Configuration info
    with st.expander("⚙️ Konfigurasi"):
        st.markdown("""
        Tambahkan ke Streamlit Secrets:
        
        ```toml
        WAHA_API_URL = "https://your-waha-url.com"
        WAHA_API_KEY = "your-api-key"
        WAHA_SESSION = "default"
        ```
        """)


# =============================================================================
# SINGLETON & EXPORTS
# =============================================================================

@st.cache_resource
def get_whatsapp_service() -> WhatsAppService:
    """Get cached WhatsApp service instance."""
    return WhatsAppService()


__all__ = [
    "WAHAConfig",
    "WAHAClient",
    "WhatsAppService",
    "MessageTemplates",
    "MessageType",
    "get_whatsapp_service",
    "render_whatsapp_status",
    "render_whatsapp_test",
    "render_whatsapp_settings",
]
