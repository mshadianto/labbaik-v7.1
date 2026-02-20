"""
LABBAIK AI - API Documentation Page
=====================================
Interactive API documentation for partners.
"""

import streamlit as st
from services.partner_api import API_ENDPOINTS, get_partner_api
from services.user import get_current_user, is_logged_in, UserRole
from services.ai.helpers import add_xp_safe
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS


def render_api_docs_page():
    """Main API documentation page"""
    try:
        from services.analytics import track_page
        track_page("api_docs")
    except Exception:
        pass

    inject_css(HERO_CSS, CARD_CSS)

    if not st.session_state.get("api_docs_xp_awarded"):
        add_xp_safe(5, "Membaca dokumentasi API")
        st.session_state.api_docs_xp_awarded = True

    st.markdown("""
        <div class="page-hero">
            <h1><span aria-hidden="true">📚</span> Dokumentasi API</h1>
            <div class="subtitle">Referensi lengkap Partner REST API LABBAIK</div>
        </div>
    """, unsafe_allow_html=True)

    # Quick links
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
            <div style="background: rgba(33,150,243,0.1); padding: 1rem; border-radius: 12px; text-align: center;">
                <div style="font-size: 2rem;" aria-hidden="true">🔑</div>
                <div style="font-weight: bold;">Authentication</div>
                <div style="font-size: 0.8rem; color: #b0b0b0;">API Key based auth</div>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
            <div style="background: rgba(76,175,80,0.1); padding: 1rem; border-radius: 12px; text-align: center;">
                <div style="font-size: 2rem;" aria-hidden="true">📦</div>
                <div style="font-weight: bold;">RESTful</div>
                <div style="font-size: 0.8rem; color: #b0b0b0;">JSON responses</div>
            </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
            <div style="background: rgba(255,152,0,0.1); padding: 1rem; border-radius: 12px; text-align: center;">
                <div style="font-size: 2rem;" aria-hidden="true">🔔</div>
                <div style="font-weight: bold;">Webhooks</div>
                <div style="font-size: 0.8rem; color: #b0b0b0;">Real-time events</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Getting Started",
        "Authentication",
        "Endpoints",
        "Webhooks",
        "API Console"
    ])

    with tab1:
        render_getting_started()

    with tab2:
        render_authentication_docs()

    with tab3:
        render_endpoints_docs()

    with tab4:
        render_webhooks_docs()

    with tab5:
        render_api_console()


def render_getting_started():
    """Getting started section"""
    st.markdown("### Getting Started")

    st.markdown("""
    #### Base URL
    ```
    https://api.labbaik.io/api/v1
    ```

    #### Quick Start

    1. **Dapatkan API Key** - Daftar sebagai partner dan generate API key di dashboard
    2. **Autentikasi** - Sertakan API key di header setiap request
    3. **Mulai Integrasi** - Gunakan endpoints yang tersedia

    #### Request Format
    ```bash
    curl -X GET "https://api.labbaik.io/api/v1/packages" \\
      -H "Authorization: Bearer lbk_live_xxxxxxxxxxxx" \\
      -H "Content-Type: application/json"
    ```

    #### Response Format
    Semua response dalam format JSON:
    ```json
    {
      "success": true,
      "data": { ... },
      "message": "Optional message",
      "pagination": {
        "page": 1,
        "limit": 20,
        "total": 100
      }
    }
    ```

    #### Error Response
    ```json
    {
      "success": false,
      "error": "error_code",
      "message": "Human readable error message"
    }
    ```
    """)

    st.markdown("#### Error Codes")

    errors = [
        ("400", "bad_request", "Invalid request format or missing required fields"),
        ("401", "unauthorized", "Invalid or missing API key"),
        ("403", "permission_denied", "API key doesn't have required permission"),
        ("404", "not_found", "Resource not found"),
        ("429", "rate_limited", "Too many requests, try again later"),
        ("500", "internal_error", "Server error, contact support"),
    ]

    st.markdown("""
    | HTTP Code | Error Code | Description |
    |-----------|------------|-------------|
    """ + "\n".join([f"| {code} | `{err}` | {desc} |" for code, err, desc in errors]))


def render_authentication_docs():
    """Authentication documentation"""
    st.markdown("### Authentication")

    st.markdown("""
    #### API Key Authentication

    Semua API request harus menyertakan API key di header `Authorization`:

    ```http
    Authorization: Bearer lbk_live_xxxxxxxxxxxxxxxxxxxx
    ```

    #### Mendapatkan API Key

    1. Login ke dashboard partner
    2. Buka menu **Settings > API Keys**
    3. Klik **Generate New Key**
    4. Simpan key dengan aman (hanya ditampilkan sekali!)

    #### Permissions

    API key dapat memiliki permission berbeda:
    """)

    permissions = [
        ("packages:read", "Membaca data paket"),
        ("packages:write", "Membuat/update/delete paket"),
        ("bookings:read", "Membaca data booking"),
        ("bookings:write", "Membuat/update booking"),
        ("webhooks:read", "Melihat konfigurasi webhook"),
        ("webhooks:write", "Mengatur webhook"),
        ("analytics:read", "Melihat analytics"),
    ]

    for perm, desc in permissions:
        st.markdown(f"- `{perm}` - {desc}")

    st.markdown("""
    #### Rate Limits

    | Plan | Requests/Day |
    |------|--------------|
    | Silver | 1,000 |
    | Gold | 10,000 |
    | Enterprise | Unlimited |

    Rate limit info tersedia di response header:
    ```http
    X-RateLimit-Limit: 1000
    X-RateLimit-Remaining: 950
    X-RateLimit-Reset: 1640995200
    ```
    """)

    # Show user's API keys if logged in
    user = get_current_user()
    if user and user.role in [UserRole.PARTNER, UserRole.ADMIN]:
        st.markdown("---")
        st.markdown("#### Your API Keys")

        api = get_partner_api()
        keys = api.get_partner_keys(user.id)

        if keys:
            for key in keys:
                status_color = "#4CAF50" if key.status.value == "active" else "#F44336"
                st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; align-items: center;
                                padding: 0.75rem; background: rgba(255,255,255,0.05);
                                border-radius: 8px; margin: 0.5rem 0;">
                        <div>
                            <code>{key.key_prefix}...</code>
                            <span style="color: #b0b0b0; margin-left: 1rem;">{key.name}</span>
                        </div>
                        <div style="color: {status_color};">● {key.status.value}</div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Belum ada API key. Generate key baru di bawah.")

        if st.button("Generate New API Key", type="primary"):
            full_key, key_obj = api.create_api_key(user.id, "Generated via Docs")
            st.success("API Key berhasil dibuat!")
            st.code(full_key)
            st.warning("Simpan key ini! Tidak akan ditampilkan lagi.")


def render_endpoints_docs():
    """Endpoints documentation"""
    st.markdown("### API Endpoints")

    for category, endpoints in API_ENDPOINTS.items():
        st.markdown(f"#### {category.title()}")

        for endpoint, details in endpoints.items():
            with st.expander(f"**{endpoint}** - {details.get('description', '')}"):
                # Permissions
                perms = details.get("permissions", [])
                if perms:
                    st.markdown(f"**Permissions:** `{', '.join(perms)}`")

                # Parameters
                params = details.get("params")
                if params:
                    st.markdown("**Query Parameters:**")
                    for param, desc in params.items():
                        st.markdown(f"- `{param}`: {desc}")

                # Request body
                body = details.get("body")
                if body:
                    st.markdown("**Request Body:**")
                    st.json(body)

                # Response
                response = details.get("response")
                if response:
                    st.markdown("**Response:**")
                    st.json(response)

                # Events (for webhooks)
                events = details.get("events")
                if events:
                    st.markdown("**Available Events:**")
                    for event in events:
                        st.markdown(f"- `{event}`")

                # Example
                st.markdown("**Example:**")
                method = endpoint.split()[0]
                path = endpoint.split()[1]

                example = f"""```bash
curl -X {method} "https://api.labbaik.io{path}" \\
  -H "Authorization: Bearer lbk_live_xxxx" \\
  -H "Content-Type: application/json"
```"""
                st.markdown(example)


def render_webhooks_docs():
    """Webhooks documentation"""
    st.markdown("### Webhooks")

    st.markdown("""
    Webhooks memungkinkan Anda menerima notifikasi real-time saat event terjadi.

    #### Setup Webhook

    1. Siapkan endpoint HTTPS di server Anda
    2. Daftarkan webhook via API atau dashboard
    3. Verifikasi signature untuk keamanan

    #### Webhook Payload

    ```json
    {
      "event": "booking.created",
      "timestamp": "2025-12-26T10:30:00Z",
      "data": {
        "booking_code": "LBK-XXXX",
        "customer_name": "Ahmad",
        "package_id": 123,
        "total_price": 25000000
      },
      "signature": "sha256=xxxxxxxxxxxx"
    }
    ```

    #### Verifikasi Signature

    ```python
    import hmac
    import hashlib

    def verify_webhook(payload, signature, secret):
        expected = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(f"sha256={expected}", signature)
    ```

    #### Available Events
    """)

    events = [
        ("booking.created", "Booking baru dibuat"),
        ("booking.confirmed", "Booking dikonfirmasi"),
        ("booking.cancelled", "Booking dibatalkan"),
        ("payment.received", "Pembayaran diterima"),
        ("package.updated", "Paket diupdate"),
    ]

    for event, desc in events:
        st.markdown(f"- `{event}` - {desc}")

    st.markdown("""
    #### Retry Policy

    Jika webhook gagal (non-2xx response), kami akan retry:
    - Retry 1: setelah 1 menit
    - Retry 2: setelah 5 menit
    - Retry 3: setelah 30 menit
    - Retry 4: setelah 2 jam
    - Retry 5: setelah 24 jam

    Setelah 5 kali gagal, webhook akan di-disable.
    """)


def render_api_console():
    """Interactive API console"""
    st.markdown("### API Console")
    st.markdown("Test API endpoints langsung dari browser")

    user = get_current_user()

    if not user or user.role not in [UserRole.PARTNER, UserRole.ADMIN]:
        st.warning("API Console hanya tersedia untuk Partner. Silakan daftar sebagai partner.")
        return

    col1, col2 = st.columns([1, 2])

    with col1:
        method = st.selectbox("Method", ["GET", "POST", "PUT", "DELETE"])

        endpoint = st.selectbox("Endpoint", [
            "/api/v1/packages",
            "/api/v1/packages/{id}",
            "/api/v1/bookings",
            "/api/v1/bookings/{code}",
            "/api/v1/analytics/overview",
        ])

        if "{id}" in endpoint or "{code}" in endpoint:
            param_value = st.text_input("Path Parameter", placeholder="ID or Code")
            endpoint = endpoint.replace("{id}", param_value).replace("{code}", param_value)

    with col2:
        if method in ["POST", "PUT"]:
            request_body = st.text_area(
                "Request Body (JSON)",
                value='{\n  "name": "Test Package",\n  "price": 25000000\n}',
                height=150
            )
        else:
            request_body = None

    if st.button("Send Request", type="primary"):
        # Get API key
        api = get_partner_api()
        keys = api.get_partner_keys(user.id)

        if not keys:
            st.error("Anda belum memiliki API key. Generate terlebih dahulu.")
            return

        # Use first active key
        active_key = None
        for k in keys:
            if k.status.value == "active":
                # We need the full key, which we don't have stored
                # In real implementation, use actual API call
                st.info("Simulating API call...")
                break

        # Simulate response
        st.markdown('<h4 role="status" aria-live="polite">Response</h4>', unsafe_allow_html=True)

        sample_response = {
            "success": True,
            "data": {
                "id": 1,
                "name": "Sample Package",
                "price": 25000000,
                "duration_days": 9
            }
        }

        st.json(sample_response)

        st.markdown("""
        ```
        HTTP/1.1 200 OK
        Content-Type: application/json
        X-RateLimit-Remaining: 999
        ```
        """)


__all__ = ["render_api_docs_page"]
