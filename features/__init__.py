"""
LABBAIK AI - Enhanced Features Package
======================================
Advanced features for Umrah planning platform.

Features included:
1. Crowd Prediction - Masjid crowd level predictions
2. SOS Emergency - One-tap emergency with WhatsApp
3. Group Tracking - Real-time location sharing
4. 3D Manasik - Interactive ritual simulation
5. Smart Comparison - AI-powered package comparison
6. Analytics Dashboard - Enhanced visitor analytics
7. WhatsApp Service - WAHA integration for notifications
8. Doa Player - Voice-guided doa/dzikir
9. WhatsApp Bot - Intelligent chat bot
10. Live Price Updates - Real-time package pricing
"""

# Crowd Prediction
try:
    from features.crowd_prediction import (
        CrowdPredictor,
        render_crowd_widget,
        render_24h_forecast,
        render_weekly_heatmap,
        render_crowd_prediction_page,
    )
except ImportError:
    pass

# SOS Emergency
try:
    from features.sos_emergency import (
        SOSService,
        EmergencyType,
        EmergencyContact,
        render_sos_button,
        render_sos_setup,
        render_sos_activated,
        render_sos_page,
        EMERGENCY_CONTACTS_SAUDI,
    )
except ImportError:
    pass

# Group Tracking
try:
    from features.group_tracking import (
        GroupTrackingService,
        TravelGroup,
        GroupMember,
        MemberStatus,
        render_group_tracking_page,
        render_tracking_mini_widget,
        render_member_card,
        create_demo_group,
    )
except ImportError:
    pass

# 3D Manasik
try:
    from features.manasik_3d import (
        render_3d_kaaba,
        render_manasik_page,
        render_manasik_mini_widget,
        render_ritual_step_card,
        RITUALS_DATA,
        RitualStep,
    )
except ImportError:
    pass

# Smart Comparison
try:
    from features.smart_comparison import (
        render_smart_comparison_page,
        render_package_card,
        render_comparison_table,
        get_sample_packages,
        match_packages,
        PackageDetails,
        UserPreferences,
    )
except ImportError:
    pass

# WhatsApp Service (WAHA)
try:
    from features.whatsapp_service import (
        WAHAClient,
        WhatsAppService,
        MessageTemplates,
        render_whatsapp_status,
        render_whatsapp_test,
        render_whatsapp_settings,
        send_sos_via_whatsapp,
    )
except ImportError:
    pass

# WhatsApp Bot — removed (features/whatsapp_bot.py deleted; use services/whatsapp/)

# Doa Player — moved to ui/pages/doa_player.py

# Umrah Complete Guide
try:
    from features.umrah_complete import (
        render_umrah_complete_page,
        render_doa_card_enhanced,
    )
    from features.umrah_guide import (
        UMRAH_DEFINITION,
        UMRAH_VIRTUES,
        UMRAH_PILLARS,
        UMRAH_SUNNAHS,
        MIQAT_LOCATIONS,
        HISTORICAL_SITES,
        UMRAH_PROCEDURES,
    )
except ImportError:
    pass

# PWA Support
try:
    from features.pwa_support import (
        init_pwa,
        render_install_button,
        render_pwa_settings_page,
        render_offline_indicator,
        PWA_MANIFEST,
        OFFLINE_HTML,
    )
except ImportError:
    pass

__all__ = [
    # Crowd Prediction
    "CrowdPredictor",
    "render_crowd_widget",
    "render_24h_forecast",
    "render_weekly_heatmap",
    "render_crowd_prediction_page",
    
    # SOS Emergency
    "SOSService",
    "EmergencyType",
    "EmergencyContact",
    "render_sos_button",
    "render_sos_setup",
    "render_sos_activated",
    "render_sos_page",
    "EMERGENCY_CONTACTS_SAUDI",
    
    # Group Tracking
    "GroupTrackingService",
    "TravelGroup",
    "GroupMember",
    "MemberStatus",
    "render_group_tracking_page",
    "render_tracking_mini_widget",
    "render_member_card",
    "create_demo_group",
    
    # 3D Manasik
    "render_3d_kaaba",
    "render_manasik_page",
    "render_manasik_mini_widget",
    "render_ritual_step_card",
    "RITUALS_DATA",
    "RitualStep",
    
    # Smart Comparison
    "render_smart_comparison_page",
    "render_package_card",
    "render_comparison_table",
    "get_sample_packages",
    "match_packages",
    "PackageDetails",
    "UserPreferences",
    
    # WhatsApp Service
    "WAHAClient",
    "WhatsAppService",
    "MessageTemplates",
    "render_whatsapp_status",
    "render_whatsapp_test",
    "render_whatsapp_settings",
    "send_sos_via_whatsapp",

    # WhatsApp Bot — removed (use services/whatsapp/)
    # Doa Player — moved to ui/pages/doa_player.py

    # Umrah Complete Guide
    "render_umrah_complete_page",
    "render_doa_card_enhanced",
    "UMRAH_DEFINITION",
    "UMRAH_VIRTUES",
    "UMRAH_PILLARS",
    "UMRAH_SUNNAHS",
    "MIQAT_LOCATIONS",
    "HISTORICAL_SITES",
    "UMRAH_PROCEDURES",

    # PWA Support
    "init_pwa",
    "render_install_button",
    "render_pwa_settings_page",
    "render_offline_indicator",
    "PWA_MANIFEST",
    "OFFLINE_HTML",
]

# Dynamic Version
try:
    from core.version import APP_VERSION as __version__
except ImportError:
    __version__ = "7.8.0"
