"""
LABBAIK AI - Application Constants
==================================
Centralized constants for consistent values across the application.
"""

from enum import Enum, IntEnum
from typing import Dict, List, Tuple

# =============================================================================
# APPLICATION INFO (Dynamic from version.py)
# =============================================================================

try:
    from core.version import APP_VERSION, APP_NAME, APP_TAGLINE
except ImportError:
    APP_NAME = "LABBAIK Smart Planner"
    APP_VERSION = "7.8.0"
    APP_TAGLINE = "Satu-satunya AI Companion untuk Umrah Anda"

APP_AUTHOR = "MS Hadianto"
APP_WEBSITE = "https://labbaik.io"


# =============================================================================
# ENUMS
# =============================================================================

class UserRole(str, Enum):
    """User roles in the system."""
    GUEST = "guest"
    USER = "user"
    PREMIUM = "premium"
    PARTNER = "partner"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"


class SubscriptionTier(str, Enum):
    """Subscription tiers."""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class BookingStatus(str, Enum):
    """Booking status values."""
    DRAFT = "draft"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PAID = "paid"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    REFUNDED = "refunded"


class ChatRole(str, Enum):
    """Chat message roles."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class UmrahPackageType(str, Enum):
    """Types of Umrah packages."""
    REGULER = "reguler"
    PLUS = "plus"
    VIP = "vip"
    BACKPACKER = "backpacker"
    MANDIRI = "mandiri"


class HotelStarRating(IntEnum):
    """Hotel star ratings."""
    BUDGET = 2
    STANDARD = 3
    SUPERIOR = 4
    DELUXE = 5


class PaymentStatus(str, Enum):
    """Payment status values."""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    EXPIRED = "expired"
    REFUNDED = "refunded"


class BadgeType(str, Enum):
    """Gamification badge types."""
    NEWCOMER = "newcomer"
    EXPLORER = "explorer"
    PLANNER = "planner"
    SCHOLAR = "scholar"
    CONTRIBUTOR = "contributor"
    AMBASSADOR = "ambassador"


# =============================================================================
# LIMITS & THRESHOLDS
# =============================================================================

class Limits:
    """Application limits."""
    # Chat
    MAX_MESSAGE_LENGTH = 4000
    MAX_CHAT_HISTORY = 50
    MAX_CONTEXT_MESSAGES = 10
    
    # Cost Simulator
    MIN_DAYS_UMRAH = 7
    MAX_DAYS_UMRAH = 30
    MIN_PERSONS = 1
    MAX_PERSONS = 50
    
    # User
    MAX_USERNAME_LENGTH = 50
    MIN_PASSWORD_LENGTH = 8
    MAX_LOGIN_ATTEMPTS = 5
    
    # Files
    MAX_UPLOAD_SIZE_MB = 10
    ALLOWED_IMAGE_TYPES = ["png", "jpg", "jpeg", "gif", "webp"]
    
    # Rate Limiting
    API_REQUESTS_PER_MINUTE = 30
    CHAT_REQUESTS_PER_MINUTE = 20
    
    # Pagination
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100


# =============================================================================
# COST CONSTANTS
# =============================================================================

class CostConstants:
    """Cost calculation constants."""
    # Exchange rate (fallback; prefer live rates from kurs_calculator when available)
    SAR_TO_IDR = 4200.0

    # Base costs (IDR)
    VISA_COST = 2_000_000
    HANDLING_FEE = 500_000
    MANASIK_FEE = 300_000
    MUTAWIF_FEE_PER_DAY = 150_000
    TRAVEL_INSURANCE = 350_000
    
    # Airline markups
    AIRLINE_MARKUP_PERCENT = 15
    
    # Hotel rates per night (IDR) - Makkah
    HOTEL_RATES_MAKKAH = {
        HotelStarRating.BUDGET: 800_000,
        HotelStarRating.STANDARD: 1_500_000,
        HotelStarRating.SUPERIOR: 2_500_000,
        HotelStarRating.DELUXE: 4_000_000,
    }
    
    # Hotel rates per night (IDR) - Madinah
    HOTEL_RATES_MADINAH = {
        HotelStarRating.BUDGET: 600_000,
        HotelStarRating.STANDARD: 1_200_000,
        HotelStarRating.SUPERIOR: 2_000_000,
        HotelStarRating.DELUXE: 3_500_000,
    }
    
    # Seasonal multipliers
    SEASONAL_MULTIPLIERS = {
        "low": 1.0,
        "regular": 1.2,
        "high": 1.5,
        "peak": 2.0,  # Ramadan
    }
    
    # Departure city flight costs (IDR)
    FLIGHT_COSTS = {
        "Jakarta": 12_000_000,
        "Surabaya": 13_000_000,
        "Medan": 14_000_000,
        "Makassar": 14_500_000,
        "Bandung": 12_500_000,
        "Semarang": 12_800_000,
        "Yogyakarta": 12_600_000,
        "Palembang": 13_200_000,
        "Balikpapan": 15_000_000,
        "Manado": 16_000_000,
    }


# =============================================================================
# UI CONSTANTS
# =============================================================================

class UIConstants:
    """UI-related constants."""
    # Colors
    PRIMARY_COLOR = "#1B4D3E"  # Islamic Green
    SECONDARY_COLOR = "#C4A747"  # Gold
    ACCENT_COLOR = "#2E7D32"
    BACKGROUND_COLOR = "#F5F5F5"
    TEXT_COLOR = "#333333"
    ERROR_COLOR = "#D32F2F"
    SUCCESS_COLOR = "#388E3C"
    WARNING_COLOR = "#F57C00"
    INFO_COLOR = "#1976D2"
    
    # Fonts
    PRIMARY_FONT = "Poppins"
    SECONDARY_FONT = "Roboto"
    ARABIC_FONT = "Amiri"
    
    # Icons
    ICONS = {
        "home": "🏠",
        "chat": "💬",
        "calculator": "🧮",
        "booking": "📝",
        "group": "👥",
        "guide": "📖",
        "profile": "👤",
        "admin": "⚙️",
        "kaaba": "🕋",
        "mosque": "🕌",
        "prayer": "🤲",
        "quran": "📿",
        "plane": "✈️",
        "hotel": "🏨",
        "calendar": "📅",
        "money": "💰",
        "star": "⭐",
        "heart": "❤️",
        "check": "✅",
        "warning": "⚠️",
        "info": "ℹ️",
        "error": "❌",
    }


# =============================================================================
# MESSAGES & TEMPLATES
# =============================================================================

class Messages:
    """Standard messages and templates."""
    # Greetings
    GREETING_MORNING = "Assalamu'alaikum! Selamat pagi 🌅"
    GREETING_AFTERNOON = "Assalamu'alaikum! Selamat siang ☀️"
    GREETING_EVENING = "Assalamu'alaikum! Selamat sore 🌆"
    GREETING_NIGHT = "Assalamu'alaikum! Selamat malam 🌙"
    
    # System prompts
    SYSTEM_PROMPT = """Anda adalah LABBAIK AI, asisten cerdas untuk perencanaan ibadah Umrah.
    
Tugas Anda:
1. Membantu jamaah merencanakan perjalanan Umrah
2. Memberikan informasi akurat tentang tata cara Umrah
3. Membantu simulasi biaya perjalanan
4. Menjawab pertanyaan seputar Umrah dengan ramah dan informatif

Prinsip:
- Selalu berikan jawaban berdasarkan sumber yang terpercaya
- Dorong pengguna untuk DYOR (Do Your Own Research)
- Gunakan bahasa Indonesia yang baik dan santun
- Sertakan doa atau dzikir yang relevan jika sesuai konteks

Batasan:
- Tidak memberikan fatwa atau keputusan hukum fiqih yang kompleks
- Selalu sarankan untuk berkonsultasi dengan ustadz/ulama untuk masalah fiqih
- Informasi biaya bersifat estimasi dan dapat berubah"""
    
    # Error messages
    ERROR_GENERAL = "Mohon maaf, terjadi kesalahan. Silakan coba lagi."
    ERROR_API = "Layanan sedang sibuk. Silakan coba beberapa saat lagi."
    ERROR_AUTH = "Sesi Anda telah berakhir. Silakan login kembali."
    ERROR_PERMISSION = "Anda tidak memiliki akses ke fitur ini."
    ERROR_VALIDATION = "Data yang dimasukkan tidak valid."
    ERROR_NOT_FOUND = "Data tidak ditemukan."
    
    # Success messages
    SUCCESS_LOGIN = "Berhasil login! Selamat datang kembali."
    SUCCESS_REGISTER = "Registrasi berhasil! Silakan cek email untuk verifikasi."
    SUCCESS_BOOKING = "Booking berhasil dibuat! Tim kami akan menghubungi Anda."
    SUCCESS_SAVE = "Data berhasil disimpan."
    SUCCESS_DELETE = "Data berhasil dihapus."
    
    # Disclaimer
    DISCLAIMER = """⚠️ **DISCLAIMER - PENTING DIBACA**

Informasi yang disediakan LABBAIK AI bersifat edukatif dan referensi umum. 
Kami TIDAK menyediakan layanan perjalanan secara langsung.

✅ Selalu verifikasi informasi dengan sumber resmi
✅ Konsultasikan masalah fiqih dengan ustadz/ulama terpercaya
✅ Periksa harga dan ketersediaan langsung ke travel agent
✅ Pastikan dokumen perjalanan sesuai persyaratan terkini

LABBAIK AI tidak bertanggung jawab atas keputusan yang diambil 
berdasarkan informasi dari platform ini."""


# =============================================================================
# INDONESIAN CITIES DATA
# =============================================================================

INDONESIA_CITIES: List[Dict] = [
    {"name": "Jakarta", "code": "JKT", "airport": "CGK", "province": "DKI Jakarta"},
    {"name": "Surabaya", "code": "SUB", "airport": "SUB", "province": "Jawa Timur"},
    {"name": "Medan", "code": "MES", "airport": "KNO", "province": "Sumatera Utara"},
    {"name": "Makassar", "code": "UPG", "airport": "UPG", "province": "Sulawesi Selatan"},
    {"name": "Bandung", "code": "BDO", "airport": "BDO", "province": "Jawa Barat"},
    {"name": "Semarang", "code": "SRG", "airport": "SRG", "province": "Jawa Tengah"},
    {"name": "Yogyakarta", "code": "JOG", "airport": "YIA", "province": "DI Yogyakarta"},
    {"name": "Palembang", "code": "PLM", "airport": "PLM", "province": "Sumatera Selatan"},
    {"name": "Balikpapan", "code": "BPN", "airport": "BPN", "province": "Kalimantan Timur"},
    {"name": "Manado", "code": "MDC", "airport": "MDC", "province": "Sulawesi Utara"},
    {"name": "Denpasar", "code": "DPS", "airport": "DPS", "province": "Bali"},
    {"name": "Pekanbaru", "code": "PKU", "airport": "PKU", "province": "Riau"},
    {"name": "Padang", "code": "PDG", "airport": "PDG", "province": "Sumatera Barat"},
    {"name": "Banjarmasin", "code": "BDJ", "airport": "BDJ", "province": "Kalimantan Selatan"},
    {"name": "Pontianak", "code": "PNK", "airport": "PNK", "province": "Kalimantan Barat"},
]


# =============================================================================
# UMRAH RITUALS DATA
# =============================================================================

UMRAH_RITUALS: List[Dict] = [
    {
        "order": 1,
        "name": "Ihram",
        "arabic": "إحرام",
        "description": "Niat dan memakai pakaian ihram di miqat",
        "location": "Miqat (Bir Ali/Juhfah/dll)",
        "pillars": ["Niat", "Memakai kain ihram"],
    },
    {
        "order": 2,
        "name": "Tawaf",
        "arabic": "طواف",
        "description": "Mengelilingi Ka'bah sebanyak 7 kali",
        "location": "Masjidil Haram, Makkah",
        "pillars": ["7 putaran", "Dimulai dari Hajar Aswad", "Ka'bah di sebelah kiri"],
    },
    {
        "order": 3,
        "name": "Sai",
        "arabic": "سعي",
        "description": "Berjalan antara bukit Safa dan Marwah 7 kali",
        "location": "Mas'a (antara Safa-Marwah)",
        "pillars": ["7 perjalanan", "Dimulai dari Safa", "Berakhir di Marwah"],
    },
    {
        "order": 4,
        "name": "Tahallul",
        "arabic": "تحلل",
        "description": "Mencukur atau memotong rambut",
        "location": "Area sekitar Masjidil Haram",
        "pillars": ["Mencukur/memotong rambut", "Minimal 3 helai"],
    },
]


# =============================================================================
# PRAYER TIMES CONSTANTS
# =============================================================================

PRAYER_NAMES = {
    "fajr": {"id": "Subuh", "ar": "الفجر"},
    "sunrise": {"id": "Syuruq", "ar": "الشروق"},
    "dhuhr": {"id": "Dzuhur", "ar": "الظهر"},
    "asr": {"id": "Ashar", "ar": "العصر"},
    "maghrib": {"id": "Maghrib", "ar": "المغرب"},
    "isha": {"id": "Isya", "ar": "العشاء"},
}

HOLY_CITIES_COORDS = {
    "makkah": {"lat": 21.4225, "lon": 39.8262, "timezone": "Asia/Riyadh"},
    "madinah": {"lat": 24.4672, "lon": 39.6024, "timezone": "Asia/Riyadh"},
}
