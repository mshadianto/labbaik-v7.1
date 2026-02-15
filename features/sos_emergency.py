"""
LABBAIK AI - SOS Emergency System
=================================
One-tap emergency system with:
- WhatsApp integration for instant alerts (via WAHA)
- GPS location sharing
- Pre-configured emergency contacts
- Embassy & hospital quick dial
- Group notification for Umrah Bareng
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import urllib.parse
import json
from services.ai.helpers import add_xp_safe
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS

# WAHA Integration (optional - graceful fallback)
try:
    from services.whatsapp import WhatsAppService, get_whatsapp_service
    HAS_WAHA = True
except ImportError:
    HAS_WAHA = False
    def get_whatsapp_service():
        return None

# =============================================================================
# DATA STRUCTURES
# =============================================================================

class EmergencyType(str, Enum):
    MEDICAL = "medical"
    LOST = "lost"
    SECURITY = "security"
    ACCIDENT = "accident"
    OTHER = "other"


@dataclass
class EmergencyContact:
    """Emergency contact structure."""
    name: str
    phone: str
    whatsapp: str = ""
    relationship: str = ""
    is_primary: bool = False
    
    def __post_init__(self):
        if not self.whatsapp:
            self.whatsapp = self.phone


@dataclass 
class EmergencyLocation:
    """Location data for emergency."""
    latitude: float = 0.0
    longitude: float = 0.0
    address: str = ""
    landmark: str = ""
    timestamp: str = ""
    
    def get_maps_url(self) -> str:
        """Get Google Maps URL for location."""
        if self.latitude and self.longitude:
            return f"https://www.google.com/maps?q={self.latitude},{self.longitude}"
        return ""


# =============================================================================
# EMERGENCY CONTACTS DATABASE
# =============================================================================

EMERGENCY_CONTACTS_SAUDI = {
    "emergency": [
        {"name": "Saudi Emergency", "phone": "911", "icon": "🚨", "desc": "Polisi, Ambulans, Pemadam"},
        {"name": "Ambulans", "phone": "997", "icon": "🚑", "desc": "Layanan medis darurat"},
        {"name": "Polisi", "phone": "999", "icon": "👮", "desc": "Keamanan & kepolisian"},
        {"name": "Civil Defense", "phone": "998", "icon": "🔥", "desc": "Pemadam kebakaran"},
    ],
    "embassy": [
        {"name": "KBRI Riyadh", "phone": "+966-11-488-2800", "icon": "🇮🇩", "desc": "Kedutaan Besar RI"},
        {"name": "KJRI Jeddah", "phone": "+966-12-667-6270", "icon": "🇮🇩", "desc": "Konsulat Jenderal RI"},
        {"name": "Hotline Kemenag", "phone": "+62-21-3811642", "icon": "📞", "desc": "Kementerian Agama RI"},
    ],
    "hospitals_makkah": [
        {"name": "Ajyad Emergency Hospital", "phone": "+966-12-545-6666", "icon": "🏥", "desc": "Dekat Masjidil Haram"},
        {"name": "King Abdul Aziz Hospital", "phone": "+966-12-556-6666", "icon": "🏥", "desc": "RS Pemerintah"},
        {"name": "Hera General Hospital", "phone": "+966-12-553-9999", "icon": "🏥", "desc": "RS Umum"},
    ],
    "hospitals_madinah": [
        {"name": "King Fahd Hospital", "phone": "+966-14-846-6666", "icon": "🏥", "desc": "RS Utama Madinah"},
        {"name": "Madinah General Hospital", "phone": "+966-14-826-0000", "icon": "🏥", "desc": "RS Pemerintah"},
        {"name": "Al Ansar Hospital", "phone": "+966-14-822-0000", "icon": "🏥", "desc": "RS Swasta"},
    ],
}

EMERGENCY_TEMPLATES = {
    EmergencyType.MEDICAL: {
        "icon": "🚑",
        "title": "Darurat Medis",
        "message_id": "🚨 DARURAT MEDIS!\n\nSaya {name} membutuhkan bantuan medis segera.\n\n📍 Lokasi: {location}\n🗺️ Maps: {maps_url}\n⏰ Waktu: {time}\n\nMohon segera hubungi saya atau kirim bantuan!",
        "message_en": "🚨 MEDICAL EMERGENCY!\n\nI am {name} and need immediate medical assistance.\n\n📍 Location: {location}\n🗺️ Maps: {maps_url}\n⏰ Time: {time}\n\nPlease contact me or send help immediately!",
    },
    EmergencyType.LOST: {
        "icon": "🆘",
        "title": "Terpisah dari Rombongan",
        "message_id": "🆘 TERPISAH DARI ROMBONGAN!\n\nSaya {name} terpisah dari rombongan umrah.\n\n📍 Lokasi terakhir: {location}\n🗺️ Maps: {maps_url}\n⏰ Waktu: {time}\n👥 Rombongan: {group_name}\n\nMohon segera hubungi saya!",
        "message_en": "🆘 SEPARATED FROM GROUP!\n\nI am {name} and have been separated from my Umrah group.\n\n📍 Last location: {location}\n🗺️ Maps: {maps_url}\n⏰ Time: {time}\n👥 Group: {group_name}\n\nPlease contact me immediately!",
    },
    EmergencyType.SECURITY: {
        "icon": "👮",
        "title": "Masalah Keamanan",
        "message_id": "⚠️ MASALAH KEAMANAN!\n\nSaya {name} mengalami masalah keamanan.\n\n📍 Lokasi: {location}\n🗺️ Maps: {maps_url}\n⏰ Waktu: {time}\n📝 Detail: {details}\n\nMohon segera hubungi saya!",
        "message_en": "⚠️ SECURITY ISSUE!\n\nI am {name} and experiencing a security problem.\n\n📍 Location: {location}\n🗺️ Maps: {maps_url}\n⏰ Time: {time}\n📝 Details: {details}\n\nPlease contact me immediately!",
    },
    EmergencyType.ACCIDENT: {
        "icon": "🚗",
        "title": "Kecelakaan",
        "message_id": "🚨 KECELAKAAN!\n\nSaya {name} mengalami kecelakaan.\n\n📍 Lokasi: {location}\n🗺️ Maps: {maps_url}\n⏰ Waktu: {time}\n📝 Kondisi: {details}\n\nMohon segera kirim bantuan!",
        "message_en": "🚨 ACCIDENT!\n\nI am {name} and have been in an accident.\n\n📍 Location: {location}\n🗺️ Maps: {maps_url}\n⏰ Time: {time}\n📝 Condition: {details}\n\nPlease send help immediately!",
    },
    EmergencyType.OTHER: {
        "icon": "❗",
        "title": "Darurat Lainnya",
        "message_id": "❗ BANTUAN DIPERLUKAN!\n\nSaya {name} membutuhkan bantuan.\n\n📍 Lokasi: {location}\n🗺️ Maps: {maps_url}\n⏰ Waktu: {time}\n📝 Detail: {details}\n\nMohon segera hubungi saya!",
        "message_en": "❗ HELP NEEDED!\n\nI am {name} and need assistance.\n\n📍 Location: {location}\n🗺️ Maps: {maps_url}\n⏰ Time: {time}\n📝 Details: {details}\n\nPlease contact me immediately!",
    },
}


# =============================================================================
# SOS SERVICE
# =============================================================================

class SOSService:
    """Emergency SOS service handler."""
    
    def __init__(self):
        self._init_session_state()
    
    def _init_session_state(self):
        """Initialize session state for SOS."""
        if "sos_contacts" not in st.session_state:
            st.session_state.sos_contacts = []
        
        if "sos_user_info" not in st.session_state:
            st.session_state.sos_user_info = {
                "name": "",
                "phone": "",
                "passport": "",
                "blood_type": "",
                "allergies": "",
                "medications": "",
                "group_name": "",
                "hotel_makkah": "",
                "hotel_madinah": "",
            }
        
        if "sos_location" not in st.session_state:
            st.session_state.sos_location = EmergencyLocation()
    
    def add_emergency_contact(self, contact: EmergencyContact):
        """Add emergency contact."""
        st.session_state.sos_contacts.append(contact)
    
    def remove_emergency_contact(self, index: int):
        """Remove emergency contact by index."""
        if 0 <= index < len(st.session_state.sos_contacts):
            st.session_state.sos_contacts.pop(index)
    
    def update_user_info(self, **kwargs):
        """Update user information."""
        st.session_state.sos_user_info.update(kwargs)
    
    def generate_sos_message(
        self, 
        emergency_type: EmergencyType,
        details: str = "",
        language: str = "id"
    ) -> str:
        """Generate SOS message with all relevant information."""
        
        template = EMERGENCY_TEMPLATES.get(emergency_type, EMERGENCY_TEMPLATES[EmergencyType.OTHER])
        message_key = f"message_{language}"
        message = template.get(message_key, template["message_id"])
        
        user_info = st.session_state.sos_user_info
        location = st.session_state.sos_location
        
        # Format message
        formatted = message.format(
            name=user_info.get("name", "Unknown"),
            location=location.address or "Lokasi tidak diketahui",
            maps_url=location.get_maps_url() or "N/A",
            time=datetime.now().strftime("%Y-%m-%d %H:%M"),
            group_name=user_info.get("group_name", "N/A"),
            details=details or "Tidak ada detail tambahan",
        )
        
        # Add medical info for medical emergencies
        if emergency_type == EmergencyType.MEDICAL:
            medical_info = []
            if user_info.get("blood_type"):
                medical_info.append(f"🩸 Golongan Darah: {user_info['blood_type']}")
            if user_info.get("allergies"):
                medical_info.append(f"⚠️ Alergi: {user_info['allergies']}")
            if user_info.get("medications"):
                medical_info.append(f"💊 Obat: {user_info['medications']}")
            
            if medical_info:
                formatted += "\n\n📋 INFO MEDIS:\n" + "\n".join(medical_info)
        
        return formatted
    
    def get_whatsapp_link(self, phone: str, message: str) -> str:
        """Generate WhatsApp link with pre-filled message."""
        # Clean phone number
        clean_phone = phone.replace("+", "").replace("-", "").replace(" ", "")
        encoded_message = urllib.parse.quote(message)
        return f"https://wa.me/{clean_phone}?text={encoded_message}"
    
    def get_sms_link(self, phone: str, message: str) -> str:
        """Generate SMS link with pre-filled message."""
        encoded_message = urllib.parse.quote(message)
        return f"sms:{phone}?body={encoded_message}"
    
    def get_call_link(self, phone: str) -> str:
        """Generate tel: link for calling."""
        return f"tel:{phone}"


# =============================================================================
# RENDER FUNCTIONS
# =============================================================================

def render_sos_button(size: str = "large"):
    """
    Render the main SOS button.
    
    Args:
        size: "large" for main page, "small" for sidebar
    """
    if size == "large":
        st.markdown("""
        <style>
        .sos-button-large {
            background: linear-gradient(135deg, #ef4444, #dc2626);
            color: white;
            font-size: 2rem;
            font-weight: bold;
            padding: 2rem 4rem;
            border-radius: 50%;
            border: 4px solid #fff;
            box-shadow: 0 0 30px rgba(239, 68, 68, 0.5), 0 10px 40px rgba(0,0,0,0.3);
            cursor: pointer;
            animation: pulse-sos 2s infinite;
            text-align: center;
            display: block;
            margin: 2rem auto;
            width: 200px;
            height: 200px;
            line-height: 160px;
        }
        
        @keyframes pulse-sos {
            0% { box-shadow: 0 0 30px rgba(239, 68, 68, 0.5); }
            50% { box-shadow: 0 0 50px rgba(239, 68, 68, 0.8); }
            100% { box-shadow: 0 0 30px rgba(239, 68, 68, 0.5); }
        }
        </style>
        """, unsafe_allow_html=True)
        
        if st.button("🆘 SOS", key="sos_main", use_container_width=False):
            st.session_state.sos_triggered = True
            st.rerun()
    else:
        # Compact button for sidebar
        if st.button("🆘 DARURAT", key="sos_sidebar", use_container_width=True, type="primary"):
            st.session_state.sos_triggered = True
            st.rerun()


def render_sos_setup():
    """Render SOS setup form for user info and contacts."""
    
    st.markdown("## ⚙️ Setup Darurat")
    st.caption("Lengkapi informasi ini untuk respons darurat yang lebih cepat")
    
    service = SOSService()
    
    # User Information
    with st.expander("👤 Informasi Pribadi", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input(
                "Nama Lengkap",
                value=st.session_state.sos_user_info.get("name", ""),
                key="sos_name"
            )
            phone = st.text_input(
                "No. HP (dengan kode negara)",
                value=st.session_state.sos_user_info.get("phone", ""),
                placeholder="+62812xxxxxxxx",
                key="sos_phone"
            )
            passport = st.text_input(
                "No. Paspor",
                value=st.session_state.sos_user_info.get("passport", ""),
                key="sos_passport"
            )
        
        with col2:
            blood_type = st.selectbox(
                "Golongan Darah",
                ["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
                index=0,
                key="sos_blood"
            )
            allergies = st.text_input(
                "Alergi (jika ada)",
                value=st.session_state.sos_user_info.get("allergies", ""),
                key="sos_allergies"
            )
            medications = st.text_input(
                "Obat Rutin (jika ada)",
                value=st.session_state.sos_user_info.get("medications", ""),
                key="sos_meds"
            )
    
    # Trip Information
    with st.expander("✈️ Informasi Perjalanan", expanded=False):
        group_name = st.text_input(
            "Nama Rombongan/Travel",
            value=st.session_state.sos_user_info.get("group_name", ""),
            key="sos_group"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            hotel_makkah = st.text_input(
                "Hotel di Makkah",
                value=st.session_state.sos_user_info.get("hotel_makkah", ""),
                key="sos_hotel_mkh"
            )
        with col2:
            hotel_madinah = st.text_input(
                "Hotel di Madinah",
                value=st.session_state.sos_user_info.get("hotel_madinah", ""),
                key="sos_hotel_mdn"
            )
    
    # Emergency Contacts
    with st.expander("📞 Kontak Darurat", expanded=True):
        st.caption("Tambahkan kontak yang akan dihubungi saat darurat")
        
        # Add new contact
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            new_name = st.text_input("Nama", key="new_contact_name")
        with col2:
            new_phone = st.text_input("No. WhatsApp", placeholder="+62xxx", key="new_contact_phone")
        with col3:
            new_relation = st.selectbox("Hubungan", ["Keluarga", "Teman", "Mutawif", "Travel Agent"], key="new_contact_rel")
        
        if st.button("➕ Tambah Kontak"):
            if new_name and new_phone:
                contact = EmergencyContact(
                    name=new_name,
                    phone=new_phone,
                    relationship=new_relation
                )
                service.add_emergency_contact(contact)
                st.success(f"✅ {new_name} ditambahkan!")
                st.rerun()
        
        # List existing contacts
        st.markdown("---")
        contacts = st.session_state.sos_contacts
        
        if contacts:
            for i, contact in enumerate(contacts):
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.markdown(f"**{contact.name}**")
                with col2:
                    st.caption(f"📱 {contact.phone} ({contact.relationship})")
                with col3:
                    if st.button("🗑️", key=f"del_contact_{i}"):
                        service.remove_emergency_contact(i)
                        st.rerun()
        else:
            st.info("Belum ada kontak darurat. Tambahkan minimal 1 kontak.")
    
    # Save button
    if st.button("💾 Simpan Semua", type="primary", use_container_width=True):
        service.update_user_info(
            name=name,
            phone=phone,
            passport=passport,
            blood_type=blood_type,
            allergies=allergies,
            medications=medications,
            group_name=group_name,
            hotel_makkah=hotel_makkah,
            hotel_madinah=hotel_madinah,
        )
        st.success("✅ Informasi darurat tersimpan!")


def render_sos_activated():
    """Render SOS activated screen with emergency options."""
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #ef4444, #dc2626); padding: 2rem; border-radius: 20px; text-align: center; margin-bottom: 2rem;">
        <div style="font-size: 4rem;">🆘</div>
        <div style="color: white; font-size: 2rem; font-weight: bold;">MODE DARURAT AKTIF</div>
        <div style="color: rgba(255,255,255,0.8);">Pilih jenis darurat dan kirim pesan</div>
    </div>
    """, unsafe_allow_html=True)
    
    service = SOSService()
    
    # Emergency type selection
    st.markdown("### Pilih Jenis Darurat")
    
    col1, col2, col3 = st.columns(3)
    
    emergency_types = [
        (EmergencyType.MEDICAL, "🚑", "Darurat Medis"),
        (EmergencyType.LOST, "🆘", "Terpisah Rombongan"),
        (EmergencyType.SECURITY, "👮", "Masalah Keamanan"),
    ]
    
    for i, (etype, icon, label) in enumerate(emergency_types):
        with [col1, col2, col3][i]:
            if st.button(f"{icon}\n{label}", key=f"etype_{etype}", use_container_width=True):
                st.session_state.sos_type = etype
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚗\nKecelakaan", key="etype_accident", use_container_width=True):
            st.session_state.sos_type = EmergencyType.ACCIDENT
    with col2:
        if st.button("❗\nLainnya", key="etype_other", use_container_width=True):
            st.session_state.sos_type = EmergencyType.OTHER
    
    # Get selected type
    selected_type = st.session_state.get("sos_type", EmergencyType.OTHER)
    template = EMERGENCY_TEMPLATES[selected_type]
    
    st.markdown(f"### {template['icon']} {template['title']}")
    
    # Additional details
    details = st.text_area(
        "Detail tambahan (opsional)",
        placeholder="Jelaskan situasi Anda...",
        key="sos_details"
    )
    
    # Generate message
    message = service.generate_sos_message(selected_type, details)
    
    with st.expander("📝 Preview Pesan", expanded=False):
        st.code(message)
    
    st.divider()
    
    # Quick action buttons
    st.markdown("### 📤 Kirim Bantuan")
    
    # To personal contacts
    contacts = st.session_state.sos_contacts
    
    if contacts:
        st.markdown("**Kontak Pribadi:**")
        
        # WAHA Direct Send Button (if available)
        if HAS_WAHA:
            wa_service = get_whatsapp_service()
            if wa_service and wa_service.is_available:
                if st.button("🚀 KIRIM KE SEMUA KONTAK (OTOMATIS)", type="primary", use_container_width=True):
                    with st.spinner("Mengirim pesan darurat..."):
                        user_info = st.session_state.sos_user_info
                        location = st.session_state.sos_location
                        
                        phones = [c.phone for c in contacts]
                        result = wa_service.send_sos_alert(
                            recipients=phones,
                            name=user_info.get("name", "Unknown"),
                            emergency_type=template['title'],
                            location=location.address or "Lokasi tidak diketahui",
                            latitude=location.latitude,
                            longitude=location.longitude,
                            details=details
                        )
                        
                        if result.get("success"):
                            st.success(f"✅ Pesan terkirim ke {result.get('sent')}/{result.get('total')} kontak!")
                            st.balloons()
                        else:
                            st.error("❌ Gagal mengirim. Gunakan link manual di bawah.")
                
                st.caption("☝️ Klik untuk kirim otomatis via WhatsApp API")
                st.markdown("---")
        
        # Manual WhatsApp links (fallback)
        st.markdown("**Atau kirim manual:**")
        cols = st.columns(min(len(contacts), 3))
        
        for i, contact in enumerate(contacts):
            with cols[i % 3]:
                wa_link = service.get_whatsapp_link(contact.phone, message)
                st.markdown(f"""
                <a href="{wa_link}" target="_blank" style="text-decoration: none;">
                    <div style="background: #25D366; padding: 1rem; border-radius: 10px; text-align: center; margin-bottom: 0.5rem;">
                        <div style="color: white; font-size: 1.5rem;">📱</div>
                        <div style="color: white; font-weight: bold;">{contact.name}</div>
                        <div style="color: rgba(255,255,255,0.8); font-size: 0.75rem;">WhatsApp</div>
                    </div>
                </a>
                """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ Belum ada kontak darurat. Tambahkan di Setup Darurat.")
    
    st.divider()
    
    # Official emergency contacts
    st.markdown("### 🚨 Kontak Resmi")
    
    tab1, tab2, tab3 = st.tabs(["🚨 Darurat", "🇮🇩 Kedutaan", "🏥 Rumah Sakit"])
    
    with tab1:
        for contact in EMERGENCY_CONTACTS_SAUDI["emergency"]:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"{contact['icon']} **{contact['name']}** - {contact['desc']}")
            with col2:
                call_link = service.get_call_link(contact['phone'])
                st.markdown(f"[📞 {contact['phone']}]({call_link})")
    
    with tab2:
        for contact in EMERGENCY_CONTACTS_SAUDI["embassy"]:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"{contact['icon']} **{contact['name']}** - {contact['desc']}")
            with col2:
                call_link = service.get_call_link(contact['phone'])
                st.markdown(f"[📞 Call]({call_link})")
    
    with tab3:
        location = st.radio("Lokasi Anda:", ["Makkah", "Madinah"], horizontal=True, key="hospital_loc")
        hospital_key = "hospitals_makkah" if location == "Makkah" else "hospitals_madinah"
        
        for contact in EMERGENCY_CONTACTS_SAUDI[hospital_key]:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"{contact['icon']} **{contact['name']}** - {contact['desc']}")
            with col2:
                call_link = service.get_call_link(contact['phone'])
                st.markdown(f"[📞 Call]({call_link})")
    
    st.divider()
    
    # Cancel button
    if st.button("❌ Batalkan Mode Darurat", use_container_width=True):
        st.session_state.sos_triggered = False
        st.rerun()


def render_sos_page():
    """Full SOS emergency page."""
    inject_css(HERO_CSS, CARD_CSS)

    st.markdown("""
        <div class="page-hero" style="--hero-bg: linear-gradient(135deg, #2a0d0d 0%, #4a1a1a 100%); --hero-border: #f87171; --hero-title: #f87171;">
            <h1>🆘 SOS Darurat</h1>
            <div class="subtitle">Sistem darurat satu sentuhan untuk keadaan darurat saat umrah</div>
        </div>
    """, unsafe_allow_html=True)

    if not st.session_state.get("sos_setup_xp_awarded"):
        add_xp_safe(5, "Menyiapkan kontak darurat")
        st.session_state.sos_setup_xp_awarded = True
    
    # Check if SOS is triggered
    if st.session_state.get("sos_triggered", False):
        render_sos_activated()
    else:
        # Main SOS button
        st.markdown("### Tekan tombol jika Anda dalam keadaan darurat")
        
        render_sos_button("large")
        
        st.divider()
        
        # Setup section
        render_sos_setup()
        
        st.divider()
        
        # Quick contacts section
        st.markdown("### 📞 Kontak Penting")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #1a1a1a, #2d2d2d); padding: 1rem; border-radius: 15px; border: 1px solid #d4af37;">
                <div style="color: #d4af37; font-weight: bold; margin-bottom: 0.5rem;">🚨 Saudi Emergency</div>
                <div style="color: white; font-size: 2rem; font-weight: bold;">911</div>
                <div style="color: #888; font-size: 0.8rem;">Polisi, Ambulans, Pemadam</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #1a1a1a, #2d2d2d); padding: 1rem; border-radius: 15px; border: 1px solid #d4af37;">
                <div style="color: #d4af37; font-weight: bold; margin-bottom: 0.5rem;">🇮🇩 KBRI Riyadh</div>
                <div style="color: white; font-size: 1.2rem; font-weight: bold;">+966-11-488-2800</div>
                <div style="color: #888; font-size: 0.8rem;">Kedutaan Besar RI</div>
            </div>
            """, unsafe_allow_html=True)


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    "SOSService",
    "EmergencyType",
    "EmergencyContact",
    "render_sos_button",
    "render_sos_setup",
    "render_sos_activated",
    "render_sos_page",
    "EMERGENCY_CONTACTS_SAUDI",
]
