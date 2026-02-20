"""
LABBAIK AI v6.0 - Umrah Bareng SUPER WOW Edition
=================================================
Reclub-style community platform for Umrah travel companions.

Features adapted from Reclub:
- 🏠 Club/Community System (Komunitas Umrah)
- 📅 Meet/Activity Creation (Buat Trip)
- ✅ RSVP + Waitlist System
- ⭐ Experience Rating System
- 🎯 Smart Matchmaking Algorithm
- 🏆 Leaderboard & Stats
- 💬 Real-time Chat
- 🔗 Club Codes for Easy Sharing
- 🔍 Discover with Advanced Filters
- 👤 Rich Player Profiles
- 🏅 Badges & Achievements
- 📊 Analytics Dashboard
"""

import streamlit as st
from datetime import date, datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random
import re
import string
import hashlib
import json

from services.ai.helpers import ai_complete, add_xp_safe
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS
from ui.components import format_idr as format_currency

# =============================================================================
# ENUMS
# =============================================================================

class TripStatus(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    FILLING = "filling"         # > 50% filled
    ALMOST_FULL = "almost_full" # > 80% filled
    FULL = "full"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class RSVPStatus(str, Enum):
    CONFIRMED = "confirmed"
    WAITLISTED = "waitlisted"
    REQUESTED = "requested"
    DECLINED = "declined"
    CANCELLED = "cancelled"


class MemberRole(str, Enum):
    LEADER = "leader"
    CO_LEADER = "co_leader"
    MEMBER = "member"
    GUEST = "guest"


class ExperienceLevel(str, Enum):
    FIRST_TIMER = "first_timer"      # Belum pernah
    BEGINNER = "beginner"            # 1x
    INTERMEDIATE = "intermediate"    # 2-3x
    EXPERIENCED = "experienced"      # 4-5x
    EXPERT = "expert"               # 6+ kali


class TripType(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    GENDER_MEN = "men_only"
    GENDER_WOMEN = "women_only"
    FAMILY = "family"
    YOUTH = "youth"        # 18-35
    SENIOR = "senior"      # 50+
    COUPLE = "couple"      # Pasutri
    PROFESSIONAL = "professional"  # Eksekutif


class TravelStyle(str, Enum):
    IBADAH_INTENSIVE = "ibadah_intensive"
    BALANCED = "balanced"
    ZIARAH_EXPLORER = "ziarah_explorer"
    SHOPPING_FRIENDLY = "shopping"
    PHOTOGRAPHY = "photography"
    RELAXED = "relaxed"
    ADVENTURE = "adventure"


class BudgetRange(str, Enum):
    BACKPACKER = "backpacker"   # < 20 juta
    EKONOMIS = "ekonomis"       # 20-25 juta
    STANDAR = "standar"         # 25-35 juta
    PREMIUM = "premium"         # 35-50 juta
    VIP = "vip"                # 50-75 juta
    LUXURY = "luxury"          # > 75 juta


class BadgeType(str, Enum):
    # Achievement badges
    VERIFIED = "verified"
    FIRST_TRIP = "first_trip"
    VETERAN = "veteran"           # 5+ trips
    ELITE = "elite"               # 10+ trips
    
    # Social badges
    FRIENDLY = "friendly"
    TOP_REVIEWER = "top_reviewer"
    HELPFUL = "helpful"
    COMMUNITY_STAR = "community_star"
    
    # Leader badges
    TOP_LEADER = "top_leader"
    TRUSTED_LEADER = "trusted_leader"
    SUPERHOST = "superhost"
    
    # Special badges
    RAMADAN_WARRIOR = "ramadan_warrior"
    EARLY_BIRD = "early_bird"
    NIGHT_OWL = "night_owl"
    SOCIAL_BUTTERFLY = "social_butterfly"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class UserStats:
    """User statistics for leaderboard."""
    trips_created: int = 0
    trips_joined: int = 0
    trips_completed: int = 0
    total_jamaah_led: int = 0
    reviews_given: int = 0
    reviews_received: int = 0
    avg_rating_given: float = 0.0
    avg_rating_received: float = 0.0
    helpful_votes: int = 0
    response_rate: float = 100.0
    response_time_hours: float = 2.0
    cancellation_rate: float = 0.0
    repeat_travelers: int = 0


@dataclass
class UserProfile:
    """Rich user profile like Reclub."""
    user_id: str
    name: str
    avatar: str
    city: str
    bio: str
    
    # Verification
    is_verified: bool = False
    is_premium: bool = False
    verified_at: Optional[datetime] = None
    
    # Experience
    experience_level: ExperienceLevel = ExperienceLevel.FIRST_TIMER
    umrah_count: int = 0
    first_umrah_year: Optional[int] = None
    
    # Preferences
    preferred_style: TravelStyle = TravelStyle.BALANCED
    preferred_budget: BudgetRange = BudgetRange.STANDAR
    preferred_duration: int = 9
    languages: List[str] = field(default_factory=lambda: ["Indonesia"])
    
    # Social
    followers: int = 0
    following: int = 0
    
    # Stats
    stats: UserStats = field(default_factory=UserStats)
    
    # Badges
    badges: List[BadgeType] = field(default_factory=list)
    
    # Activity
    joined_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    
    # Rating
    rating: float = 0.0
    rating_count: int = 0


@dataclass
class TripMember:
    """Trip member with RSVP status."""
    user_id: str
    name: str
    avatar: str
    role: MemberRole
    rsvp_status: RSVPStatus
    joined_at: datetime
    
    # Profile snapshot
    is_verified: bool = False
    experience_level: ExperienceLevel = ExperienceLevel.FIRST_TIMER
    rating: float = 0.0
    trips_completed: int = 0
    badges: List[BadgeType] = field(default_factory=list)
    
    # Additional
    notes: str = ""
    room_preference: str = "double"
    dietary: str = ""


@dataclass
class TripActivity:
    """Activity log for trip."""
    timestamp: datetime
    user_name: str
    action: str  # joined, left, commented, etc.
    details: str = ""


@dataclass
class ChatMessage:
    """Chat message in trip."""
    id: str
    user_id: str
    user_name: str
    user_avatar: str
    content: str
    timestamp: datetime
    is_system: bool = False
    reactions: Dict[str, int] = field(default_factory=dict)


@dataclass
class Review:
    """Review for trip/leader."""
    id: str
    reviewer_id: str
    reviewer_name: str
    reviewer_avatar: str
    rating: float
    content: str
    timestamp: datetime
    helpful_votes: int = 0
    
    # Categories
    rating_leader: float = 0.0
    rating_experience: float = 0.0
    rating_value: float = 0.0
    rating_communication: float = 0.0


@dataclass
class UmrahTrip:
    """Comprehensive trip data like Reclub meets."""
    id: str
    club_code: str  # Like Reclub's club code for easy sharing
    
    # Basic info
    title: str
    description: str
    
    # Leader
    leader: TripMember
    co_leaders: List[TripMember] = field(default_factory=list)
    
    # Schedule
    departure_city: str = ""
    departure_date: Optional[date] = None
    return_date: Optional[date] = None
    
    # Capacity (like Reclub's confirmed/waitlisted)
    min_members: int = 5
    max_members: int = 15
    
    # Members with different statuses
    confirmed_members: List[TripMember] = field(default_factory=list)
    waitlisted_members: List[TripMember] = field(default_factory=list)
    requested_members: List[TripMember] = field(default_factory=list)
    
    # Preferences
    trip_type: TripType = TripType.PUBLIC
    travel_style: TravelStyle = TravelStyle.BALANCED
    budget_range: BudgetRange = BudgetRange.STANDAR
    experience_required: ExperienceLevel = ExperienceLevel.FIRST_TIMER
    
    # Package details
    package_type: str = "reguler"
    hotel_star: int = 4
    includes_flight: bool = True
    includes_visa: bool = True
    includes_mutawif: bool = True
    includes_meals: bool = True
    
    # Itinerary
    days_makkah: int = 5
    days_madinah: int = 4
    itinerary: List[Dict] = field(default_factory=list)
    
    # Pricing
    price_estimate: int = 30_000_000
    price_includes: List[str] = field(default_factory=list)
    price_excludes: List[str] = field(default_factory=list)
    
    # Status
    status: TripStatus = TripStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Social engagement
    views: int = 0
    likes: int = 0
    shares: int = 0
    saves: int = 0
    
    # Tags for discovery
    tags: List[str] = field(default_factory=list)
    
    # Chat & Activity
    chat_enabled: bool = True
    messages: List[ChatMessage] = field(default_factory=list)
    activities: List[TripActivity] = field(default_factory=list)
    
    # Reviews
    reviews: List[Review] = field(default_factory=list)
    avg_rating: float = 0.0
    
    # Settings
    auto_accept: bool = False
    require_verification: bool = False
    allow_waitlist: bool = True
    notify_on_spot: bool = True


@dataclass
class Community:
    """Community/Club like Reclub."""
    id: str
    code: str  # Club code like "VLFUC"
    name: str
    description: str
    avatar: str
    cover_image: str
    
    # Leader
    owner_id: str
    owner_name: str
    admins: List[str] = field(default_factory=list)
    
    # Members
    member_count: int = 0
    members: List[str] = field(default_factory=list)
    
    # Settings
    is_public: bool = True
    location: str = ""
    focus: str = "All Levels"
    
    # Stats
    trips_created: int = 0
    total_jamaah: int = 0
    avg_rating: float = 0.0
    
    # Trips
    upcoming_trips: List[str] = field(default_factory=list)
    past_trips: List[str] = field(default_factory=list)
    
    created_at: datetime = field(default_factory=datetime.now)


# =============================================================================
# BADGE DEFINITIONS
# =============================================================================

BADGE_INFO = {
    BadgeType.VERIFIED: {
        "icon": "✅",
        "name": "Verified",
        "description": "Identitas terverifikasi",
        "color": "#4CAF50"
    },
    BadgeType.FIRST_TRIP: {
        "icon": "🌟",
        "name": "First Trip",
        "description": "Menyelesaikan trip pertama",
        "color": "#FFC107"
    },
    BadgeType.VETERAN: {
        "icon": "🏆",
        "name": "Veteran",
        "description": "5+ trips selesai",
        "color": "#FF9800"
    },
    BadgeType.ELITE: {
        "icon": "💎",
        "name": "Elite",
        "description": "10+ trips selesai",
        "color": "#9C27B0"
    },
    BadgeType.FRIENDLY: {
        "icon": "🤝",
        "name": "Friendly",
        "description": "Rating keramahan tinggi",
        "color": "#2196F3"
    },
    BadgeType.TOP_REVIEWER: {
        "icon": "⭐",
        "name": "Top Reviewer",
        "description": "Review berkualitas tinggi",
        "color": "#FF5722"
    },
    BadgeType.HELPFUL: {
        "icon": "💡",
        "name": "Helpful",
        "description": "Sering membantu jamaah lain",
        "color": "#00BCD4"
    },
    BadgeType.COMMUNITY_STAR: {
        "icon": "🌠",
        "name": "Community Star",
        "description": "Kontributor aktif komunitas",
        "color": "#E91E63"
    },
    BadgeType.TOP_LEADER: {
        "icon": "👑",
        "name": "Top Leader",
        "description": "Leader dengan rating tertinggi",
        "color": "#FFD700"
    },
    BadgeType.TRUSTED_LEADER: {
        "icon": "🛡️",
        "name": "Trusted Leader",
        "description": "Leader terpercaya",
        "color": "#3F51B5"
    },
    BadgeType.SUPERHOST: {
        "icon": "🏅",
        "name": "Superhost",
        "description": "Leader dengan 20+ trips sukses",
        "color": "#F44336"
    },
    BadgeType.RAMADAN_WARRIOR: {
        "icon": "🌙",
        "name": "Ramadan Warrior",
        "description": "Umrah saat Ramadan",
        "color": "#673AB7"
    },
    BadgeType.EARLY_BIRD: {
        "icon": "🌅",
        "name": "Early Bird",
        "description": "Selalu booking 3+ bulan sebelumnya",
        "color": "#8BC34A"
    },
    BadgeType.SOCIAL_BUTTERFLY: {
        "icon": "🦋",
        "name": "Social Butterfly",
        "description": "50+ koneksi dalam platform",
        "color": "#FF4081"
    },
}


# =============================================================================
# PAGE-SPECIFIC CSS
# =============================================================================

PAGE_CSS = """
/* Umrah Bareng hero overrides */
:root {
    --hero-bg: linear-gradient(135deg, #0d1b2a 0%, #1b2a4a 60%, #2a1a4a 100%);
    --hero-border: #d4af37;
    --hero-title: #d4af37;
    --hero-subtitle: #94a3b8;
}

/* Stat cards row */
.ub-stats-row {
    display: flex;
    gap: 1rem;
    margin-bottom: 1.5rem;
}

.ub-stat-card {
    flex: 1;
    text-align: center;
    padding: 1.25rem 0.75rem;
    background: linear-gradient(145deg, #1a1a2e 0%, #1e293b 100%);
    border-radius: 15px;
    border: 1px solid #333;
    transition: transform 0.2s ease;
}

.ub-stat-card:hover {
    transform: translateY(-2px);
}

.ub-stat-card .number {
    font-size: 1.6rem;
    font-weight: bold;
}

.ub-stat-card .label {
    color: #94a3b8;
    font-size: 0.78rem;
    margin-top: 0.25rem;
}

/* AI recommendation section */
.ub-ai-section {
    margin-top: 1.5rem;
    margin-bottom: 1.5rem;
}

.ub-ai-prompt-card {
    background: linear-gradient(145deg, #1a2e1a 0%, #1a3a1a 100%);
    border: 1px solid #228B22;
    border-radius: 15px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}

.ub-ai-prompt-card h4 {
    color: #4ade80;
    margin: 0 0 0.5rem 0;
}

.ub-ai-prompt-card p {
    color: #94a3b8;
    font-size: 0.9rem;
    margin: 0;
}

/* Match score badge */
.ub-match-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 12px;
    font-size: 0.8rem;
    font-weight: bold;
}

.ub-match-high {
    background: #1a3a1a;
    color: #4ade80;
    border: 1px solid #228B22;
}

.ub-match-med {
    background: #3a3a1a;
    color: #fbbf24;
    border: 1px solid #b8860b;
}

.ub-match-low {
    background: #2a1a1a;
    color: #f87171;
    border: 1px solid #8b0000;
}

/* XP toast notification */
.ub-xp-toast {
    background: linear-gradient(135deg, #1a3a1a, #2a4a2a);
    border: 1px solid #4ade80;
    border-radius: 10px;
    padding: 0.75rem 1rem;
    color: #4ade80;
    font-weight: bold;
    text-align: center;
    margin: 0.5rem 0;
}
"""


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def generate_club_code() -> str:
    """Generate unique club code like Reclub."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))


def generate_trip_id() -> str:
    """Generate unique trip ID."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"trip_{timestamp}_{random_suffix}"


def format_relative_time(dt: datetime) -> str:
    """Format datetime as relative time."""
    now = datetime.now()
    diff = now - dt
    
    if diff.days > 30:
        return dt.strftime("%d %b %Y")
    elif diff.days > 0:
        return f"{diff.days} hari lalu"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} jam lalu"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} menit lalu"
    else:
        return "Baru saja"


def get_experience_label(level: ExperienceLevel) -> Tuple[str, str]:
    """Get label and icon for experience level."""
    labels = {
        ExperienceLevel.FIRST_TIMER: ("🆕", "First Timer"),
        ExperienceLevel.BEGINNER: ("🌱", "Beginner (1x)"),
        ExperienceLevel.INTERMEDIATE: ("🌿", "Intermediate (2-3x)"),
        ExperienceLevel.EXPERIENCED: ("🌳", "Experienced (4-5x)"),
        ExperienceLevel.EXPERT: ("🏆", "Expert (6+x)"),
    }
    return labels.get(level, ("❓", "Unknown"))


def get_trip_type_label(trip_type: TripType) -> Tuple[str, str]:
    """Get label and icon for trip type."""
    labels = {
        TripType.PUBLIC: ("🌐", "Publik"),
        TripType.PRIVATE: ("🔒", "Private"),
        TripType.GENDER_MEN: ("👨", "Khusus Pria"),
        TripType.GENDER_WOMEN: ("👩", "Khusus Wanita"),
        TripType.FAMILY: ("👨‍👩‍👧‍👦", "Keluarga"),
        TripType.YOUTH: ("🔥", "Muda (18-35)"),
        TripType.SENIOR: ("🤲", "Senior (50+)"),
        TripType.COUPLE: ("💑", "Pasutri"),
        TripType.PROFESSIONAL: ("💼", "Eksekutif"),
    }
    return labels.get(trip_type, ("❓", "Unknown"))


def get_style_label(style: TravelStyle) -> Tuple[str, str]:
    """Get label and icon for travel style."""
    labels = {
        TravelStyle.IBADAH_INTENSIVE: ("📿", "Fokus Ibadah"),
        TravelStyle.BALANCED: ("⚖️", "Seimbang"),
        TravelStyle.ZIARAH_EXPLORER: ("🕌", "Ziarah Explorer"),
        TravelStyle.SHOPPING_FRIENDLY: ("🛍️", "Shopping Friendly"),
        TravelStyle.PHOTOGRAPHY: ("📸", "Photography"),
        TravelStyle.RELAXED: ("🧘", "Santai"),
        TravelStyle.ADVENTURE: ("⛰️", "Petualangan"),
    }
    return labels.get(style, ("❓", "Unknown"))


def get_budget_label(budget: BudgetRange) -> Tuple[str, str, str]:
    """Get label, icon, and range for budget."""
    labels = {
        BudgetRange.BACKPACKER: ("🎒", "Backpacker", "< 20 Juta"),
        BudgetRange.EKONOMIS: ("💚", "Ekonomis", "20-25 Juta"),
        BudgetRange.STANDAR: ("💙", "Standar", "25-35 Juta"),
        BudgetRange.PREMIUM: ("💜", "Premium", "35-50 Juta"),
        BudgetRange.VIP: ("💛", "VIP", "50-75 Juta"),
        BudgetRange.LUXURY: ("👑", "Luxury", "> 75 Juta"),
    }
    return labels.get(budget, ("❓", "Unknown", "N/A"))


def calculate_match_score(trip: UmrahTrip, preferences: Dict) -> int:
    """Calculate match score with weighted factors."""
    score = 0
    weights = {
        "city": 25,
        "budget": 20,
        "style": 15,
        "type": 15,
        "experience": 10,
        "date": 15,
    }
    
    # City match
    if preferences.get("city") and trip.departure_city == preferences["city"]:
        score += weights["city"]
    
    # Budget match
    if preferences.get("budget"):
        if trip.budget_range.value == preferences["budget"]:
            score += weights["budget"]
        # Partial match for adjacent budgets
        budget_order = list(BudgetRange)
        try:
            trip_idx = budget_order.index(trip.budget_range)
            pref_idx = next(i for i, b in enumerate(budget_order) if b.value == preferences["budget"])
            if abs(trip_idx - pref_idx) == 1:
                score += weights["budget"] // 2
        except (ValueError, StopIteration):
            pass
    
    # Style match
    if preferences.get("style") and trip.travel_style.value == preferences["style"]:
        score += weights["style"]
    
    # Type match
    if preferences.get("type") and trip.trip_type.value == preferences["type"]:
        score += weights["type"]
    
    # Experience match
    if preferences.get("experience"):
        exp_order = list(ExperienceLevel)
        try:
            trip_idx = exp_order.index(trip.experience_required)
            pref_idx = next(i for i, e in enumerate(exp_order) if e.value == preferences["experience"])
            if pref_idx >= trip_idx:  # User meets or exceeds requirement
                score += weights["experience"]
        except (ValueError, StopIteration):
            pass
    
    # Date range match
    if preferences.get("date_from") and preferences.get("date_to") and trip.departure_date:
        if preferences["date_from"] <= trip.departure_date <= preferences["date_to"]:
            score += weights["date"]
    
    return min(score, 100)


def get_trip_fill_status(trip: UmrahTrip) -> Tuple[str, str, float]:
    """Get fill status with color and percentage."""
    confirmed = len(trip.confirmed_members)
    max_cap = trip.max_members
    pct = confirmed / max_cap if max_cap > 0 else 0
    
    if pct >= 1.0:
        return "🔴", "Full", pct
    elif pct >= 0.8:
        return "🟠", "Almost Full", pct
    elif pct >= 0.5:
        return "🟡", "Filling Fast", pct
    elif pct >= 0.2:
        return "🟢", "Open", pct
    else:
        return "⚪", "New", pct


# =============================================================================
# MOCK DATA GENERATORS
# =============================================================================

def generate_mock_users(count: int = 50) -> List[UserProfile]:
    """Generate mock user profiles."""
    names = [
        "Ahmad Fauzi", "Siti Nurhaliza", "Budi Santoso", "Dewi Kartika",
        "Muhammad Rizki", "Fatimah Zahra", "Hasan Abdullah", "Aisyah Putri",
        "Umar Faruq", "Khadijah Sari", "Ali Rahman", "Nurul Hidayah",
        "Yusuf Mansur", "Aminah Salsabila", "Ibrahim Hakim", "Zahra Aulia",
        "Hamzah Wijaya", "Maryam Azzahra", "Ismail Pratama", "Halimah Kusuma"
    ]
    
    cities = ["Jakarta", "Surabaya", "Bandung", "Medan", "Makassar", 
              "Semarang", "Yogyakarta", "Palembang", "Balikpapan", "Pekanbaru"]
    
    bios = [
        "Pecinta perjalanan spiritual 🕋",
        "Alhamdulillah sudah berkali-kali ke Baitullah",
        "Berbagi pengalaman umrah dengan sesama Muslim",
        "Mencari teman perjalanan yang sefrekuensi",
        "Semoga bisa terus kembali ke tanah suci",
    ]
    
    users = []
    for i in range(count):
        name = random.choice(names)
        exp = random.choice(list(ExperienceLevel))
        umrah_count = {
            ExperienceLevel.FIRST_TIMER: 0,
            ExperienceLevel.BEGINNER: 1,
            ExperienceLevel.INTERMEDIATE: random.randint(2, 3),
            ExperienceLevel.EXPERIENCED: random.randint(4, 5),
            ExperienceLevel.EXPERT: random.randint(6, 15),
        }[exp]
        
        badges = []
        if random.random() > 0.3:
            badges.append(BadgeType.VERIFIED)
        if umrah_count >= 5:
            badges.append(BadgeType.VETERAN)
        if umrah_count >= 10:
            badges.append(BadgeType.ELITE)
        if random.random() > 0.7:
            badges.append(random.choice([BadgeType.FRIENDLY, BadgeType.HELPFUL, BadgeType.TOP_REVIEWER]))
        
        stats = UserStats(
            trips_created=random.randint(0, 10),
            trips_joined=random.randint(0, 20),
            trips_completed=umrah_count,
            total_jamaah_led=random.randint(0, 100),
            reviews_given=random.randint(0, 30),
            reviews_received=random.randint(0, 50),
            avg_rating_received=round(random.uniform(4.0, 5.0), 1),
            response_rate=round(random.uniform(85, 100), 0),
            response_time_hours=round(random.uniform(0.5, 24), 1),
        )
        
        user = UserProfile(
            user_id=f"user_{i}_{random.randint(1000, 9999)}",
            name=name,
            avatar=f"https://api.dicebear.com/7.x/avataaars/svg?seed={name.replace(' ', '')}{i}",
            city=random.choice(cities),
            bio=random.choice(bios),
            is_verified=BadgeType.VERIFIED in badges,
            is_premium=random.random() > 0.8,
            experience_level=exp,
            umrah_count=umrah_count,
            preferred_style=random.choice(list(TravelStyle)),
            preferred_budget=random.choice(list(BudgetRange)),
            followers=random.randint(0, 500),
            following=random.randint(0, 300),
            stats=stats,
            badges=badges,
            rating=stats.avg_rating_received,
            rating_count=stats.reviews_received,
        )
        users.append(user)
    
    return users


def generate_mock_trips(users: List[UserProfile], count: int = 30) -> List[UmrahTrip]:
    """Generate mock trips."""
    titles = [
        "Umrah Ramadan Penuh Berkah 🌙",
        "Umrah Hemat Backpacker Style 🎒",
        "Umrah Keluarga Bahagia 👨‍👩‍👧‍👦",
        "Umrah Bersama Ustadz Terkenal 📿",
        "Umrah Eksekutif VIP ⭐",
        "Umrah Muda Penuh Semangat 🔥",
        "Umrah Lansia Nyaman & Aman 🤲",
        "Umrah Plus Turki & Dubai 🌍",
        "Umrah Awal Tahun Fresh Start ✨",
        "Umrah Liburan Sekolah 📚",
        "Umrah Spiritualis Deep Connection 🤲",
        "Umrah Photography Tour 📸",
        "Umrah Shopping Paradise 🛍️",
        "Umrah First Timer Friendly 🌟",
        "Umrah Weekend Warriors 💪",
    ]
    
    descriptions = [
        "Mari bergabung dalam perjalanan umrah yang penuh berkah! Kami akan berangkat dengan fasilitas lengkap dan bimbingan mutawif berpengalaman. InsyaAllah perjalanan ini akan menjadi pengalaman spiritual yang tak terlupakan.",
        "Untuk Anda yang ingin umrah dengan budget terjangkau namun tetap nyaman. Kami fokus pada ibadah dengan fasilitas yang cukup dan bimbingan yang baik.",
        "Trip ini dirancang untuk keluarga dengan berbagai usia. Ada program khusus untuk anak-anak dan kemudahan untuk lansia. Mari umrah bersama keluarga tercinta!",
        "Perjalanan umrah dengan pendampingan ustadz yang akan membimbing setiap ritual dan memberikan tausiyah sepanjang perjalanan.",
    ]
    
    cities = ["Jakarta", "Surabaya", "Bandung", "Medan", "Makassar", "Semarang", "Yogyakarta"]
    
    trips = []
    for i in range(count):
        leader_user = random.choice(users)
        dep_date = date.today() + timedelta(days=random.randint(30, 180))
        duration = random.choice([9, 10, 12, 14])
        
        leader = TripMember(
            user_id=leader_user.user_id,
            name=leader_user.name,
            avatar=leader_user.avatar,
            role=MemberRole.LEADER,
            rsvp_status=RSVPStatus.CONFIRMED,
            joined_at=datetime.now() - timedelta(days=random.randint(1, 30)),
            is_verified=leader_user.is_verified,
            experience_level=leader_user.experience_level,
            rating=leader_user.rating,
            trips_completed=leader_user.umrah_count,
            badges=leader_user.badges,
        )
        
        max_members = random.choice([10, 15, 20, 25, 30, 45])
        confirmed_count = random.randint(1, max_members - 1)
        waitlist_count = random.randint(0, 10) if confirmed_count >= max_members * 0.8 else 0
        
        # Generate confirmed members
        confirmed = [leader]
        for j in range(confirmed_count - 1):
            member_user = random.choice(users)
            member = TripMember(
                user_id=member_user.user_id,
                name=member_user.name,
                avatar=member_user.avatar,
                role=MemberRole.MEMBER,
                rsvp_status=RSVPStatus.CONFIRMED,
                joined_at=datetime.now() - timedelta(days=random.randint(0, 20)),
                is_verified=member_user.is_verified,
                experience_level=member_user.experience_level,
                rating=member_user.rating,
                trips_completed=member_user.umrah_count,
            )
            confirmed.append(member)
        
        # Generate waitlisted
        waitlisted = []
        for j in range(waitlist_count):
            member_user = random.choice(users)
            member = TripMember(
                user_id=member_user.user_id,
                name=member_user.name,
                avatar=member_user.avatar,
                role=MemberRole.MEMBER,
                rsvp_status=RSVPStatus.WAITLISTED,
                joined_at=datetime.now() - timedelta(days=random.randint(0, 10)),
                is_verified=member_user.is_verified,
                experience_level=member_user.experience_level,
                rating=member_user.rating,
            )
            waitlisted.append(member)
        
        # Determine status
        fill_pct = confirmed_count / max_members
        if fill_pct >= 1.0:
            status = TripStatus.FULL
        elif fill_pct >= 0.8:
            status = TripStatus.ALMOST_FULL
        elif fill_pct >= 0.5:
            status = TripStatus.FILLING
        else:
            status = TripStatus.OPEN
        
        budget = random.choice(list(BudgetRange))
        price_map = {
            BudgetRange.BACKPACKER: random.randint(15, 20) * 1_000_000,
            BudgetRange.EKONOMIS: random.randint(20, 25) * 1_000_000,
            BudgetRange.STANDAR: random.randint(25, 35) * 1_000_000,
            BudgetRange.PREMIUM: random.randint(35, 50) * 1_000_000,
            BudgetRange.VIP: random.randint(50, 75) * 1_000_000,
            BudgetRange.LUXURY: random.randint(75, 120) * 1_000_000,
        }
        
        trip = UmrahTrip(
            id=generate_trip_id(),
            club_code=generate_club_code(),
            title=random.choice(titles),
            description=random.choice(descriptions),
            leader=leader,
            departure_city=random.choice(cities),
            departure_date=dep_date,
            return_date=dep_date + timedelta(days=duration),
            min_members=random.choice([5, 10]),
            max_members=max_members,
            confirmed_members=confirmed,
            waitlisted_members=waitlisted,
            trip_type=random.choice(list(TripType)),
            travel_style=random.choice(list(TravelStyle)),
            budget_range=budget,
            experience_required=random.choice(list(ExperienceLevel)),
            hotel_star=random.choice([3, 4, 5]),
            days_makkah=random.choice([4, 5, 6]),
            days_madinah=random.choice([3, 4, 5]),
            price_estimate=price_map[budget],
            status=status,
            created_at=datetime.now() - timedelta(days=random.randint(1, 60)),
            views=random.randint(50, 5000),
            likes=random.randint(0, 500),
            shares=random.randint(0, 100),
            saves=random.randint(0, 200),
            tags=random.sample(["ramadan", "hemat", "keluarga", "muda", "premium", 
                               "ziarah", "backpacker", "photography", "spiritual",
                               "first-timer", "experienced", "vip"], k=random.randint(2, 5)),
            avg_rating=round(random.uniform(4.0, 5.0), 1) if random.random() > 0.3 else 0,
        )
        trips.append(trip)
    
    return trips


def generate_mock_communities(users: List[UserProfile], count: int = 10) -> List[Community]:
    """Generate mock communities."""
    community_names = [
        ("Umrah Jakarta Community", "Komunitas jamaah umrah dari Jakarta dan sekitarnya"),
        ("Backpacker Umrah Indonesia", "Untuk yang suka umrah hemat dan mandiri"),
        ("Umrah Keluarga Indonesia", "Komunitas keluarga yang suka umrah bersama"),
        ("Muslim Professional Umrah", "Eksekutif dan profesional Muslim"),
        ("Umrah First Timer Support", "Dukungan untuk yang baru pertama kali"),
        ("Umrah Photography Club", "Pecinta fotografi saat umrah"),
        ("Umrah Muda Indonesia", "Komunitas anak muda pecinta umrah"),
        ("Umrah Lansia Care", "Komunitas lansia dengan pendampingan khusus"),
    ]
    
    communities = []
    for i, (name, desc) in enumerate(community_names[:count]):
        owner = random.choice(users)
        
        community = Community(
            id=f"comm_{i}_{random.randint(1000, 9999)}",
            code=generate_club_code(),
            name=name,
            description=desc,
            avatar=f"https://api.dicebear.com/7.x/identicon/svg?seed={name.replace(' ', '')}",
            cover_image=f"https://picsum.photos/seed/{i}/800/200",
            owner_id=owner.user_id,
            owner_name=owner.name,
            member_count=random.randint(50, 2000),
            is_public=random.random() > 0.2,
            location=random.choice(["Jakarta", "Surabaya", "All Indonesia"]),
            trips_created=random.randint(5, 50),
            total_jamaah=random.randint(100, 5000),
            avg_rating=round(random.uniform(4.0, 5.0), 1),
        )
        communities.append(community)
    
    return communities


def generate_current_user() -> UserProfile:
    """Generate current user profile."""
    return UserProfile(
        user_id="current_user_001",
        name="Sopian",
        avatar="https://api.dicebear.com/7.x/avataaars/svg?seed=sopian",
        city="Jakarta",
        bio="Founder LABBAIK AI 🕋 | Pecinta perjalanan spiritual | Sudah 3x umrah, ingin berbagi pengalaman dan mencari teman perjalanan yang sefrekuensi.",
        is_verified=True,
        is_premium=True,
        experience_level=ExperienceLevel.INTERMEDIATE,
        umrah_count=3,
        first_umrah_year=2019,
        preferred_style=TravelStyle.BALANCED,
        preferred_budget=BudgetRange.STANDAR,
        followers=256,
        following=189,
        stats=UserStats(
            trips_created=2,
            trips_joined=5,
            trips_completed=3,
            total_jamaah_led=45,
            reviews_given=8,
            reviews_received=12,
            avg_rating_received=4.8,
            response_rate=98,
            response_time_hours=1.5,
        ),
        badges=[
            BadgeType.VERIFIED,
            BadgeType.FRIENDLY,
            BadgeType.TOP_REVIEWER,
            BadgeType.TRUSTED_LEADER,
        ],
        rating=4.8,
        rating_count=12,
    )


# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

def init_umrah_bareng_state():
    """Initialize all session state for Umrah Bareng."""
    
    # Generate mock data if not exists
    if "ub_users" not in st.session_state:
        st.session_state.ub_users = generate_mock_users(50)
    
    if "ub_trips" not in st.session_state:
        st.session_state.ub_trips = generate_mock_trips(st.session_state.ub_users, 30)
    
    if "ub_communities" not in st.session_state:
        st.session_state.ub_communities = generate_mock_communities(st.session_state.ub_users, 8)
    
    if "ub_current_user" not in st.session_state:
        st.session_state.ub_current_user = generate_current_user()
    
    # Navigation state
    if "ub_view" not in st.session_state:
        st.session_state.ub_view = "discover"
    
    if "ub_selected_trip" not in st.session_state:
        st.session_state.ub_selected_trip = None
    
    if "ub_selected_community" not in st.session_state:
        st.session_state.ub_selected_community = None
    
    if "ub_selected_user" not in st.session_state:
        st.session_state.ub_selected_user = None
    
    # Filter state
    if "ub_filters" not in st.session_state:
        st.session_state.ub_filters = {}
    
    # User's trips
    if "ub_my_trips" not in st.session_state:
        st.session_state.ub_my_trips = []
    
    if "ub_joined_trips" not in st.session_state:
        st.session_state.ub_joined_trips = []
    
    if "ub_saved_trips" not in st.session_state:
        st.session_state.ub_saved_trips = []
    
    # Notifications
    if "ub_notifications" not in st.session_state:
        st.session_state.ub_notifications = [
            {"type": "join_request", "message": "Ahmad ingin bergabung dengan trip Anda", "time": datetime.now() - timedelta(minutes=5), "read": False},
            {"type": "message", "message": "Pesan baru di grup Umrah Ramadan", "time": datetime.now() - timedelta(hours=1), "read": False},
            {"type": "reminder", "message": "Trip Anda berangkat dalam 30 hari!", "time": datetime.now() - timedelta(hours=2), "read": True},
            {"type": "system", "message": "Selamat! Anda mendapat badge Friendly 🤝", "time": datetime.now() - timedelta(days=1), "read": True},
        ]
    
    # Create trip wizard state
    if "ub_create_step" not in st.session_state:
        st.session_state.ub_create_step = 1

    if "ub_create_data" not in st.session_state:
        st.session_state.ub_create_data = {}

    # Gamification XP tracking
    if "ub_xp_group_action" not in st.session_state:
        st.session_state.ub_xp_group_action = False
    if "ub_xp_ai_recommendation" not in st.session_state:
        st.session_state.ub_xp_ai_recommendation = False

    # AI recommendation state
    if "ub_ai_response" not in st.session_state:
        st.session_state.ub_ai_response = None


# =============================================================================
# NAVIGATION HELPERS
# =============================================================================

def navigate_to(view: str, **kwargs):
    """Navigate to a view with optional parameters."""
    st.session_state.ub_view = view
    for key, value in kwargs.items():
        st.session_state[f"ub_{key}"] = value


# =============================================================================
# UI COMPONENTS - HEADER & NAVIGATION
# =============================================================================

def render_header():
    """Render app header with search and notifications."""
    col1, col2, col3, col4, col5 = st.columns([2, 4, 1, 1, 1])
    
    with col1:
        st.markdown("### 🕋 Umrah Bareng")
    
    with col2:
        search = st.text_input(
            "search",
            placeholder="🔍 Cari trip, komunitas, atau jamaah...",
            label_visibility="collapsed",
            key="header_search"
        )
        if search:
            st.session_state.ub_filters["search"] = search
    
    with col3:
        # Saved trips
        saved_count = len(st.session_state.ub_saved_trips)
        if st.button(f"💾 {saved_count}", key="btn_saved", help="Trip tersimpan"):
            navigate_to("saved")
            st.rerun()
    
    with col4:
        # Notifications
        notifs = st.session_state.ub_notifications
        unread = sum(1 for n in notifs if not n.get("read", True))
        badge = f"🔴{unread}" if unread > 0 else ""
        if st.button(f"🔔{badge}", key="btn_notif", help="Notifikasi"):
            navigate_to("notifications")
            st.rerun()
    
    with col5:
        # Profile
        user = st.session_state.ub_current_user
        if st.button(f"👤", key="btn_profile", help=user.name):
            navigate_to("profile", selected_user=user)
            st.rerun()


def render_sidebar():
    """Render sidebar navigation."""
    with st.sidebar:
        user = st.session_state.ub_current_user
        
        # User card
        with st.container(border=True):
            col1, col2 = st.columns([1, 2])
            with col1:
                st.image(user.avatar, width=60)
            with col2:
                verified = "✅" if user.is_verified else ""
                premium = "⭐" if user.is_premium else ""
                st.markdown(f"**{user.name}** {verified}{premium}")
                exp_icon, exp_label = get_experience_label(user.experience_level)
                st.caption(f"{exp_icon} {exp_label}")
                st.caption(f"⭐ {user.rating} ({user.rating_count} reviews)")
        
        st.divider()
        
        # Main navigation
        st.markdown("### 🧭 Menu")
        
        nav_items = [
            ("discover", "🔍 Discover", "Temukan trips"),
            ("communities", "🏘️ Communities", "Komunitas"),
            ("create", "➕ Buat Trip", "Buat trip baru"),
            ("my_trips", "📋 Trip Saya", "Kelola trips"),
            ("match", "🎯 Smart Match", "Rekomendasi"),
            ("leaderboard", "🏆 Leaderboard", "Peringkat"),
            ("messages", "💬 Messages", "Chat"),
        ]
        
        current_view = st.session_state.ub_view
        
        for view_id, label, help_text in nav_items:
            btn_type = "primary" if current_view == view_id else "secondary"
            if st.button(label, key=f"nav_{view_id}", help=help_text, use_container_width=True, type=btn_type):
                navigate_to(view_id)
                st.rerun()
        
        st.divider()
        
        # Quick stats
        st.markdown("### 📊 Stats Anda")
        
        stats = user.stats
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Trips", stats.trips_completed, help="Total trips selesai")
            st.metric("Followers", user.followers)
        with col2:
            st.metric("Rating", f"⭐{user.rating}")
            st.metric("Following", user.following)
        
        # Badges
        if user.badges:
            st.markdown("### 🏅 Badges")
            badges_html = ""
            for badge in user.badges[:6]:
                info = BADGE_INFO.get(badge, {})
                badges_html += f"{info.get('icon', '🏅')} "
            st.markdown(badges_html)
        
        st.divider()
        
        # Join by code
        st.markdown("### 🔗 Join Trip")
        code_input = st.text_input(
            "Club Code",
            placeholder="Masukkan kode (cth: ABC12)",
            max_chars=5,
            label_visibility="collapsed"
        )
        if code_input:
            trips = st.session_state.ub_trips
            found = next((t for t in trips if t.club_code.upper() == code_input.upper()), None)
            if found:
                st.success(f"✅ Ditemukan: {found.title}")
                if st.button("Lihat Trip", type="primary"):
                    navigate_to("trip_detail", selected_trip=found)
                    st.rerun()
            else:
                st.error("❌ Kode tidak ditemukan")


# =============================================================================
# UI COMPONENTS - CARDS & WIDGETS
# =============================================================================

def render_trip_card(trip: UmrahTrip, show_match_score: bool = False, compact: bool = False):
    """Render a trip card like Reclub's meet card."""
    
    with st.container(border=True):
        # Status indicator & title
        status_icon, status_text, fill_pct = get_trip_fill_status(trip)
        
        col1, col2, col3 = st.columns([5, 2, 1])
        
        with col1:
            st.markdown(f"### {status_icon} {trip.title}")
        
        with col2:
            if show_match_score:
                score = calculate_match_score(trip, st.session_state.ub_filters)
                if score >= 75:
                    st.success(f"🎯 {score}% Match")
                elif score >= 50:
                    st.warning(f"🎯 {score}% Match")
                else:
                    st.info(f"🎯 {score}% Match")
        
        with col3:
            # Save button
            saved = trip.id in st.session_state.ub_saved_trips
            save_icon = "💾" if saved else "🤍"
            if st.button(save_icon, key=f"save_{trip.id}", help="Simpan"):
                if saved:
                    st.session_state.ub_saved_trips.remove(trip.id)
                else:
                    st.session_state.ub_saved_trips.append(trip.id)
                st.rerun()
        
        # Club code for sharing
        st.caption(f"📋 Kode: **{trip.club_code}** | 📍 {trip.departure_city}")
        
        if not compact:
            # Leader info
            col1, col2, col3 = st.columns([1, 3, 2])
            
            with col1:
                st.image(trip.leader.avatar, width=50)
            
            with col2:
                verified = "✅" if trip.leader.is_verified else ""
                st.markdown(f"**{trip.leader.name}** {verified}")
                exp_icon, exp_label = get_experience_label(trip.leader.experience_level)
                st.caption(f"⭐ {trip.leader.rating} · {exp_icon} {trip.leader.trips_completed} trips")
            
            with col3:
                if trip.departure_date:
                    st.markdown(f"📅 **{trip.departure_date.strftime('%d %b %Y')}**")
                    duration = (trip.return_date - trip.departure_date).days if trip.return_date else 0
                    st.caption(f"{duration} hari")
        
        # Trip details badges
        type_icon, type_label = get_trip_type_label(trip.trip_type)
        style_icon, style_label = get_style_label(trip.travel_style)
        budget_icon, budget_label, _ = get_budget_label(trip.budget_range)
        
        st.markdown(f"{type_icon} {type_label} | {style_icon} {style_label} | {budget_icon} {budget_label} | 🏨 {trip.hotel_star}⭐")
        
        # Capacity bar (like Reclub's confirmed/waitlisted)
        confirmed = len(trip.confirmed_members)
        waitlisted = len(trip.waitlisted_members)
        
        st.progress(fill_pct, text=f"👥 **{confirmed}** Confirmed · **{waitlisted}** Waitlisted")
        
        col1, col2 = st.columns(2)
        with col1:
            st.caption(f"{trip.max_members - confirmed} slot tersisa")
        with col2:
            st.caption(f"💰 {format_currency(trip.price_estimate)}")
        
        # Tags
        if trip.tags:
            tags_html = " ".join([f"`{tag}`" for tag in trip.tags[:5]])
            st.markdown(tags_html)
        
        # Actions
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.caption(f"❤️ {trip.likes}")
        with col2:
            st.caption(f"👁️ {trip.views}")
        with col3:
            if st.button("💬", key=f"chat_{trip.id}", help="Chat"):
                navigate_to("trip_detail", selected_trip=trip)
                st.rerun()
        with col4:
            if trip.status in [TripStatus.OPEN, TripStatus.FILLING, TripStatus.ALMOST_FULL]:
                if st.button("🚀 Join", key=f"join_{trip.id}", type="primary"):
                    # Gamification: award XP for first group join
                    if not st.session_state.get("ub_xp_group_action", False):
                        st.session_state.ub_xp_group_action = True
                        add_xp_safe(25, "Bergabung grup Umrah Bareng")
                    navigate_to("trip_detail", selected_trip=trip)
                    st.rerun()
            else:
                st.button("Full", key=f"full_{trip.id}", disabled=True)


def render_user_card(user: UserProfile, compact: bool = False):
    """Render a user profile card."""
    
    with st.container(border=True):
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col1:
            st.image(user.avatar, width=60 if not compact else 40)
        
        with col2:
            verified = "✅" if user.is_verified else ""
            premium = "⭐" if user.is_premium else ""
            st.markdown(f"**{user.name}** {verified}{premium}")
            
            exp_icon, exp_label = get_experience_label(user.experience_level)
            st.caption(f"{exp_icon} {exp_label} · 📍 {user.city}")
            
            if not compact:
                st.caption(f"⭐ {user.rating} ({user.rating_count}) · 👥 {user.followers} followers")
                
                # Badges
                if user.badges:
                    badges = " ".join([BADGE_INFO[b]["icon"] for b in user.badges[:4]])
                    st.markdown(badges)
        
        with col3:
            if st.button("👤", key=f"view_user_{user.user_id}", help="Lihat profil"):
                navigate_to("profile", selected_user=user)
                st.rerun()


def render_community_card(community: Community):
    """Render a community card."""
    
    with st.container(border=True):
        col1, col2 = st.columns([1, 4])
        
        with col1:
            st.image(community.avatar, width=60)
        
        with col2:
            st.markdown(f"### {community.name}")
            st.caption(f"📋 Kode: **{community.code}** | 📍 {community.location}")
            st.caption(community.description[:100] + "..." if len(community.description) > 100 else community.description)
            
            col_a, col_b, col_c, col_d = st.columns(4)
            with col_a:
                st.metric("Members", f"{community.member_count:,}", label_visibility="collapsed")
                st.caption("members")
            with col_b:
                st.metric("Trips", community.trips_created, label_visibility="collapsed")
                st.caption("trips")
            with col_c:
                st.metric("Rating", f"⭐{community.avg_rating}", label_visibility="collapsed")
                st.caption("rating")
            with col_d:
                if st.button("Join", key=f"join_comm_{community.id}", type="primary"):
                    # Gamification: award XP for first group join
                    if not st.session_state.get("ub_xp_group_action", False):
                        st.session_state.ub_xp_group_action = True
                        add_xp_safe(25, "Bergabung komunitas Umrah Bareng")
                    st.success("✅ Bergabung!")


def render_filters_panel():
    """Render advanced filters panel."""
    
    with st.expander("🎯 Filter & Preferensi", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        
        cities = ["Semua", "Jakarta", "Surabaya", "Bandung", "Medan", "Makassar", "Semarang", "Yogyakarta"]
        
        with col1:
            city = st.selectbox("🏙️ Kota", cities, key="filter_city")
            if city != "Semua":
                st.session_state.ub_filters["city"] = city
            elif "city" in st.session_state.ub_filters:
                del st.session_state.ub_filters["city"]
        
        with col2:
            budgets = ["Semua"] + [b.value for b in BudgetRange]
            budget = st.selectbox(
                "💰 Budget",
                budgets,
                format_func=lambda x: get_budget_label(BudgetRange(x))[1] if x != "Semua" else "Semua",
                key="filter_budget"
            )
            if budget != "Semua":
                st.session_state.ub_filters["budget"] = budget
            elif "budget" in st.session_state.ub_filters:
                del st.session_state.ub_filters["budget"]
        
        with col3:
            styles = ["Semua"] + [s.value for s in TravelStyle]
            style = st.selectbox(
                "🎨 Gaya",
                styles,
                format_func=lambda x: get_style_label(TravelStyle(x))[1] if x != "Semua" else "Semua",
                key="filter_style"
            )
            if style != "Semua":
                st.session_state.ub_filters["style"] = style
            elif "style" in st.session_state.ub_filters:
                del st.session_state.ub_filters["style"]
        
        with col4:
            types = ["Semua"] + [t.value for t in TripType]
            trip_type = st.selectbox(
                "👥 Tipe",
                types,
                format_func=lambda x: get_trip_type_label(TripType(x))[1] if x != "Semua" else "Semua",
                key="filter_type"
            )
            if trip_type != "Semua":
                st.session_state.ub_filters["type"] = trip_type
            elif "type" in st.session_state.ub_filters:
                del st.session_state.ub_filters["type"]
        
        # Date range
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            date_from = st.date_input(
                "📅 Dari",
                value=date.today() + timedelta(days=30),
                key="filter_date_from"
            )
            st.session_state.ub_filters["date_from"] = date_from
        
        with col2:
            date_to = st.date_input(
                "📅 Sampai",
                value=date.today() + timedelta(days=180),
                key="filter_date_to"
            )
            st.session_state.ub_filters["date_to"] = date_to
        
        with col3:
            if st.button("🔄 Reset", use_container_width=True):
                st.session_state.ub_filters = {}
                st.rerun()
        
        # Experience filter
        col1, col2 = st.columns(2)
        with col1:
            exp_levels = ["Semua"] + [e.value for e in ExperienceLevel]
            exp = st.selectbox(
                "⭐ Level Pengalaman",
                exp_levels,
                format_func=lambda x: get_experience_label(ExperienceLevel(x))[1] if x != "Semua" else "Semua Level",
                key="filter_experience"
            )
            if exp != "Semua":
                st.session_state.ub_filters["experience"] = exp
        
        with col2:
            # Status filter
            statuses = ["Semua", "open", "filling", "almost_full"]
            status = st.selectbox(
                "🔔 Status",
                statuses,
                format_func=lambda x: {"Semua": "Semua Status", "open": "🟢 Open", "filling": "🟡 Filling", "almost_full": "🟠 Almost Full"}.get(x, x),
                key="filter_status"
            )


# =============================================================================
# VIEW RENDERERS
# =============================================================================

def render_discover_view():
    """Render discover trips view like Reclub."""
    
    st.markdown("## 🔍 Discover Trips")
    st.caption("Temukan perjalanan umrah yang cocok dengan preferensi Anda")
    
    # Filters
    render_filters_panel()
    
    # Sort & View options
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        sort_by = st.selectbox(
            "Urutkan",
            ["🕐 Terbaru", "🎯 Paling Cocok", "📅 Terdekat", "🔥 Populer", "💰 Termurah", "⭐ Rating Tertinggi"],
            label_visibility="collapsed"
        )
    
    with col2:
        view_mode = st.radio("View", ["📱 Cards", "📋 List"], horizontal=True, label_visibility="collapsed")
    
    # Get and filter trips
    trips = st.session_state.ub_trips.copy()
    filters = st.session_state.ub_filters
    
    # Apply filters
    if filters.get("city"):
        trips = [t for t in trips if t.departure_city == filters["city"]]
    if filters.get("budget"):
        trips = [t for t in trips if t.budget_range.value == filters["budget"]]
    if filters.get("style"):
        trips = [t for t in trips if t.travel_style.value == filters["style"]]
    if filters.get("type"):
        trips = [t for t in trips if t.trip_type.value == filters["type"]]
    if filters.get("date_from") and filters.get("date_to"):
        trips = [t for t in trips if t.departure_date and filters["date_from"] <= t.departure_date <= filters["date_to"]]
    if filters.get("search"):
        search_term = filters["search"].lower()
        trips = [t for t in trips if search_term in t.title.lower() or search_term in t.description.lower()]
    
    # Sort
    if "Paling Cocok" in sort_by:
        trips = sorted(trips, key=lambda t: calculate_match_score(t, filters), reverse=True)
    elif "Terdekat" in sort_by:
        trips = sorted(trips, key=lambda t: t.departure_date or date.max)
    elif "Populer" in sort_by:
        trips = sorted(trips, key=lambda t: t.likes + t.views, reverse=True)
    elif "Termurah" in sort_by:
        trips = sorted(trips, key=lambda t: t.price_estimate)
    elif "Rating" in sort_by:
        trips = sorted(trips, key=lambda t: t.avg_rating, reverse=True)
    else:
        trips = sorted(trips, key=lambda t: t.created_at, reverse=True)
    
    # Stats
    open_trips = len([t for t in trips if t.status in [TripStatus.OPEN, TripStatus.FILLING]])
    st.info(f"📋 {len(trips)} trips ditemukan · 🟢 {open_trips} masih open")
    
    # Render trips
    show_match = "Paling Cocok" in sort_by
    
    if "Cards" in view_mode:
        cols = st.columns(2)
        for i, trip in enumerate(trips[:20]):
            with cols[i % 2]:
                render_trip_card(trip, show_match_score=show_match)
    else:
        for trip in trips[:20]:
            render_trip_card(trip, show_match_score=show_match, compact=True)
    
    if len(trips) > 20:
        st.info(f"Menampilkan 20 dari {len(trips)} trips. Gunakan filter untuk hasil lebih spesifik.")


def render_communities_view():
    """Render communities view like Reclub clubs."""

    st.markdown("## 🏘️ Communities")
    st.caption("Bergabung dengan komunitas umrah di Indonesia")

    # Search
    search = st.text_input("🔍 Cari komunitas...", key="comm_search")

    # Stats
    communities = st.session_state.ub_communities
    total_members = sum(c.member_count for c in communities)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Communities", len(communities))
    with col2:
        st.metric("Total Members", f"{total_members:,}")
    with col3:
        st.metric("Active Trips", sum(c.trips_created for c in communities))
    with col4:
        if st.button("➕ Buat Community", type="primary"):
            st.session_state.ub_show_create_community = True

    # Create Community Form
    if st.session_state.get("ub_show_create_community"):
        _render_create_community_form()

    st.divider()

    # Filter
    if search:
        communities = [c for c in communities if search.lower() in c.name.lower()]

    # Render communities
    for community in communities:
        render_community_card(community)


def _render_create_community_form():
    """Render community creation form."""
    st.markdown("---")
    st.markdown("### Buat Community Baru")

    with st.form("create_community_form"):
        comm_name = st.text_input(
            "Nama Community", placeholder="Contoh: Jamaah Jakarta Selatan"
        )
        comm_desc = st.text_area(
            "Deskripsi", placeholder="Jelaskan tujuan dan fokus community Anda...",
            max_chars=500
        )

        col1, col2 = st.columns(2)
        with col1:
            comm_location = st.selectbox(
                "Lokasi",
                ["Jakarta", "Surabaya", "Bandung", "Medan", "Makassar",
                 "Semarang", "Yogyakarta", "Palembang", "Lainnya"]
            )
            comm_public = st.toggle("Community Publik", value=True)
        with col2:
            comm_focus = st.selectbox(
                "Fokus",
                ["All Levels", "Pemula", "Berpengalaman", "Keluarga",
                 "Profesional Muda", "Lansia"]
            )

        col_submit, col_cancel = st.columns(2)
        with col_submit:
            submitted = st.form_submit_button(
                "Buat Community", type="primary", use_container_width=True
            )
        with col_cancel:
            cancelled = st.form_submit_button(
                "Batal", use_container_width=True
            )

    if cancelled:
        st.session_state.ub_show_create_community = False
        st.rerun()

    if submitted:
        if not comm_name or len(comm_name.strip()) < 3:
            st.error("Nama community minimal 3 karakter.")
            return

        current_user = st.session_state.get("ub_current_user")
        owner_id = current_user.id if current_user else "user_0"
        owner_name = current_user.name if current_user else "Anda"

        new_community = Community(
            id=f"comm_{random.randint(10000, 99999)}",
            code=generate_club_code(),
            name=comm_name.strip(),
            description=comm_desc.strip() if comm_desc else "",
            avatar=f"https://api.dicebear.com/7.x/identicon/svg?seed={comm_name.strip().replace(' ', '')}",
            cover_image="",
            owner_id=owner_id,
            owner_name=owner_name,
            admins=[owner_id],
            member_count=1,
            members=[owner_id],
            is_public=comm_public,
            location=comm_location,
            focus=comm_focus,
            trips_created=0,
            total_jamaah=0,
            avg_rating=0.0,
        )

        st.session_state.ub_communities.insert(0, new_community)
        st.session_state.ub_show_create_community = False
        st.success(f"Community **{comm_name}** berhasil dibuat! Kode: **{new_community.code}**")
        st.rerun()


def render_smart_match_view():
    """Render smart matching view."""
    
    st.markdown("## 🎯 Smart Match")
    st.caption("Temukan trip yang paling cocok berdasarkan preferensi Anda")
    
    user = st.session_state.ub_current_user
    
    # User preferences form
    with st.form("match_preferences"):
        st.markdown("### 📋 Preferensi Anda")
        
        col1, col2 = st.columns(2)
        
        with col1:
            city = st.selectbox("🏙️ Kota Keberangkatan", ["Jakarta", "Surabaya", "Bandung", "Medan", "Makassar"])
            style = st.selectbox("🎨 Gaya Perjalanan", list(TravelStyle), format_func=lambda x: get_style_label(x)[1])
            date_pref = st.date_input("📅 Preferensi Tanggal", value=date.today() + timedelta(days=60))
        
        with col2:
            budget = st.selectbox("💰 Budget", list(BudgetRange), format_func=lambda x: get_budget_label(x)[1])
            trip_type = st.selectbox("👥 Tipe Trip", list(TripType), format_func=lambda x: get_trip_type_label(x)[1])
            flexibility = st.slider("📊 Fleksibilitas Tanggal (hari)", 0, 30, 14)
        
        # Experience preference
        exp_pref = st.selectbox("⭐ Pengalaman Minimal", list(ExperienceLevel), format_func=lambda x: get_experience_label(x)[1])
        
        submitted = st.form_submit_button("🔍 Cari Match Terbaik", type="primary", use_container_width=True)
    
    if submitted:
        # Calculate matches
        preferences = {
            "city": city,
            "budget": budget.value,
            "style": style.value,
            "type": trip_type.value,
            "experience": exp_pref.value,
            "date_from": date_pref - timedelta(days=flexibility),
            "date_to": date_pref + timedelta(days=flexibility),
        }
        
        trips = st.session_state.ub_trips
        scored_trips = [(trip, calculate_match_score(trip, preferences)) for trip in trips]
        scored_trips = [(t, s) for t, s in scored_trips if s > 0]
        scored_trips.sort(key=lambda x: x[1], reverse=True)
        
        st.success(f"🎯 Ditemukan {len(scored_trips)} trips yang cocok!")
        
        # Show matches in tiers
        perfect = [(t, s) for t, s in scored_trips if s >= 80]
        good = [(t, s) for t, s in scored_trips if 50 <= s < 80]
        fair = [(t, s) for t, s in scored_trips if s < 50]
        
        if perfect:
            st.markdown("### 🏆 Perfect Match (80%+)")
            for trip, score in perfect[:5]:
                with st.container(border=True):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"**{trip.title}**")
                        st.caption(f"📍 {trip.departure_city} · 📅 {trip.departure_date} · 👥 {len(trip.confirmed_members)}/{trip.max_members}")
                        st.caption(f"💰 {format_currency(trip.price_estimate)} · ⭐ {trip.leader.rating}")
                    with col2:
                        st.success(f"🎯 {score}%")
                        if st.button("Lihat", key=f"match_{trip.id}", type="primary"):
                            navigate_to("trip_detail", selected_trip=trip)
                            st.rerun()
        
        if good:
            st.markdown("### ✨ Good Match (50-79%)")
            for trip, score in good[:5]:
                with st.container(border=True):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"**{trip.title}**")
                        st.caption(f"📍 {trip.departure_city} · 📅 {trip.departure_date}")
                    with col2:
                        st.warning(f"🎯 {score}%")


def render_leaderboard_view():
    """Render leaderboard like Reclub rankings."""
    
    st.markdown("## 🏆 Leaderboard")
    st.caption("Top contributors dalam komunitas Umrah Bareng")
    
    tabs = st.tabs(["👑 Top Leaders", "⭐ Top Reviewers", "🤝 Most Helpful", "🔥 Rising Stars"])
    
    users = st.session_state.ub_users
    
    with tabs[0]:
        # Sort by trips led
        leaders = sorted(users, key=lambda u: u.stats.total_jamaah_led, reverse=True)[:10]
        
        for i, user in enumerate(leaders, 1):
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"#{i}")
            
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([1, 1, 3, 2])
                
                with col1:
                    st.markdown(f"### {medal}")
                
                with col2:
                    st.image(user.avatar, width=50)
                
                with col3:
                    verified = "✅" if user.is_verified else ""
                    st.markdown(f"**{user.name}** {verified}")
                    st.caption(f"👥 {user.stats.total_jamaah_led} jamaah dipimpin")
                
                with col4:
                    st.metric("Rating", f"⭐ {user.rating}")
    
    with tabs[1]:
        # Sort by reviews
        reviewers = sorted(users, key=lambda u: u.stats.reviews_given, reverse=True)[:10]
        
        for i, user in enumerate(reviewers, 1):
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"#{i}")
            
            with st.container(border=True):
                col1, col2, col3 = st.columns([1, 2, 2])
                with col1:
                    st.markdown(f"### {medal}")
                    st.image(user.avatar, width=40)
                with col2:
                    st.markdown(f"**{user.name}**")
                    st.caption(f"📝 {user.stats.reviews_given} reviews")
                with col3:
                    st.metric("Helpful", f"👍 {user.stats.helpful_votes}")
    
    with tabs[2]:
        # Sort by helpful votes
        helpful = sorted(users, key=lambda u: u.stats.helpful_votes, reverse=True)[:10]
        
        for i, user in enumerate(helpful, 1):
            st.markdown(f"{i}. **{user.name}** - 👍 {user.stats.helpful_votes} helpful votes")
    
    with tabs[3]:
        # New users with good activity
        recent = sorted(users, key=lambda u: u.joined_at, reverse=True)[:10]
        
        for user in recent:
            st.markdown(f"🌟 **{user.name}** - Bergabung {format_relative_time(user.joined_at)}")


# =============================================================================
# HELPER: MARKDOWN TO HTML
# =============================================================================

def _markdown_to_html_simple(text: str) -> str:
    """Simple markdown to HTML conversion for display in custom styled div."""
    lines = text.split("\n")
    html_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            html_lines.append("<br/>")
            continue
        # Bold
        line = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
        # Italic
        line = re.sub(r"\*(.+?)\*", r"<em>\1</em>", line)
        # Bullet points
        if line.startswith("- ") or line.startswith("* "):
            line = "&bull; " + line[2:]
        # Numbered lists
        match = re.match(r"^(\d+)\.\s+", line)
        if match:
            line = "<strong>" + match.group(1) + ".</strong> " + line[match.end():]
        html_lines.append("<div style='margin-bottom:0.3rem;'>" + line + "</div>")

    return "\n".join(html_lines)


# =============================================================================
# AI RECOMMENDATION SECTION
# =============================================================================

def render_ai_recommendation():
    """Render AI-powered group recommendation section."""

    st.markdown("---")
    prompt_html = (
        '<div class="ub-ai-prompt-card">'
        '<h4>🤖 Rekomendasi AI - Teman Umrah</h4>'
        '<p>Dapatkan rekomendasi grup dan tips mencocokkan teman perjalanan '
        'berdasarkan preferensi Anda dari AI.</p>'
        '</div>'
    )
    st.markdown(prompt_html, unsafe_allow_html=True)

    user = st.session_state.ub_current_user
    trips = st.session_state.ub_trips

    # Collect summary data for the AI prompt
    open_trips = [t for t in trips if t.status in [TripStatus.OPEN, TripStatus.FILLING]]
    city_counts = {}
    for t in open_trips:
        city_counts[t.departure_city] = city_counts.get(t.departure_city, 0) + 1

    city_summary_parts = []
    for city, count in sorted(city_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
        city_summary_parts.append(city + " (" + str(count) + " trip)")
    city_summary = ", ".join(city_summary_parts) if city_summary_parts else "Belum ada data"

    exp_icon, exp_label = get_experience_label(user.experience_level)
    style_icon, style_label = get_style_label(user.preferred_style)
    budget_icon, budget_label, budget_range = get_budget_label(user.preferred_budget)

    col1, col2 = st.columns([3, 1])
    with col1:
        user_question = st.text_input(
            "Pertanyaan tambahan (opsional)",
            placeholder="Contoh: Saya ingin umrah saat Ramadan dengan keluarga...",
            key="ub_ai_question"
        )
    with col2:
        ask_ai = st.button(
            "🤖 Tanya AI",
            type="primary",
            use_container_width=True,
            key="ub_ask_ai_btn"
        )

    if ask_ai:
        extra_question = ""
        if user_question:
            extra_question = " Pertanyaan tambahan dari user: " + user_question

        prompt_text = (
            "Profil jamaah:\n"
            "- Nama: " + user.name + "\n"
            "- Kota: " + user.city + "\n"
            "- Pengalaman: " + exp_label + " (" + str(user.umrah_count) + "x umrah)\n"
            "- Gaya perjalanan: " + style_label + "\n"
            "- Budget: " + budget_label + " (" + budget_range + ")\n"
            "- Durasi preferensi: " + str(user.preferred_duration) + " hari\n\n"
            "Trip yang tersedia saat ini:\n"
            "- Total trip open: " + str(len(open_trips)) + "\n"
            "- Kota keberangkatan populer: " + city_summary + "\n\n"
            "Berikan rekomendasi:\n"
            "1. Tipe grup yang paling cocok untuk profil ini\n"
            "2. Tips memilih teman perjalanan umrah\n"
            "3. Saran waktu terbaik berangkat\n"
            "4. Tips agar pengalaman umrah bareng lebih berkesan\n"
            + extra_question
        )

        system_prompt = (
            "Kamu adalah konsultan perjalanan Umrah yang membantu mencocokkan grup. "
            "Berikan saran praktis dan personal berdasarkan profil jamaah. "
            "Gunakan Bahasa Indonesia yang sopan dan bersahabat. "
            "Sertakan tips konkret yang bisa langsung diterapkan."
        )

        with st.spinner("AI sedang menganalisis profil Anda..."):
            response = ai_complete(prompt_text, system_prompt=system_prompt, max_tokens=800)

        if response:
            st.session_state.ub_ai_response = response
            # Gamification: award XP for first AI recommendation
            if not st.session_state.ub_xp_ai_recommendation:
                st.session_state.ub_xp_ai_recommendation = True
                add_xp_safe(20, "Rekomendasi AI Umrah Bareng")
                xp_html = (
                    '<div class="ub-xp-toast">'
                    '+20 XP - Rekomendasi AI Umrah Bareng!'
                    '</div>'
                )
                st.markdown(xp_html, unsafe_allow_html=True)

    # Render stored AI response
    ai_response = st.session_state.get("ub_ai_response")
    if ai_response:
        html_content = _markdown_to_html_simple(ai_response)
        ai_card_html = (
            '<div class="ai-card" role="status" aria-live="polite">'
            '<h4>🧠 Rekomendasi AI untuk Anda</h4>'
            '<p>' + html_content + '</p>'
            '</div>'
        )
        st.markdown(ai_card_html, unsafe_allow_html=True)
    else:
        if not ask_ai:
            st.info(
                "Klik **Tanya AI** untuk mendapatkan rekomendasi grup dan "
                "tips mencocokkan teman perjalanan umrah yang sesuai profil Anda."
            )


# =============================================================================
# 🚀 MAIN PAGE RENDERER
# =============================================================================

def render_umrah_bareng_page():
    """Main Umrah Bareng page renderer."""

    # Track page view
    try:
        from services.analytics import track_page
        track_page("umrah_bareng")
    except Exception:
        pass

    # Initialize state
    init_umrah_bareng_state()

    # Inject shared + page-specific CSS
    inject_css(HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS, PAGE_CSS)

    # Hero banner
    hero_html = (
        '<div class="page-hero">'
        '<div class="bismillah">بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ</div>'
        '<h1><span aria-hidden="true">🕋 </span>Umrah Bareng</h1>'
        '<div class="subtitle">Temukan teman perjalanan umrah yang sefrekuensi</div>'
        '</div>'
    )
    st.markdown(hero_html, unsafe_allow_html=True)

    # Summary stats row
    trips = st.session_state.ub_trips
    users = st.session_state.ub_users
    communities = st.session_state.ub_communities
    open_count = len([t for t in trips if t.status in [TripStatus.OPEN, TripStatus.FILLING]])
    total_jamaah = sum(len(t.confirmed_members) for t in trips)

    stats_html = (
        '<div class="ub-stats-row">'
        '<div class="ub-stat-card">'
        '<div class="number" style="color:#4ade80;">' + str(len(trips)) + '</div>'
        '<div class="label">Total Trip</div>'
        '</div>'
        '<div class="ub-stat-card">'
        '<div class="number" style="color:#60a5fa;">' + str(open_count) + '</div>'
        '<div class="label">Trip Open</div>'
        '</div>'
        '<div class="ub-stat-card">'
        '<div class="number" style="color:#d4af37;">' + str(total_jamaah) + '</div>'
        '<div class="label">Total Jamaah</div>'
        '</div>'
        '<div class="ub-stat-card">'
        '<div class="number" style="color:#c084fc;">' + str(len(communities)) + '</div>'
        '<div class="label">Komunitas</div>'
        '</div>'
        '</div>'
    )
    st.markdown(stats_html, unsafe_allow_html=True)

    # Render header
    render_header()

    # Render sidebar
    render_sidebar()

    st.divider()

    # Get current view (use ub_view which is set by navigate_to)
    current_view = st.session_state.get("ub_view", "discover")

    # Render appropriate view
    if current_view == "discover":
        render_discover_view()
    elif current_view == "communities":
        render_communities_view()
    elif current_view in ("match", "smart_match"):
        render_smart_match_view()
    elif current_view == "leaderboard":
        render_leaderboard_view()
    else:
        render_discover_view()

    # AI Recommendation section (always visible at bottom)
    render_ai_recommendation()


# Export
__all__ = ["render_umrah_bareng_page"]
