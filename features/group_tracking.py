"""
LABBAIK AI - Group Tracking System
==================================
Real-time group tracking for Umrah Bareng:
- Live location sharing among group members
- Check-in system at key locations
- Member status dashboard
- Lost member alerts
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import random
import string
from services.ai.helpers import ai_complete, add_xp_safe
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS, AI_CARD_CSS

# =============================================================================
# DATA STRUCTURES
# =============================================================================

class MemberStatus(str, Enum):
    ONLINE = "online"           # Recently active (< 5 min)
    AWAY = "away"               # Active 5-30 min ago
    OFFLINE = "offline"         # Inactive > 30 min
    SOS = "sos"                 # Emergency
    CHECKED_IN = "checked_in"   # At designated location


class LocationType(str, Enum):
    MASJIDIL_HARAM = "masjidil_haram"
    MASJID_NABAWI = "masjid_nabawi"
    HOTEL_MAKKAH = "hotel_makkah"
    HOTEL_MADINAH = "hotel_madinah"
    MINA = "mina"
    ARAFAH = "arafah"
    MUZDALIFAH = "muzdalifah"
    AIRPORT = "airport"
    CUSTOM = "custom"


@dataclass
class GroupMember:
    """Group member data."""
    id: str
    name: str
    phone: str
    avatar: str = "👤"
    status: MemberStatus = MemberStatus.OFFLINE
    last_seen: datetime = field(default_factory=datetime.now)
    last_location: str = ""
    location_type: LocationType = LocationType.CUSTOM
    latitude: float = 0.0
    longitude: float = 0.0
    is_leader: bool = False
    battery_level: int = 100
    check_ins: List[Dict] = field(default_factory=list)


@dataclass
class TravelGroup:
    """Travel group structure."""
    id: str
    name: str
    code: str  # Shareable join code
    leader_id: str
    members: List[GroupMember] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    current_city: str = "Makkah"
    hotel_makkah: str = ""
    hotel_madinah: str = ""
    check_in_locations: List[Dict] = field(default_factory=list)


# =============================================================================
# KEY LOCATIONS DATABASE
# =============================================================================

KEY_LOCATIONS = {
    LocationType.MASJIDIL_HARAM: {
        "name": "Masjidil Haram",
        "icon": "🕋",
        "lat": 21.4225,
        "lng": 39.8262,
        "city": "Makkah"
    },
    LocationType.MASJID_NABAWI: {
        "name": "Masjid Nabawi",
        "icon": "🕌",
        "lat": 24.4672,
        "lng": 39.6112,
        "city": "Madinah"
    },
    LocationType.MINA: {
        "name": "Mina",
        "icon": "⛺",
        "lat": 21.4133,
        "lng": 39.8933,
        "city": "Makkah"
    },
    LocationType.ARAFAH: {
        "name": "Arafah",
        "icon": "🏔️",
        "lat": 21.3549,
        "lng": 39.9842,
        "city": "Makkah"
    },
    LocationType.MUZDALIFAH: {
        "name": "Muzdalifah",
        "icon": "🌙",
        "lat": 21.3892,
        "lng": 39.9333,
        "city": "Makkah"
    },
}


# =============================================================================
# GROUP TRACKING SERVICE
# =============================================================================

class GroupTrackingService:
    """Service for group tracking functionality."""
    
    def __init__(self):
        self._init_session_state()
    
    def _init_session_state(self):
        """Initialize session state."""
        if "tracking_groups" not in st.session_state:
            st.session_state.tracking_groups = {}
        
        if "current_group_id" not in st.session_state:
            st.session_state.current_group_id = None
        
        if "my_member_id" not in st.session_state:
            st.session_state.my_member_id = None
    
    def _generate_code(self, length: int = 6) -> str:
        """Generate random group code."""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    
    def _generate_id(self) -> str:
        """Generate random ID."""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
    
    def create_group(self, name: str, leader_name: str, leader_phone: str) -> TravelGroup:
        """Create a new travel group."""
        group_id = self._generate_id()
        code = self._generate_code()
        leader_id = self._generate_id()
        
        leader = GroupMember(
            id=leader_id,
            name=leader_name,
            phone=leader_phone,
            avatar="👑",
            status=MemberStatus.ONLINE,
            is_leader=True
        )
        
        group = TravelGroup(
            id=group_id,
            name=name,
            code=code,
            leader_id=leader_id,
            members=[leader]
        )
        
        st.session_state.tracking_groups[group_id] = group
        st.session_state.current_group_id = group_id
        st.session_state.my_member_id = leader_id
        
        return group
    
    def join_group(self, code: str, name: str, phone: str) -> Optional[TravelGroup]:
        """Join existing group with code."""
        # Find group by code
        for group_id, group in st.session_state.tracking_groups.items():
            if group.code == code.upper():
                member_id = self._generate_id()
                member = GroupMember(
                    id=member_id,
                    name=name,
                    phone=phone,
                    status=MemberStatus.ONLINE
                )
                group.members.append(member)
                
                st.session_state.current_group_id = group_id
                st.session_state.my_member_id = member_id
                
                return group
        
        return None
    
    def get_current_group(self) -> Optional[TravelGroup]:
        """Get current active group."""
        group_id = st.session_state.current_group_id
        if group_id and group_id in st.session_state.tracking_groups:
            return st.session_state.tracking_groups[group_id]
        return None
    
    def update_my_location(self, location_type: LocationType, custom_name: str = ""):
        """Update current user's location."""
        group = self.get_current_group()
        if not group:
            return
        
        member_id = st.session_state.my_member_id
        for member in group.members:
            if member.id == member_id:
                member.status = MemberStatus.ONLINE
                member.last_seen = datetime.now()
                member.location_type = location_type
                
                if location_type in KEY_LOCATIONS:
                    loc_info = KEY_LOCATIONS[location_type]
                    member.last_location = loc_info["name"]
                    member.latitude = loc_info["lat"]
                    member.longitude = loc_info["lng"]
                else:
                    member.last_location = custom_name or "Unknown"
                
                break
    
    def check_in(self, location_type: LocationType):
        """Record a check-in at location."""
        group = self.get_current_group()
        if not group:
            return
        
        member_id = st.session_state.my_member_id
        for member in group.members:
            if member.id == member_id:
                member.status = MemberStatus.CHECKED_IN
                member.check_ins.append({
                    "location": location_type.value,
                    "time": datetime.now().isoformat()
                })
                self.update_my_location(location_type)
                break
    
    def trigger_sos(self):
        """Trigger SOS for current user."""
        group = self.get_current_group()
        if not group:
            return
        
        member_id = st.session_state.my_member_id
        for member in group.members:
            if member.id == member_id:
                member.status = MemberStatus.SOS
                break
    
    def get_member_stats(self) -> Dict[str, int]:
        """Get member status statistics."""
        group = self.get_current_group()
        if not group:
            return {}
        
        stats = {
            "total": len(group.members),
            "online": 0,
            "away": 0,
            "offline": 0,
            "sos": 0,
            "checked_in": 0,
        }
        
        for member in group.members:
            status_key = member.status.value
            if status_key in stats:
                stats[status_key] += 1
        
        return stats


# =============================================================================
# MOCK DATA FOR DEMO
# =============================================================================

def create_demo_group() -> TravelGroup:
    """Create demo group with sample members."""
    service = GroupTrackingService()
    
    # Check if demo group exists
    if "demo_group" in st.session_state:
        return st.session_state.demo_group
    
    # Create demo group
    group = TravelGroup(
        id="demo123",
        name="Rombongan Umrah Barokah 2025",
        code="UMR2025",
        leader_id="leader1",
        current_city="Makkah",
        hotel_makkah="Pullman Zamzam",
        hotel_madinah="Dar Al Taqwa",
    )
    
    # Add demo members
    demo_members = [
        GroupMember(
            id="leader1",
            name="Ustadz Ahmad",
            phone="+628123456789",
            avatar="👑",
            status=MemberStatus.ONLINE,
            last_seen=datetime.now(),
            last_location="Masjidil Haram",
            location_type=LocationType.MASJIDIL_HARAM,
            is_leader=True,
            battery_level=85
        ),
        GroupMember(
            id="member2",
            name="Budi Santoso",
            phone="+628234567890",
            avatar="👤",
            status=MemberStatus.ONLINE,
            last_seen=datetime.now() - timedelta(minutes=2),
            last_location="Masjidil Haram",
            location_type=LocationType.MASJIDIL_HARAM,
            battery_level=72
        ),
        GroupMember(
            id="member3",
            name="Siti Aminah",
            phone="+628345678901",
            avatar="👩",
            status=MemberStatus.CHECKED_IN,
            last_seen=datetime.now() - timedelta(minutes=5),
            last_location="Hotel Pullman",
            location_type=LocationType.HOTEL_MAKKAH,
            battery_level=45
        ),
        GroupMember(
            id="member4",
            name="Pak Haji Ridwan",
            phone="+628456789012",
            avatar="🧔",
            status=MemberStatus.AWAY,
            last_seen=datetime.now() - timedelta(minutes=15),
            last_location="Masjidil Haram - Mas'a",
            location_type=LocationType.MASJIDIL_HARAM,
            battery_level=28
        ),
        GroupMember(
            id="member5",
            name="Dewi Kartika",
            phone="+628567890123",
            avatar="👩",
            status=MemberStatus.OFFLINE,
            last_seen=datetime.now() - timedelta(hours=1),
            last_location="Unknown",
            location_type=LocationType.CUSTOM,
            battery_level=15
        ),
    ]
    
    group.members = demo_members
    st.session_state.demo_group = group
    st.session_state.tracking_groups["demo123"] = group
    st.session_state.current_group_id = "demo123"
    st.session_state.my_member_id = "leader1"
    
    return group


# =============================================================================
# RENDER FUNCTIONS
# =============================================================================

def render_member_card(member: GroupMember, compact: bool = False):
    """Render a member card."""
    
    # Status colors and icons
    status_config = {
        MemberStatus.ONLINE: ("#22c55e", "🟢", "Online"),
        MemberStatus.AWAY: ("#eab308", "🟡", "Away"),
        MemberStatus.OFFLINE: ("#6b7280", "⚫", "Offline"),
        MemberStatus.SOS: ("#ef4444", "🔴", "SOS!"),
        MemberStatus.CHECKED_IN: ("#3b82f6", "✅", "Checked In"),
    }
    
    color, icon, label = status_config.get(member.status, ("#6b7280", "⚫", "Unknown"))
    
    # Time since last seen
    time_diff = datetime.now() - member.last_seen
    if time_diff.seconds < 60:
        time_str = "Baru saja"
    elif time_diff.seconds < 3600:
        time_str = f"{time_diff.seconds // 60} menit lalu"
    else:
        time_str = f"{time_diff.seconds // 3600} jam lalu"
    
    # Battery indicator
    if member.battery_level > 50:
        battery_icon = "🔋"
        battery_color = "#22c55e"
    elif member.battery_level > 20:
        battery_icon = "🔋"
        battery_color = "#eab308"
    else:
        battery_icon = "🪫"
        battery_color = "#ef4444"
    
    if compact:
        st.markdown(f"""
        <div style="display: flex; align-items: center; padding: 0.5rem; background: #1a1a1a; border-radius: 10px; margin-bottom: 0.5rem; border-left: 3px solid {color};">
            <span style="font-size: 1.5rem; margin-right: 0.5rem;">{member.avatar}</span>
            <div style="flex: 1;">
                <div style="color: white; font-weight: bold;">{member.name} {"👑" if member.is_leader else ""}</div>
                <div style="color: #b0b0b0; font-size: 0.75rem;">{icon} {label} • {member.last_location}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a1a, #2d2d2d); padding: 1rem; border-radius: 15px; border-left: 4px solid {color}; margin-bottom: 1rem;">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <span style="font-size: 2.5rem;">{member.avatar}</span>
                    <div>
                        <div style="color: white; font-size: 1.1rem; font-weight: bold;">
                            {member.name} {"👑" if member.is_leader else ""}
                        </div>
                        <div style="color: {color}; font-size: 0.9rem;">{icon} {label}</div>
                        <div style="color: #b0b0b0; font-size: 0.8rem;">📍 {member.last_location} • {time_str}</div>
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="color: {battery_color};">{battery_icon} {member.battery_level}%</div>
                    <div style="color: #b0b0b0; font-size: 0.75rem;">📱 {member.phone[-4:]}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_group_header(group: TravelGroup):
    """Render group header with stats."""
    
    service = GroupTrackingService()
    stats = service.get_member_stats()
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1a1a1a, #2d2d2d); padding: 1.5rem; border-radius: 20px; border: 1px solid #d4af37; margin-bottom: 1rem;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="color: #d4af37; font-size: 0.9rem;">Rombongan</div>
                <div style="color: white; font-size: 1.5rem; font-weight: bold;">{group.name}</div>
                <div style="color: #b0b0b0; font-size: 0.85rem;">📍 {group.current_city} • 🏨 {group.hotel_makkah}</div>
            </div>
            <div style="text-align: center; background: #2d2d2d; padding: 1rem; border-radius: 15px;">
                <div style="color: #d4af37; font-size: 0.8rem;">Kode Grup</div>
                <div style="color: white; font-size: 1.5rem; font-weight: bold; font-family: monospace;">{group.code}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Status summary
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👥 Total", stats.get("total", 0))
    with col2:
        st.metric("🟢 Online", stats.get("online", 0) + stats.get("checked_in", 0))
    with col3:
        st.metric("🟡 Away", stats.get("away", 0))
    with col4:
        sos_count = stats.get("sos", 0)
        if sos_count > 0:
            st.error(f"🔴 SOS: {sos_count}")
        else:
            st.metric("⚫ Offline", stats.get("offline", 0))


def render_member_list(group: TravelGroup):
    """Render list of all members."""
    
    st.markdown("### 👥 Anggota Rombongan")
    
    # Sort: SOS first, then online, then away, then offline
    priority = {
        MemberStatus.SOS: 0,
        MemberStatus.ONLINE: 1,
        MemberStatus.CHECKED_IN: 2,
        MemberStatus.AWAY: 3,
        MemberStatus.OFFLINE: 4,
    }
    
    sorted_members = sorted(group.members, key=lambda m: priority.get(m.status, 5))
    
    for member in sorted_members:
        render_member_card(member, compact=False)


def render_check_in_panel():
    """Render check-in panel for current user."""
    
    st.markdown("### 📍 Check In Lokasi")
    st.caption("Bagikan lokasi Anda ke rombongan")
    
    service = GroupTrackingService()
    
    # Quick check-in buttons
    col1, col2 = st.columns(2)
    
    locations = [
        (LocationType.MASJIDIL_HARAM, "🕋", "Masjidil Haram"),
        (LocationType.HOTEL_MAKKAH, "🏨", "Hotel Makkah"),
        (LocationType.MASJID_NABAWI, "🕌", "Masjid Nabawi"),
        (LocationType.HOTEL_MADINAH, "🏨", "Hotel Madinah"),
    ]
    
    for i, (loc_type, icon, name) in enumerate(locations):
        with [col1, col2][i % 2]:
            if st.button(f"{icon} {name}", key=f"checkin_{loc_type}", use_container_width=True):
                service.check_in(loc_type)
                st.success(f"✅ Check in di {name}!")
                st.rerun()


def render_tracking_map(group: TravelGroup):
    """Render simple map showing member locations."""
    
    st.markdown("### 🗺️ Peta Lokasi")
    st.caption("Lokasi anggota rombongan")
    
    # Simple location summary (would use actual map in production)
    location_counts = {}
    
    for member in group.members:
        loc = member.last_location or "Unknown"
        if loc not in location_counts:
            location_counts[loc] = []
        location_counts[loc].append(member)
    
    for location, members in location_counts.items():
        member_names = ", ".join([m.name for m in members])
        status_icons = " ".join([
            "🟢" if m.status in [MemberStatus.ONLINE, MemberStatus.CHECKED_IN] 
            else "🟡" if m.status == MemberStatus.AWAY 
            else "🔴" if m.status == MemberStatus.SOS
            else "⚫" 
            for m in members
        ])
        
        st.markdown(f"""
        <div style="background: #1a1a1a; padding: 1rem; border-radius: 10px; margin-bottom: 0.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="color: #d4af37; font-weight: bold;">📍 {location}</div>
                    <div style="color: #b0b0b0; font-size: 0.85rem;">{member_names}</div>
                </div>
                <div style="font-size: 1.2rem;">{status_icons}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_group_tracking_page():
    """Full group tracking page."""
    inject_css(HERO_CSS, CARD_CSS, AI_CARD_CSS)

    st.markdown("""
        <div class="page-hero">
            <h1>📍 Group Tracking</h1>
            <div class="subtitle">Pantau lokasi anggota grup umrah secara real-time</div>
        </div>
    """, unsafe_allow_html=True)
    
    service = GroupTrackingService()
    
    # Check if user has a group
    group = service.get_current_group()
    
    if not group:
        # No group - show create/join options
        st.markdown("### Mulai Tracking Rombongan")
        
        tab1, tab2, tab3 = st.tabs(["➕ Buat Grup", "🔗 Gabung Grup", "👀 Demo"])
        
        with tab1:
            st.markdown("#### Buat Rombongan Baru")
            
            group_name = st.text_input("Nama Rombongan", placeholder="Umrah Barokah 2025")
            leader_name = st.text_input("Nama Anda (Ketua)", placeholder="Nama lengkap")
            leader_phone = st.text_input("No. HP", placeholder="+628xxx")
            
            if st.button("🚀 Buat Grup", type="primary", use_container_width=True):
                if group_name and leader_name and leader_phone:
                    new_group = service.create_group(group_name, leader_name, leader_phone)
                    st.success(f"✅ Grup berhasil dibuat! Kode: **{new_group.code}**")
                    add_xp_safe(15, "Membuat grup tracking")
                    st.rerun()
                else:
                    st.error("Lengkapi semua field!")
        
        with tab2:
            st.markdown("#### Gabung Rombongan")
            
            join_code = st.text_input("Kode Grup", placeholder="ABC123", max_chars=6)
            member_name = st.text_input("Nama Anda", placeholder="Nama lengkap", key="join_name")
            member_phone = st.text_input("No. HP", placeholder="+628xxx", key="join_phone")
            
            if st.button("🔗 Gabung", type="primary", use_container_width=True):
                if join_code and member_name and member_phone:
                    joined_group = service.join_group(join_code, member_name, member_phone)
                    if joined_group:
                        st.success(f"✅ Berhasil gabung ke {joined_group.name}!")
                        st.rerun()
                    else:
                        st.error("Kode grup tidak ditemukan!")
                else:
                    st.error("Lengkapi semua field!")
        
        with tab3:
            st.markdown("#### Mode Demo")
            st.caption("Coba fitur tracking dengan data contoh")
            
            if st.button("🎮 Mulai Demo", use_container_width=True):
                create_demo_group()
                st.success("✅ Demo group created!")
                st.rerun()
    
    else:
        # Has group - show tracking dashboard
        render_group_header(group)
        
        # Tabs for different views
        tab1, tab2, tab3 = st.tabs(["👥 Anggota", "📍 Check In", "🗺️ Peta"])
        
        with tab1:
            render_member_list(group)
        
        with tab2:
            render_check_in_panel()
        
        with tab3:
            render_tracking_map(group)
        
        # Group actions
        st.divider()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📤 Share Kode Grup", use_container_width=True):
                st.code(f"Gabung rombongan {group.name} di LABBAIK AI!\nKode: {group.code}")
        
        with col2:
            if st.button("🔔 Notif Semua", use_container_width=True):
                st.info("Notifikasi terkirim ke semua anggota")
        
        with col3:
            if st.button("🚪 Keluar Grup", use_container_width=True):
                st.session_state.current_group_id = None
                st.session_state.my_member_id = None
                st.rerun()

    st.markdown("---")
    if st.button("🤖 Tips Manajemen Grup", key="group_ai_tips"):
        with st.spinner("Menganalisis..."):
            tips = ai_complete(
                "Berikan 3 tips praktis untuk mengelola grup umrah agar semua anggota tetap aman dan terhubung. "
                "Termasuk tips komunikasi dan titik kumpul. Bahasa Indonesia.",
                system_prompt="Kamu adalah tour leader umrah berpengalaman.",
                max_tokens=300,
            )
            if tips:
                st.markdown(f'''
                    <div class="ai-card" role="status" aria-live="polite">
                        <h4>🤖 Tips AI Manajemen Grup</h4>
                        <p>{tips}</p>
                    </div>
                ''', unsafe_allow_html=True)
            else:
                st.info("AI tidak tersedia saat ini")


# =============================================================================
# MINI WIDGET FOR SIDEBAR
# =============================================================================

def render_tracking_mini_widget():
    """Render mini tracking widget for sidebar."""
    
    service = GroupTrackingService()
    group = service.get_current_group()
    
    if group:
        stats = service.get_member_stats()
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a1a, #2d2d2d); padding: 1rem; border-radius: 15px; border: 1px solid #d4af37;">
            <div style="color: #d4af37; font-size: 0.8rem; margin-bottom: 0.5rem;">📍 Rombongan</div>
            <div style="color: white; font-weight: bold; margin-bottom: 0.5rem;">{group.name}</div>
            <div style="display: flex; justify-content: space-between; color: #b0b0b0; font-size: 0.8rem;">
                <span>🟢 {stats.get('online', 0) + stats.get('checked_in', 0)}</span>
                <span>🟡 {stats.get('away', 0)}</span>
                <span>⚫ {stats.get('offline', 0)}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        if st.button("📍 Setup Tracking", use_container_width=True):
            st.session_state.current_page = "group_tracking"
            st.rerun()


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    "GroupTrackingService",
    "TravelGroup",
    "GroupMember",
    "MemberStatus",
    "render_group_tracking_page",
    "render_tracking_mini_widget",
    "render_member_card",
    "create_demo_group",
]
