"""
LABBAIK AI v6.0 - WhatsApp Integration Service (WAHA)
======================================================
Integration with WAHA (WhatsApp HTTP API) for:
- SOS Emergency alerts
- Booking confirmations
- Trip reminders
- Group notifications
- Payment notifications

WAHA Dashboard: """

import streamlit as st
import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import urllib.parse

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
        """Load config from environment variables."""
        return cls(
            base_url=os.getenv("WAHA_API_URL", "https://waha-qikiufjwa2nh.cgk-max.sumopod.my.id"),
            api_key=os.getenv("WAHA_API_KEY", ""),
            session_name=os.getenv("WAHA_SESSION", "default")
        )
    
    @classmethod
    def from_secrets(cls) -> "WAHAConfig":
        """Load config from Streamlit secrets."""
        try:
            return cls(
                base_url=st.secrets.get("WAHA_API_URL", "https://waha-qikiufjwa2nh.cgk-max.sumopod.my.id"),
                api_key=st.secrets.get("WAHA_API_KEY", ""),
                session_name=st.secrets.get("WAHA_SESSION", "default")
            )
        except Exception:
            return cls.from_env()


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    LOCATION = "location"
    CONTACT = "contact"


# =============================================================================
# MESSAGE TEMPLATES
# =============================================================================

class MessageTemplates:
    """Pre-defined message templates for various notifications."""
    
    @staticmethod
    def sos_alert(name: str, location: str, maps_url: str, emergency_type: str) -> str:
        return f"""🆘 *DARURAT - LABBAIK AI*

*{name}* membutuhkan bantuan!

📍 *Lokasi:* {location}
🗺️ *Maps:* {maps_url}
⏰ *Waktu:* {datetime.now().strftime("%d/%m/%Y %H:%M")} WAS
🚨 *Jenis:* {emergency_type}

Mohon segera hubungi atau kirim bantuan!

_Pesan otomatis dari LABBAIK AI_
"""

    @staticmethod
    def booking_confirmation(
        booking_id: str,
        name: str,
        package_name: str,
        travel_date: str,
        total_price: str,
        provider: str
    ) -> str:
        return f"""✅ *KONFIRMASI BOOKING - LABBAIK AI*

Assalamu'alaikum *{name}*,

Booking Anda telah berhasil!

📋 *Detail Booking:*
• ID: `{booking_id}`
• Paket: {package_name}
• Travel: {provider}
• Tanggal: {travel_date}
• Total: Rp {total_price}

📱 *Langkah Selanjutnya:*
1. Lakukan pembayaran DP
2. Siapkan dokumen (paspor, foto, dll)
3. Hubungi travel untuk konfirmasi

Jazakallahu khairan atas kepercayaan Anda! 🕋

_LABBAIK AI - Platform Umrah Cerdas_
"""

    @staticmethod
    def payment_reminder(
        name: str,
        booking_id: str,
        amount: str,
        due_date: str
    ) -> str:
        return f"""💰 *PENGINGAT PEMBAYARAN*

Assalamu'alaikum *{name}*,

Pembayaran booking Anda belum lengkap:

📋 Booking ID: `{booking_id}`
💵 Sisa: Rp {amount}
📅 Jatuh Tempo: {due_date}

Segera lakukan pembayaran untuk mengamankan kursi Anda.

_LABBAIK AI - Platform Umrah Cerdas_
"""

    @staticmethod
    def trip_reminder(
        name: str,
        days_left: int,
        departure_date: str,
        package_name: str
    ) -> str:
        emoji = "🎉" if days_left <= 7 else "📅"
        return f"""{emoji} *PENGINGAT PERJALANAN*

Assalamu'alaikum *{name}*,

Perjalanan umrah Anda tinggal *{days_left} hari* lagi!

✈️ *Keberangkatan:* {departure_date}
📦 *Paket:* {package_name}

📋 *Checklist Persiapan:*
☐ Paspor masih berlaku min. 6 bulan
☐ Visa sudah terbit
☐ Pakaian ihram
☐ Obat-obatan pribadi
☐ Uang SAR/USD

Semoga perjalanan Anda lancar dan mabrur! 🤲

_LABBAIK AI - Platform Umrah Cerdas_
"""

    @staticmethod
    def group_notification(
        group_name: str,
        sender_name: str,
        message: str
    ) -> str:
        return f"""👥 *{group_name}*

Dari: {sender_name}
Waktu: {datetime.now().strftime("%H:%M")}

{message}

_Via LABBAIK AI Group Tracking_
"""

    @staticmethod
    def group_sos(
        group_name: str,
        member_name: str,
        location: str,
        maps_url: str
    ) -> str:
        return f"""🚨 *SOS - ANGGOTA BUTUH BANTUAN!*

👥 Rombongan: *{group_name}*
👤 Anggota: *{member_name}*
📍 Lokasi: {location}
🗺️ Maps: {maps_url}
⏰ Waktu: {datetime.now().strftime("%H:%M")} WAS

Segera periksa dan bantu anggota ini!

_LABBAIK AI Group Tracking_
"""

    @staticmethod
    def welcome_message(name: str) -> str:
        return f"""🕋 *Assalamu'alaikum, {name}!*

Selamat datang di *LABBAIK AI* - Platform Perencanaan Umrah #1 Indonesia.

Anda akan menerima notifikasi penting tentang:
✅ Konfirmasi booking
✅ Pengingat pembayaran
✅ Countdown keberangkatan
✅ Alert darurat (jika diperlukan)

Ketik *MENU* untuk melihat perintah yang tersedia.

Jazakallahu khairan! 🤲

_LABBAIK AI - Platform Umrah Cerdas_
"""


# =============================================================================
# WAHA API CLIENT
# =============================================================================

class WAHAClient:
    """Client for WAHA (WhatsApp HTTP API)."""
    
    def __init__(self, config: WAHAConfig = None):
        self.config = config or WAHAConfig.from_secrets()
        self.base_url = self.config.base_url.rstrip("/")
        self.session = self.config.session_name
        self.headers = {
            "Content-Type": "application/json",
        }
        if self.config.api_key:
            self.headers["X-Api-Key"] = self.config.api_key
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Dict = None
    ) -> Dict[str, Any]:
        """Make HTTP request to WAHA API."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers, timeout=30)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data, timeout=30)
            else:
                return {"success": False, "error": f"Unsupported method: {method}"}
            
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Request timeout"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Connection failed"}
        except requests.exceptions.HTTPError as e:
            return {"success": False, "error": f"HTTP Error: {e}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def check_health(self) -> bool:
        """Check if WAHA API is healthy."""
        result = self._make_request("GET", "/api/health")
        return result.get("success", False)
    
    def get_sessions(self) -> List[Dict]:
        """Get all WhatsApp sessions."""
        result = self._make_request("GET", "/api/sessions")
        if result.get("success"):
            return result.get("data", [])
        return []
    
    def get_session_status(self, session: str = None) -> Dict:
        """Get status of a specific session."""
        session = session or self.session
        result = self._make_request("GET", f"/api/sessions/{session}")
        return result
    
    def send_text(
        self, 
        phone: str, 
        message: str, 
        session: str = None
    ) -> Dict[str, Any]:
        """
        Send text message.
        
        Args:
            phone: Phone number with country code (e.g., 6281234567890)
            message: Message text (supports WhatsApp formatting)
            session: Session name (optional)
        """
        session = session or self.session
        
        # Clean phone number
        phone = self._clean_phone(phone)
        
        data = {
            "chatId": f"{phone}@c.us",
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
        session = session or self.session
        phone = self._clean_phone(phone)
        
        data = {
            "chatId": f"{phone}@c.us",
            "file": {
                "url": image_url
            },
            "caption": caption,
            "session": session
        }
        
        return self._make_request("POST", "/api/sendImage", data)
    
    def send_document(
        self,
        phone: str,
        document_url: str,
        filename: str,
        caption: str = "",
        session: str = None
    ) -> Dict[str, Any]:
        """Send document/file."""
        session = session or self.session
        phone = self._clean_phone(phone)
        
        data = {
            "chatId": f"{phone}@c.us",
            "file": {
                "url": document_url,
                "filename": filename
            },
            "caption": caption,
            "session": session
        }
        
        return self._make_request("POST", "/api/sendFile", data)
    
    def send_location(
        self,
        phone: str,
        latitude: float,
        longitude: float,
        title: str = "",
        address: str = "",
        session: str = None
    ) -> Dict[str, Any]:
        """Send location message."""
        session = session or self.session
        phone = self._clean_phone(phone)
        
        data = {
            "chatId": f"{phone}@c.us",
            "latitude": latitude,
            "longitude": longitude,
            "title": title,
            "address": address,
            "session": session
        }
        
        return self._make_request("POST", "/api/sendLocation", data)
    
    def send_to_group(
        self,
        group_id: str,
        message: str,
        session: str = None
    ) -> Dict[str, Any]:
        """Send message to WhatsApp group."""
        session = session or self.session
        
        data = {
            "chatId": f"{group_id}@g.us",
            "text": message,
            "session": session
        }
        
        return self._make_request("POST", "/api/sendText", data)
    
    def _clean_phone(self, phone: str) -> str:
        """Clean phone number - remove +, -, spaces."""
        phone = str(phone).strip()
        phone = phone.replace("+", "").replace("-", "").replace(" ", "")
        
        # Convert 08xx to 628xx for Indonesian numbers
        if phone.startswith("08"):
            phone = "62" + phone[1:]
        
        return phone


# =============================================================================
# WHATSAPP SERVICE (High-Level)
# =============================================================================

class WhatsAppService:
    """High-level WhatsApp service for LABBAIK AI."""
    
    def __init__(self):
        self.client = WAHAClient()
        self.templates = MessageTemplates()
    
    def is_available(self) -> bool:
        """Check if WhatsApp service is available."""
        return self.client.check_health()
    
    def send_sos_alert(
        self,
        contacts: List[str],
        sender_name: str,
        location: str,
        maps_url: str,
        emergency_type: str = "Darurat Umum"
    ) -> Dict[str, Any]:
        """
        Send SOS alert to multiple contacts.
        
        Returns:
            Dict with success count and failed numbers
        """
        message = self.templates.sos_alert(
            name=sender_name,
            location=location,
            maps_url=maps_url,
            emergency_type=emergency_type
        )
        
        results = {
            "success": 0,
            "failed": 0,
            "failed_numbers": []
        }
        
        for phone in contacts:
            result = self.client.send_text(phone, message)
            if result.get("success"):
                results["success"] += 1
            else:
                results["failed"] += 1
                results["failed_numbers"].append(phone)
        
        return results
    
    def send_booking_confirmation(
        self,
        phone: str,
        booking_id: str,
        name: str,
        package_name: str,
        travel_date: str,
        total_price: str,
        provider: str
    ) -> Dict[str, Any]:
        """Send booking confirmation."""
        message = self.templates.booking_confirmation(
            booking_id=booking_id,
            name=name,
            package_name=package_name,
            travel_date=travel_date,
            total_price=total_price,
            provider=provider
        )
        
        return self.client.send_text(phone, message)
    
    def send_payment_reminder(
        self,
        phone: str,
        name: str,
        booking_id: str,
        amount: str,
        due_date: str
    ) -> Dict[str, Any]:
        """Send payment reminder."""
        message = self.templates.payment_reminder(
            name=name,
            booking_id=booking_id,
            amount=amount,
            due_date=due_date
        )
        
        return self.client.send_text(phone, message)
    
    def send_trip_reminder(
        self,
        phone: str,
        name: str,
        days_left: int,
        departure_date: str,
        package_name: str
    ) -> Dict[str, Any]:
        """Send trip countdown reminder."""
        message = self.templates.trip_reminder(
            name=name,
            days_left=days_left,
            departure_date=departure_date,
            package_name=package_name
        )
        
        return self.client.send_text(phone, message)
    
    def send_group_notification(
        self,
        phones: List[str],
        group_name: str,
        sender_name: str,
        message_text: str
    ) -> Dict[str, Any]:
        """Send notification to all group members."""
        message = self.templates.group_notification(
            group_name=group_name,
            sender_name=sender_name,
            message=message_text
        )
        
        results = {"success": 0, "failed": 0}
        
        for phone in phones:
            result = self.client.send_text(phone, message)
            if result.get("success"):
                results["success"] += 1
            else:
                results["failed"] += 1
        
        return results
    
    def send_group_sos(
        self,
        phones: List[str],
        group_name: str,
        member_name: str,
        location: str,
        maps_url: str
    ) -> Dict[str, Any]:
        """Send SOS alert to all group members."""
        message = self.templates.group_sos(
            group_name=group_name,
            member_name=member_name,
            location=location,
            maps_url=maps_url
        )
        
        results = {"success": 0, "failed": 0}
        
        for phone in phones:
            result = self.client.send_text(phone, message)
            if result.get("success"):
                results["success"] += 1
            else:
                results["failed"] += 1
        
        return results
    
    def send_welcome(self, phone: str, name: str) -> Dict[str, Any]:
        """Send welcome message to new user."""
        message = self.templates.welcome_message(name)
        return self.client.send_text(phone, message)


# =============================================================================
# STREAMLIT UI COMPONENTS
# =============================================================================

def render_whatsapp_status():
    """Render WhatsApp connection status widget."""
    
    service = WhatsAppService()
    
    try:
        is_available = service.is_available()
        
        if is_available:
            st.success("📱 WhatsApp: Terhubung")
        else:
            st.warning("📱 WhatsApp: Tidak tersedia")
    except Exception:
        st.caption("📱 WhatsApp: Offline")


def render_whatsapp_test():
    """Render WhatsApp test form."""
    
    st.markdown("### 📱 Test WhatsApp")
    
    service = WhatsAppService()
    
    # Check status
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.caption("Status koneksi WAHA")
    
    with col2:
        if st.button("🔄 Check"):
            if service.is_available():
                st.success("✅ Terhubung!")
            else:
                st.error("❌ Tidak terhubung")
    
    st.divider()
    
    # Test send
    phone = st.text_input(
        "No. WhatsApp (dengan kode negara)",
        placeholder="6281234567890",
        key="wa_test_phone"
    )
    
    message = st.text_area(
        "Pesan",
        value="🕋 Test dari LABBAIK AI\n\nIni adalah pesan test.",
        key="wa_test_msg"
    )
    
    if st.button("📤 Kirim Test", type="primary"):
        if phone and message:
            with st.spinner("Mengirim..."):
                result = service.client.send_text(phone, message)
                
                if result.get("success"):
                    st.success("✅ Pesan terkirim!")
                else:
                    st.error(f"❌ Gagal: {result.get('error', 'Unknown error')}")
        else:
            st.warning("Lengkapi nomor dan pesan!")


def render_whatsapp_settings():
    """Render WhatsApp settings page."""
    
    st.markdown("## 📱 Pengaturan WhatsApp")
    st.caption("Konfigurasi integrasi WhatsApp untuk notifikasi")
    
    # Current config
    config = WAHAConfig.from_secrets()
    
    st.markdown("### 🔧 Konfigurasi Saat Ini")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("WAHA URL", value=config.base_url, disabled=True)
    
    with col2:
        st.text_input("Session", value=config.session_name, disabled=True)
    
    st.divider()
    
    # Test section
    render_whatsapp_test()
    
    st.divider()
    
    # Notification settings
    st.markdown("### 🔔 Pengaturan Notifikasi")
    
    st.checkbox("📦 Konfirmasi booking otomatis", value=True)
    st.checkbox("💰 Pengingat pembayaran", value=True)
    st.checkbox("✈️ Countdown keberangkatan", value=True)
    st.checkbox("🆘 SOS alert", value=True)
    st.checkbox("👥 Notifikasi grup", value=True)
    
    if st.button("💾 Simpan Pengaturan"):
        st.success("✅ Pengaturan tersimpan!")


# =============================================================================
# INTEGRATION WITH SOS EMERGENCY
# =============================================================================

def send_sos_via_whatsapp(
    contacts: List[Dict],
    sender_name: str,
    location: str,
    latitude: float = 0,
    longitude: float = 0,
    emergency_type: str = "Darurat"
) -> Dict[str, Any]:
    """
    Send SOS alert via WhatsApp to all emergency contacts.
    This is called from the SOS Emergency feature.
    """
    service = WhatsAppService()
    
    # Generate maps URL
    if latitude and longitude:
        maps_url = f"https://www.google.com/maps?q={latitude},{longitude}"
    else:
        maps_url = "Lokasi tidak tersedia"
    
    # Extract phone numbers
    phones = [c.get("phone") or c.get("whatsapp", "") for c in contacts if c]
    phones = [p for p in phones if p]  # Filter empty
    
    if not phones:
        return {"success": 0, "failed": 0, "error": "No contacts"}
    
    return service.send_sos_alert(
        contacts=phones,
        sender_name=sender_name,
        location=location,
        maps_url=maps_url,
        emergency_type=emergency_type
    )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "WAHAConfig",
    "WAHAClient",
    "WhatsAppService",
    "MessageTemplates",
    "render_whatsapp_status",
    "render_whatsapp_test",
    "render_whatsapp_settings",
    "send_sos_via_whatsapp",
]
