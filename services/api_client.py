"""
LABBAIK API Client for Streamlit
================================
Async HTTP client for connecting Streamlit to FastAPI backend.
"""

import asyncio
import httpx
import os
from typing import Optional, Dict, Any, List
import streamlit as st


# API Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")


class LabbaikAPIClient:
    """Async API client for LABBAIK backend."""
    
    def __init__(self, token: Optional[str] = None):
        """Initialize client with optional auth token."""
        self.base_url = API_URL
        self.token = token
        self.headers = {
            "Content-Type": "application/json"
        }
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
    
    # ==========================================================================
    # AUTHENTICATION
    # ==========================================================================
    
    async def register(
        self,
        email: str,
        password: str,
        full_name: str,
        phone: Optional[str] = None
    ) -> Dict[str, Any]:
        """Register new user."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/auth/register",
                json={
                    "email": email,
                    "password": password,
                    "full_name": full_name,
                    "phone": phone
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """Login user."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/auth/login/email",
                json={"email": email, "password": password}
            )
            response.raise_for_status()
            return response.json()
    
    async def get_current_user(self) -> Dict[str, Any]:
        """Get current user info."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/auth/me",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    # ==========================================================================
    # UMRAH BARENG
    # ==========================================================================
    
    async def get_trips(
        self,
        departure_city: Optional[str] = None,
        budget_min: Optional[int] = None,
        budget_max: Optional[int] = None,
        page: int = 1,
        per_page: int = 20
    ) -> List[Dict[str, Any]]:
        """Get list of Umrah Bareng trips."""
        params = {
            "page": page,
            "per_page": per_page
        }
        if departure_city:
            params["departure_city"] = departure_city
        if budget_min:
            params["budget_min"] = budget_min
        if budget_max:
            params["budget_max"] = budget_max
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/bareng/trips",
                params=params
            )
            response.raise_for_status()
            return response.json()
    
    async def create_trip(self, trip_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new Umrah Bareng trip."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/bareng/trips",
                json=trip_data,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def join_trip(self, trip_id: str, message: str = "") -> Dict[str, Any]:
        """Join Umrah Bareng trip."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/bareng/trips/{trip_id}/join",
                json={"message": message},
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    # ==========================================================================
    # COST SIMULATION
    # ==========================================================================
    
    async def simulate_cost(
        self,
        departure_city: str,
        duration_days: int,
        num_participants: int
    ) -> Dict[str, Any]:
        """Simulate Umrah cost."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/cost/simulate",
                json={
                    "departure_city": departure_city,
                    "duration_days": duration_days,
                    "num_participants": num_participants
                }
            )
            response.raise_for_status()
            return response.json()
    
    # ==========================================================================
    # AI CHAT
    # ==========================================================================
    
    async def chat(self, question: str) -> Dict[str, Any]:
        """Ask AI about Umrah."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat",
                json={"question": question}
            )
            response.raise_for_status()
            return response.json()


# ==========================================================================
# HELPER FUNCTIONS FOR STREAMLIT
# ==========================================================================

def run_async(coro):
    """Run async function in Streamlit synchronous context."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


def get_api_client(session_state) -> LabbaikAPIClient:
    """Get API client with token from session state."""
    token = session_state.get("access_token")
    return LabbaikAPIClient(token=token)


def save_token(session_state, access_token: str, refresh_token: str = None):
    """Save tokens to session state."""
    session_state["access_token"] = access_token
    if refresh_token:
        session_state["refresh_token"] = refresh_token
    session_state["is_authenticated"] = True


def clear_token(session_state):
    """Clear tokens from session state."""
    if "access_token" in session_state:
        del session_state["access_token"]
    if "refresh_token" in session_state:
        del session_state["refresh_token"]
    session_state["is_authenticated"] = False


def is_authenticated(session_state) -> bool:
    """Check if user is authenticated."""
    return session_state.get("is_authenticated", False)
