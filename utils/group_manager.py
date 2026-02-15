"""
LABBAIK AI - Group Manager
===========================
Utility for creating and managing simulation groups for family/group Umrah planning.

This module provides:
- Group creation with unique shareable codes
- Member management (add, activate, update contributions)
- Group financial analytics (total collected, remaining per person)
- WhatsApp sharing link generation
"""

import random
import string
import json
import logging
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class GroupRole(str, Enum):
    """Member roles within a group."""
    LEADER = "leader"
    CO_LEADER = "co_leader"
    MEMBER = "member"


class GroupStatus(str, Enum):
    """Group lifecycle status."""
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MemberStatus(str, Enum):
    """Member participation status."""
    INVITED = "invited"
    ACTIVE = "active"
    DECLINED = "declined"
    REMOVED = "removed"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class GroupMember:
    """Represents a member of a simulation group."""
    id: Optional[str] = None
    group_id: str = ""
    user_id: Optional[int] = None
    name: str = ""
    phone: Optional[str] = None
    email: Optional[str] = None
    contribution_amount: int = 0
    contribution_target: Optional[int] = None
    role: GroupRole = GroupRole.MEMBER
    status: MemberStatus = MemberStatus.INVITED
    joined_at: Optional[datetime] = None
    invited_at: Optional[datetime] = None

    def is_active(self) -> bool:
        return self.status == MemberStatus.ACTIVE


@dataclass
class SimulationGroup:
    """Represents a family/group Umrah planning session."""
    id: Optional[str] = None
    group_code: str = ""
    name: str = ""
    description: Optional[str] = None
    target_date: Optional[date] = None
    target_amount: Optional[int] = None
    simulation_params: Optional[Dict] = None
    simulation_breakdown: Optional[Dict] = None
    cost_per_person: Optional[int] = None
    leader_id: Optional[int] = None
    leader_name: str = ""
    leader_phone: Optional[str] = None
    status: GroupStatus = GroupStatus.ACTIVE
    is_public: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    members: List[GroupMember] = field(default_factory=list)


# =============================================================================
# DATABASE CONNECTION HELPER
# =============================================================================

def _get_db():
    """Get database connection singleton."""
    try:
        from services.database.repository import get_db
        return get_db()
    except Exception as e:
        logger.error(f"Failed to get database connection: {e}")
        return None


# =============================================================================
# CODE GENERATION
# =============================================================================

def generate_group_code() -> str:
    """
    Generate unique 8-character group code.
    Format: UMR + 5 alphanumeric characters (e.g., UMR1A2B3)
    """
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"UMR{suffix}"


def validate_group_code(code: str) -> bool:
    """Validate group code format."""
    if not code or len(code) != 8:
        return False
    return code.upper().startswith("UMR") and code[3:].isalnum()


# =============================================================================
# GROUP CRUD OPERATIONS
# =============================================================================

def create_group(
    name: str,
    leader_id: Optional[int] = None,
    leader_name: str = "",
    leader_phone: Optional[str] = None,
    target_date: Optional[date] = None,
    simulation_params: Optional[Dict] = None,
    simulation_breakdown: Optional[Dict] = None,
    cost_per_person: Optional[int] = None,
    description: Optional[str] = None,
) -> Optional[SimulationGroup]:
    """
    Create a new simulation group.

    Args:
        name: Group name (e.g., "Keluarga Pak Ahmad")
        leader_id: User ID of the group leader (optional if not logged in)
        leader_name: Display name of the leader
        leader_phone: Phone number for WhatsApp contact
        target_date: Target departure date
        simulation_params: Simulation input parameters dict
        simulation_breakdown: Cost breakdown dict
        cost_per_person: Estimated cost per person in IDR
        description: Optional group description

    Returns:
        SimulationGroup if created successfully, None otherwise
    """
    db = _get_db()
    if not db:
        logger.warning("Database not available, using session-only mode")
        # Return a mock group for session-only operation
        group_code = generate_group_code()
        return SimulationGroup(
            id=f"local_{group_code}",
            group_code=group_code,
            name=name,
            leader_id=leader_id,
            leader_name=leader_name,
            leader_phone=leader_phone,
            target_date=target_date,
            simulation_params=simulation_params,
            simulation_breakdown=simulation_breakdown,
            cost_per_person=cost_per_person,
            description=description,
            created_at=datetime.now(),
            status=GroupStatus.ACTIVE
        )

    # Generate unique group code
    group_code = generate_group_code()
    max_attempts = 10
    attempts = 0

    while attempts < max_attempts:
        existing = get_group_by_code(group_code)
        if existing is None:
            break
        group_code = generate_group_code()
        attempts += 1

    if attempts >= max_attempts:
        logger.error("Failed to generate unique group code")
        return None

    try:
        query = """
            INSERT INTO simulation_groups (
                group_code, name, description, target_date, target_amount,
                simulation_params, simulation_breakdown, cost_per_person,
                leader_id, leader_name, leader_phone, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'active')
            RETURNING id, group_code, created_at
        """

        # Calculate target amount (cost_per_person for now, updated when members join)
        target_amount = cost_per_person

        result = db.fetch_one(query, (
            group_code,
            name,
            description,
            target_date,
            target_amount,
            json.dumps(simulation_params) if simulation_params else None,
            json.dumps(simulation_breakdown) if simulation_breakdown else None,
            cost_per_person,
            leader_id,
            leader_name,
            leader_phone
        ))

        if result:
            group = SimulationGroup(
                id=str(result['id']),
                group_code=result['group_code'],
                name=name,
                description=description,
                target_date=target_date,
                target_amount=target_amount,
                simulation_params=simulation_params,
                simulation_breakdown=simulation_breakdown,
                cost_per_person=cost_per_person,
                leader_id=leader_id,
                leader_name=leader_name,
                leader_phone=leader_phone,
                created_at=result['created_at'],
                status=GroupStatus.ACTIVE
            )

            # Auto-add leader as first member
            if leader_name:
                add_member_to_group(
                    group_id=str(result['id']),
                    name=leader_name,
                    user_id=leader_id,
                    phone=leader_phone,
                    role=GroupRole.LEADER,
                    status=MemberStatus.ACTIVE
                )

            logger.info(f"Created group '{name}' with code {group_code}")
            return group

        return None

    except Exception as e:
        logger.error(f"Error creating group: {e}")
        return None


def get_group_by_code(code: str) -> Optional[SimulationGroup]:
    """
    Fetch a group by its shareable code.

    Args:
        code: Group code (e.g., "UMR1A2B3")

    Returns:
        SimulationGroup if found, None otherwise
    """
    db = _get_db()
    if not db:
        return None

    try:
        query = "SELECT * FROM simulation_groups WHERE group_code = %s AND status = 'active'"
        result = db.fetch_one(query, (code.upper(),))
        return _row_to_group(result) if result else None
    except Exception as e:
        logger.error(f"Error fetching group by code: {e}")
        return None


def get_group_by_id(group_id: str) -> Optional[SimulationGroup]:
    """
    Fetch a group by its ID.

    Args:
        group_id: Group UUID

    Returns:
        SimulationGroup if found, None otherwise
    """
    db = _get_db()
    if not db:
        return None

    try:
        query = "SELECT * FROM simulation_groups WHERE id = %s"
        result = db.fetch_one(query, (group_id,))
        return _row_to_group(result) if result else None
    except Exception as e:
        logger.error(f"Error fetching group by ID: {e}")
        return None


def get_groups_by_user(user_id: int) -> List[SimulationGroup]:
    """
    Fetch all groups where the user is a member.

    Args:
        user_id: User's ID

    Returns:
        List of SimulationGroup objects
    """
    db = _get_db()
    if not db:
        return []

    try:
        query = """
            SELECT sg.* FROM simulation_groups sg
            JOIN group_members gm ON sg.id = gm.group_id
            WHERE gm.user_id = %s AND sg.status = 'active' AND gm.status = 'active'
            ORDER BY sg.updated_at DESC
        """
        results = db.fetch_all(query, (user_id,))
        return [_row_to_group(r) for r in results] if results else []
    except Exception as e:
        logger.error(f"Error fetching groups for user: {e}")
        return []


def update_group_simulation(
    group_id: str,
    simulation_params: Dict,
    simulation_breakdown: Dict,
    cost_per_person: int
) -> bool:
    """
    Update the simulation data for a group.

    Args:
        group_id: Group UUID
        simulation_params: Updated simulation parameters
        simulation_breakdown: Updated cost breakdown
        cost_per_person: Updated cost per person

    Returns:
        True if update successful, False otherwise
    """
    db = _get_db()
    if not db:
        return False

    try:
        query = """
            UPDATE simulation_groups
            SET simulation_params = %s,
                simulation_breakdown = %s,
                cost_per_person = %s,
                updated_at = NOW()
            WHERE id = %s
        """
        db.execute(query, (
            json.dumps(simulation_params),
            json.dumps(simulation_breakdown),
            cost_per_person,
            group_id
        ))
        return True
    except Exception as e:
        logger.error(f"Error updating group simulation: {e}")
        return False


# =============================================================================
# MEMBER OPERATIONS
# =============================================================================

def add_member_to_group(
    group_id: str,
    name: str,
    user_id: Optional[int] = None,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    role: GroupRole = GroupRole.MEMBER,
    status: MemberStatus = MemberStatus.INVITED,
) -> Optional[GroupMember]:
    """
    Add a member to a group.

    Args:
        group_id: Group UUID
        name: Member's display name
        user_id: User ID if registered (optional)
        phone: Phone number (optional)
        email: Email address (optional)
        role: Member role (leader, co_leader, member)
        status: Initial status (invited, active)

    Returns:
        GroupMember if added successfully, None otherwise
    """
    db = _get_db()
    if not db:
        # Return mock member for session-only mode
        return GroupMember(
            id=f"local_{name}",
            group_id=group_id,
            user_id=user_id,
            name=name,
            phone=phone,
            email=email,
            role=role,
            status=status,
            joined_at=datetime.now() if status == MemberStatus.ACTIVE else None
        )

    try:
        query = """
            INSERT INTO group_members (
                group_id, user_id, name, phone, email, role, status, joined_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (group_id, user_id) WHERE user_id IS NOT NULL DO UPDATE SET
                name = EXCLUDED.name,
                status = EXCLUDED.status,
                joined_at = COALESCE(group_members.joined_at, EXCLUDED.joined_at),
                updated_at = NOW()
            RETURNING id
        """

        joined_at = datetime.now() if status == MemberStatus.ACTIVE else None

        result = db.fetch_one(query, (
            group_id, user_id, name, phone, email,
            role.value, status.value, joined_at
        ))

        if result:
            return GroupMember(
                id=str(result['id']),
                group_id=group_id,
                user_id=user_id,
                name=name,
                phone=phone,
                email=email,
                role=role,
                status=status,
                joined_at=joined_at
            )
        return None

    except Exception as e:
        logger.error(f"Error adding member to group: {e}")
        return None


def get_group_members(group_id: str) -> List[GroupMember]:
    """
    Get all members of a group.

    Args:
        group_id: Group UUID

    Returns:
        List of GroupMember objects
    """
    db = _get_db()
    if not db:
        return []

    try:
        query = """
            SELECT * FROM group_members
            WHERE group_id = %s AND status != 'removed'
            ORDER BY
                CASE role WHEN 'leader' THEN 0 WHEN 'co_leader' THEN 1 ELSE 2 END,
                joined_at NULLS LAST
        """
        results = db.fetch_all(query, (group_id,))
        return [_row_to_member(r) for r in results] if results else []
    except Exception as e:
        logger.error(f"Error fetching group members: {e}")
        return []


def get_member_by_user_id(group_id: str, user_id: int) -> Optional[GroupMember]:
    """
    Get a specific member by user ID.

    Args:
        group_id: Group UUID
        user_id: User's ID

    Returns:
        GroupMember if found, None otherwise
    """
    db = _get_db()
    if not db:
        return None

    try:
        query = """
            SELECT * FROM group_members
            WHERE group_id = %s AND user_id = %s AND status != 'removed'
        """
        result = db.fetch_one(query, (group_id, user_id))
        return _row_to_member(result) if result else None
    except Exception as e:
        logger.error(f"Error fetching member: {e}")
        return None


def activate_member(group_id: str, user_id: int) -> bool:
    """
    Activate a member (when they accept invite or join via link).

    Args:
        group_id: Group UUID
        user_id: User's ID

    Returns:
        True if activation successful, False otherwise
    """
    db = _get_db()
    if not db:
        return True  # Assume success in session-only mode

    try:
        query = """
            UPDATE group_members
            SET status = 'active', joined_at = NOW(), updated_at = NOW()
            WHERE group_id = %s AND user_id = %s
        """
        db.execute(query, (group_id, user_id))
        logger.info(f"Activated member {user_id} in group {group_id}")
        return True
    except Exception as e:
        logger.error(f"Error activating member: {e}")
        return False


def update_member_contribution(
    group_id: str,
    user_id: int,
    amount: int
) -> bool:
    """
    Update a member's contribution amount.

    Args:
        group_id: Group UUID
        user_id: User's ID
        amount: New contribution amount in IDR

    Returns:
        True if update successful, False otherwise
    """
    db = _get_db()
    if not db:
        return False

    try:
        query = """
            UPDATE group_members
            SET contribution_amount = %s, updated_at = NOW()
            WHERE group_id = %s AND user_id = %s
        """
        db.execute(query, (amount, group_id, user_id))
        return True
    except Exception as e:
        logger.error(f"Error updating contribution: {e}")
        return False


# =============================================================================
# GROUP ANALYTICS
# =============================================================================

def calculate_group_totals(group_id: str) -> Dict[str, Any]:
    """
    Calculate group financial totals.

    Args:
        group_id: Group UUID

    Returns:
        Dictionary with:
        - total_members: Number of active members
        - total_target: Total amount needed (cost_per_person * members)
        - total_collected: Sum of all contributions
        - total_remaining: Amount still needed
        - per_person_remaining: Remaining per person
        - progress_percentage: Collection progress (0-100)
        - cost_per_person: Cost per individual
    """
    group = get_group_by_id(group_id)
    if not group:
        return {}

    members = get_group_members(group_id)
    active_members = [m for m in members if m.status == MemberStatus.ACTIVE]

    if not active_members:
        return {
            "total_members": 0,
            "total_target": 0,
            "total_collected": 0,
            "total_remaining": 0,
            "per_person_remaining": 0,
            "progress_percentage": 0,
            "cost_per_person": group.cost_per_person or 0,
        }

    # Calculate totals
    total_collected = sum(m.contribution_amount for m in active_members)
    cost_per_person = group.cost_per_person or 0
    total_target = cost_per_person * len(active_members)
    remaining = max(0, total_target - total_collected)
    per_person_remaining = remaining // len(active_members) if active_members else 0
    progress = (total_collected / total_target * 100) if total_target > 0 else 0

    return {
        "total_members": len(active_members),
        "total_target": total_target,
        "total_collected": total_collected,
        "total_remaining": remaining,
        "per_person_remaining": per_person_remaining,
        "progress_percentage": round(progress, 1),
        "cost_per_person": cost_per_person,
        "members": active_members,
    }


# =============================================================================
# SHARING UTILITIES
# =============================================================================

def generate_share_url(group_code: str, base_url: str = None) -> str:
    """
    Generate shareable URL with group code.

    Args:
        group_code: The group's shareable code
        base_url: Base URL of the app (defaults to labbaik.streamlit.app)

    Returns:
        Full shareable URL
    """
    if base_url is None:
        # Try to get from environment or use default
        import os
        base_url = os.environ.get("APP_BASE_URL", "https://labbaik.streamlit.app")

    return f"{base_url}/?group_id={group_code}"


def generate_whatsapp_share_link(
    group: SimulationGroup,
    share_url: str
) -> str:
    """
    Generate WhatsApp share link with formatted message.

    Args:
        group: SimulationGroup object
        share_url: The shareable URL

    Returns:
        WhatsApp share URL (https://wa.me/?text=...)
    """
    import urllib.parse

    # Format cost
    cost_formatted = f"Rp {group.cost_per_person:,.0f}" if group.cost_per_person else "TBD"

    # Format target date
    if group.target_date:
        if isinstance(group.target_date, str):
            date_formatted = group.target_date
        else:
            date_formatted = group.target_date.strftime('%d %b %Y')
    else:
        date_formatted = "Belum ditentukan"

    message = f"""Assalamualaikum!

Yuk gabung rencana Umrah keluarga kita di LABBAIK AI:

*{group.name}*
Estimasi: {cost_formatted}/orang
Target: {date_formatted}

Klik untuk lihat detail:
{share_url}

Kode Grup: *{group.group_code}*""".strip()

    encoded_message = urllib.parse.quote(message)
    return f"https://wa.me/?text={encoded_message}"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _row_to_group(row: Dict) -> SimulationGroup:
    """Convert database row to SimulationGroup object."""
    if not row:
        return None

    # Parse JSON fields
    sim_params = None
    sim_breakdown = None

    if row.get('simulation_params'):
        try:
            sim_params = json.loads(row['simulation_params']) if isinstance(row['simulation_params'], str) else row['simulation_params']
        except (json.JSONDecodeError, TypeError):
            pass

    if row.get('simulation_breakdown'):
        try:
            sim_breakdown = json.loads(row['simulation_breakdown']) if isinstance(row['simulation_breakdown'], str) else row['simulation_breakdown']
        except (json.JSONDecodeError, TypeError):
            pass

    return SimulationGroup(
        id=str(row.get('id', '')),
        group_code=row.get('group_code', ''),
        name=row.get('name', ''),
        description=row.get('description'),
        target_date=row.get('target_date'),
        target_amount=row.get('target_amount'),
        simulation_params=sim_params,
        simulation_breakdown=sim_breakdown,
        cost_per_person=row.get('cost_per_person'),
        leader_id=row.get('leader_id'),
        leader_name=row.get('leader_name', ''),
        leader_phone=row.get('leader_phone'),
        status=GroupStatus(row.get('status', 'active')),
        is_public=row.get('is_public', False),
        created_at=row.get('created_at'),
        updated_at=row.get('updated_at'),
    )


def _row_to_member(row: Dict) -> GroupMember:
    """Convert database row to GroupMember object."""
    if not row:
        return None

    return GroupMember(
        id=str(row.get('id', '')),
        group_id=str(row.get('group_id', '')),
        user_id=row.get('user_id'),
        name=row.get('name', ''),
        phone=row.get('phone'),
        email=row.get('email'),
        contribution_amount=row.get('contribution_amount', 0),
        contribution_target=row.get('contribution_target'),
        role=GroupRole(row.get('role', 'member')),
        status=MemberStatus(row.get('status', 'invited')),
        joined_at=row.get('joined_at'),
        invited_at=row.get('invited_at'),
    )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "GroupRole",
    "GroupStatus",
    "MemberStatus",
    # Data classes
    "GroupMember",
    "SimulationGroup",
    # Code generation
    "generate_group_code",
    "validate_group_code",
    # Group CRUD
    "create_group",
    "get_group_by_code",
    "get_group_by_id",
    "get_groups_by_user",
    "update_group_simulation",
    # Member operations
    "add_member_to_group",
    "get_group_members",
    "get_member_by_user_id",
    "activate_member",
    "update_member_contribution",
    # Analytics
    "calculate_group_totals",
    # Sharing
    "generate_share_url",
    "generate_whatsapp_share_link",
]
