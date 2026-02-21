"""
================================================================================
LABBAIK AI - AI SERVICE HELPERS
================================================================================
Cached AI service + convenience functions used across feature pages.
Eliminates duplicate Groq init/try-except code in every page.
================================================================================
"""

from typing import Optional

import streamlit as st
import os


def _get_groq_api_key() -> str:
    """Resolve GROQ API key from secrets or environment."""
    try:
        key = st.secrets.get("GROQ_API_KEY", "")
        if key:
            return key
    except Exception:
        pass
    return os.getenv("GROQ_API_KEY", "")


@st.cache_resource(ttl=3600)
def _init_groq_service(api_key: str) -> Optional["GroqChatService"]:
    """Create and cache a GroqChatService instance."""
    try:
        from services.ai.chat_service import GroqChatService
        service = GroqChatService(api_key=api_key)
        service.initialize()
        return service
    except Exception:
        return None


def get_groq_service() -> Optional["GroqChatService"]:
    """Get a cached GroqChatService instance. Returns None if unavailable."""
    api_key = _get_groq_api_key()
    if not api_key:
        return None
    return _init_groq_service(api_key)


def ai_complete(prompt: str, system_prompt: str = "", max_tokens: int = 512) -> Optional[str]:
    """Simple AI completion with graceful fallback.

    Returns the response string, or None if the service is unavailable.
    """
    service = get_groq_service()
    if not service:
        return None
    try:
        return service.simple_complete(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
        )
    except Exception:
        return None


def add_xp_safe(amount: int, reason: str = "") -> None:
    """Award XP via the main app gamification system, with fallback.

    Tries app.add_xp first; if import fails (e.g. circular import),
    falls back to direct session state manipulation.
    """
    try:
        from app import add_xp
        add_xp(amount, reason)
    except Exception:
        if "user_xp" in st.session_state:
            st.session_state.user_xp = st.session_state.get("user_xp", 0) + amount
        elif "xp" in st.session_state:
            st.session_state.xp = st.session_state.get("xp", 0) + amount
        if reason:
            try:
                st.toast(f"+{amount} XP: {reason}")
            except Exception:
                pass


__all__ = ["get_groq_service", "ai_complete", "add_xp_safe"]
