"""
LABBAIK AI - Utility Functions
"""

from utils.pricing_loader import (
    get_pricing_config,
    get_current_batch,
    get_batch_by_name,
    get_all_batches,
    format_currency,
)

from utils.package_calculator import (
    PackageScenario,
    PackageCostBreakdown,
    calculate_package,
    compare_scenarios,
    generate_price_tiers,
)

from utils.group_manager import (
    # Enums
    GroupRole,
    GroupStatus,
    MemberStatus,
    # Data classes
    GroupMember,
    SimulationGroup,
    # Functions
    generate_group_code,
    create_group,
    get_group_by_code,
    get_group_by_id,
    get_groups_by_user,
    get_group_members,
    add_member_to_group,
    activate_member,
    calculate_group_totals,
    generate_share_url,
    generate_whatsapp_share_link,
)

__all__ = [
    # Pricing loader
    "get_pricing_config",
    "get_current_batch",
    "get_batch_by_name",
    "get_all_batches",
    "format_currency",
    # Package calculator
    "PackageScenario",
    "PackageCostBreakdown",
    "calculate_package",
    "compare_scenarios",
    "generate_price_tiers",
    # Group manager
    "GroupRole",
    "GroupStatus",
    "MemberStatus",
    "GroupMember",
    "SimulationGroup",
    "generate_group_code",
    "create_group",
    "get_group_by_code",
    "get_group_by_id",
    "get_groups_by_user",
    "get_group_members",
    "add_member_to_group",
    "activate_member",
    "calculate_group_totals",
    "generate_share_url",
    "generate_whatsapp_share_link",
]
