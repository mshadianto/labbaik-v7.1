"""
LABBAIK AI - Initialize Admin User
===================================
Run once to create admin account.

Usage:
    # Using environment variables (recommended)
    export ADMIN_EMAIL="your_email@example.com"
    export ADMIN_PASSWORD="your_secure_password"
    python scripts/init_admin.py

    # Or using .streamlit/secrets.toml
    python scripts/init_admin.py
"""

import sys
import os
import getpass

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.user.user_service import UserService, UserRole, UserStatus


def get_credentials():
    """Get admin credentials from environment or prompt"""

    # Try environment variables first
    email = os.environ.get("ADMIN_EMAIL")
    password = os.environ.get("ADMIN_PASSWORD")
    name = os.environ.get("ADMIN_NAME", "Admin")

    # Try streamlit secrets
    if not email or not password:
        try:
            import streamlit as st
            if hasattr(st, 'secrets'):
                email = email or st.secrets.get("ADMIN_EMAIL")
                password = password or st.secrets.get("ADMIN_PASSWORD")
                name = name or st.secrets.get("ADMIN_NAME", "Admin")
        except Exception:
            pass

    # Prompt if still not set
    if not email:
        email = input("Admin Email: ").strip()

    if not password:
        password = getpass.getpass("Admin Password: ").strip()

    if not name or name == "Admin":
        name_input = input("Admin Name (Enter to skip): ").strip()
        if name_input:
            name = name_input

    return email, password, name


def validate_credentials(email: str, password: str) -> tuple:
    """Validate credentials"""
    errors = []

    if not email or "@" not in email:
        errors.append("Email tidak valid")

    if not password or len(password) < 8:
        errors.append("Password minimal 8 karakter")

    return len(errors) == 0, errors


def create_admin():
    """Create admin user"""
    service = UserService()

    # Get credentials
    email, password, name = get_credentials()

    # Validate
    is_valid, errors = validate_credentials(email, password)
    if not is_valid:
        for err in errors:
            print(f"[ERROR] {err}")
        return None

    # Check if already exists
    existing = service.get_user_by_email(email)
    if existing:
        if existing.role == UserRole.ADMIN:
            print(f"[OK] Admin sudah ada: {email}")
            return existing
        else:
            # Upgrade to admin
            existing.role = UserRole.ADMIN
            existing.status = UserStatus.ACTIVE
            service.repo.update(existing)
            print(f"[OK] User di-upgrade ke Admin: {email}")
            return existing

    # Create new admin
    success, message, user = service.register(
        email=email,
        password=password,
        name=name,
        source="system"
    )

    if success and user:
        # Set as admin
        user.role = UserRole.ADMIN
        user.status = UserStatus.ACTIVE
        service.repo.update(user)
        print(f"[OK] Admin berhasil dibuat!")
        print(f"    Email: {email}")
        print(f"    [!] Simpan password Anda dengan aman!")
        return user
    else:
        print(f"[ERROR] Gagal membuat admin: {message}")
        return None


if __name__ == "__main__":
    print("=" * 50)
    print("LABBAIK AI - Admin Initialization")
    print("=" * 50)
    print()
    print("Set credentials via:")
    print("  - Environment: ADMIN_EMAIL, ADMIN_PASSWORD")
    print("  - Secrets: .streamlit/secrets.toml")
    print("  - Or enter manually below")
    print()
    create_admin()
    print()
    print("=" * 50)
