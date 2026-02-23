"""
================================================================================
LABBAIK AI - Quote & Invoice Generator
================================================================================
Generate professional quotes and invoices with AI pricing suggestions.
================================================================================
"""

import streamlit as st
from datetime import datetime, date, timedelta
import logging
import html as html_module

from services.ai.helpers import ai_complete, add_xp_safe
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS

logger = logging.getLogger(__name__)


# =============================================================================
# PAGE-SPECIFIC CSS
# =============================================================================

QUOTES_CSS = """
/* Quote & Invoice page-specific styles */
.quote-header {
    background: linear-gradient(135deg, #1a5f2a 0%, #2d8a3e 100%);
    color: white;
    padding: 30px;
    border-radius: 15px;
    margin-bottom: 20px;
}

.quote-header h1 {
    margin: 0;
    color: white;
    text-align: center;
}

.quote-header p {
    margin: 0;
    opacity: 0.9;
    text-align: center;
}

.quote-header hr {
    border-color: rgba(255,255,255,0.3);
}

.quote-header .field {
    margin: 4px 0;
}

.quote-header .field strong {
    color: white;
}

.invoice-card {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 10px;
    border: 1px solid #dee2e6;
}

.invoice-card h2 {
    margin: 0;
    text-align: center;
}

.invoice-card .subtitle {
    margin: 0;
    color: #8e9fb3;
    text-align: center;
}

.invoice-card hr {
    border-color: #dee2e6;
}

.invoice-card .field {
    margin: 4px 0;
}

.quote-status-draft {
    display: inline-block;
    background: #4a3a1a;
    color: #fbbf24;
    padding: 0.15rem 0.6rem;
    border-radius: 10px;
    font-size: 0.75rem;
    font-weight: bold;
}

.quote-status-sent {
    display: inline-block;
    background: #1a2a4a;
    color: #60a5fa;
    padding: 0.15rem 0.6rem;
    border-radius: 10px;
    font-size: 0.75rem;
    font-weight: bold;
}

.quote-status-accepted {
    display: inline-block;
    background: #1a3a1a;
    color: #4ade80;
    padding: 0.15rem 0.6rem;
    border-radius: 10px;
    font-size: 0.75rem;
    font-weight: bold;
}

.ai-pricing-section {
    margin-top: 1rem;
}
"""


# =============================================================================
# HELPERS
# =============================================================================

def escape(text):
    """Escape HTML to prevent XSS."""
    if text is None:
        return ""
    return html_module.escape(str(text))


from ui.components.crm_helpers import format_rupiah, format_date


def _markdown_to_html_simple(text: str) -> str:
    """Simple markdown to HTML conversion for AI output."""
    import re

    lines = text.split("\n")
    html_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            html_lines.append("<br/>")
            continue
        line = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
        if line.startswith("- ") or line.startswith("* "):
            line = "&bull; " + line[2:]
        match = re.match(r"^(\d+)\.\s+", line)
        if match:
            num = match.group(1)
            rest = line[match.end():]
            line = "<strong>" + num + ".</strong> " + rest
        html_lines.append("<div style='margin-bottom:0.3rem;'>" + line + "</div>")
    return "\n".join(html_lines)


def init_session_state():
    """Initialize session state."""
    if "quote_view" not in st.session_state:
        st.session_state.quote_view = "list"
    if "quote_create_xp_awarded" not in st.session_state:
        st.session_state.quote_create_xp_awarded = False
    if "quote_ai_xp_awarded" not in st.session_state:
        st.session_state.quote_ai_xp_awarded = False


# =============================================================================
# QUOTE GENERATOR
# =============================================================================

def render_quote_generator():
    """Generate quote from package builder."""
    st.markdown("### Generate Quote Baru")

    # Load package config
    try:
        from utils.package_calculator import (
            get_config, get_hotels, get_airlines, get_origins,
            get_durations, get_room_types, get_meal_options,
            PackageScenario, calculate_package, format_currency
        )

        config = get_config()
    except Exception as e:
        logger.error(f"Failed to load package config: {e}")
        st.error("Gagal memuat konfigurasi paket")
        return

    with st.form("quote_form"):
        st.markdown("**Informasi Penerima**")
        col1, col2 = st.columns(2)

        with col1:
            recipient_name = st.text_input("Nama Penerima *", placeholder="Nama calon jamaah")
            recipient_phone = st.text_input("No. Telepon *", placeholder="08xxxxxxxxxx")

        with col2:
            recipient_email = st.text_input("Email", placeholder="email@example.com")
            valid_days = st.number_input("Berlaku (hari)", min_value=1, max_value=30, value=7)

        st.markdown("---")
        st.markdown("**Konfigurasi Paket**")

        # Duration
        col1, col2, col3 = st.columns(3)

        with col1:
            durations = get_durations()
            duration_options = {d["label"]: d for d in durations}
            selected_duration = st.selectbox("Durasi", options=list(duration_options.keys()))
            duration_data = duration_options[selected_duration]

        with col2:
            nights_makkah = st.number_input("Malam Makkah", min_value=1, max_value=14, value=duration_data.get("nights_makkah", 4))

        with col3:
            nights_madinah = st.number_input("Malam Madinah", min_value=1, max_value=14, value=duration_data.get("nights_madinah", 4))

        # Hotels
        col1, col2 = st.columns(2)

        with col1:
            hotels_makkah = get_hotels("makkah")
            hotel_makkah_options = {h["label"]: h for h in hotels_makkah}
            selected_hotel_makkah = st.selectbox("Hotel Makkah", options=list(hotel_makkah_options.keys()))
            hotel_makkah = hotel_makkah_options[selected_hotel_makkah]
            makkah_price = st.number_input("Harga/Malam Makkah", value=hotel_makkah["default_price"], step=100000)

        with col2:
            hotels_madinah = get_hotels("madinah")
            hotel_madinah_options = {h["label"]: h for h in hotels_madinah}
            selected_hotel_madinah = st.selectbox("Hotel Madinah", options=list(hotel_madinah_options.keys()))
            hotel_madinah = hotel_madinah_options[selected_hotel_madinah]
            madinah_price = st.number_input("Harga/Malam Madinah", value=hotel_madinah["default_price"], step=100000)

        # Flight
        col1, col2 = st.columns(2)

        with col1:
            airlines = get_airlines()
            airline_options = {f"{a['name']} ({a['code']})": a for a in airlines}
            selected_airline = st.selectbox("Maskapai", options=list(airline_options.keys()))
            airline = airline_options[selected_airline]

        with col2:
            origins = get_origins()
            origin_options = {o["name"]: o for o in origins}
            selected_origin = st.selectbox("Kota Keberangkatan", options=list(origin_options.keys()))
            origin = origin_options[selected_origin]

        # Room & Meal
        col1, col2 = st.columns(2)

        with col1:
            room_types = get_room_types()
            room_options = {r["label"]: r for r in room_types}
            selected_room = st.selectbox("Tipe Kamar", options=list(room_options.keys()))
            room = room_options[selected_room]

        with col2:
            meals = get_meal_options()
            meal_options = {m["label"]: m for m in meals}
            selected_meal = st.selectbox("Paket Makan", options=list(meal_options.keys()))
            meal = meal_options[selected_meal]

        # Margin
        margin_percentage = st.slider("Margin (%)", min_value=5, max_value=30, value=15)

        # Discount
        st.markdown("---")
        st.markdown("**Diskon**")
        col1, col2 = st.columns(2)

        with col1:
            discount_type = st.selectbox("Tipe Diskon", options=["Tidak ada", "Nominal", "Persentase"])

        with col2:
            if discount_type == "Nominal":
                discount_value = st.number_input("Jumlah Diskon", min_value=0, value=0, step=100000)
            elif discount_type == "Persentase":
                discount_value = st.number_input("Persentase Diskon", min_value=0, max_value=50, value=0)
            else:
                discount_value = 0

        # Notes
        notes = st.text_area("Catatan untuk Quote", placeholder="Catatan tambahan...")

        submitted = st.form_submit_button("Generate Quote", type="primary", use_container_width=True)

        if submitted:
            if not recipient_name or not recipient_phone:
                st.error("Nama dan nomor telepon penerima wajib diisi!")
            else:
                # Calculate package
                scenario = PackageScenario(
                    name=f"Quote untuk {recipient_name}",
                    duration_days=duration_data.get("days", 9),
                    nights_makkah=nights_makkah,
                    nights_madinah=nights_madinah,
                    hotel_makkah_category=hotel_makkah["category"],
                    hotel_makkah_price=makkah_price,
                    hotel_madinah_category=hotel_madinah["category"],
                    hotel_madinah_price=madinah_price,
                    airline_code=airline["code"],
                    flight_price=airline["price_economy"],
                    origin_code=origin["code"],
                    origin_surcharge=origin["surcharge"],
                    room_type=room["type"],
                    room_occupancy=room["occupancy"],
                    room_multiplier=room["price_multiplier"],
                    meal_type=meal["type"],
                    meal_price_per_day=meal["price_per_day"],
                    margin_percentage=margin_percentage
                )

                breakdown = calculate_package(scenario)

                # Apply discount
                discount_amount = 0
                if discount_type == "Nominal":
                    discount_amount = discount_value
                elif discount_type == "Persentase":
                    discount_amount = int(breakdown.selling_price_per_person * discount_value / 100)

                final_price = breakdown.selling_price_per_person - discount_amount

                # Store in session for preview
                st.session_state.quote_preview = {
                    "recipient_name": recipient_name,
                    "recipient_phone": recipient_phone,
                    "recipient_email": recipient_email,
                    "package_name": f"Paket Umrah {duration_data['label']}",
                    "duration": duration_data['label'],
                    "hotel_makkah": selected_hotel_makkah,
                    "hotel_madinah": selected_hotel_madinah,
                    "airline": selected_airline,
                    "origin": selected_origin,
                    "room": selected_room,
                    "meal": selected_meal,
                    "base_price": breakdown.selling_price_per_person,
                    "discount": discount_amount,
                    "final_price": final_price,
                    "valid_until": (date.today() + timedelta(days=valid_days)).isoformat(),
                    "notes": notes,
                    "breakdown": breakdown,
                    "margin_percentage": margin_percentage,
                    "nights_makkah": nights_makkah,
                    "nights_madinah": nights_madinah,
                }

                # Gamification: +25 XP for creating a quote (first time)
                if not st.session_state.get("quote_create_xp_awarded", False):
                    st.session_state.quote_create_xp_awarded = True
                    add_xp_safe(25, "Membuat quote umrah pertama")

                st.session_state.quote_view = "preview"
                st.rerun()


# =============================================================================
# QUOTE PREVIEW
# =============================================================================

def render_quote_preview():
    """Render quote preview."""
    if "quote_preview" not in st.session_state:
        st.session_state.quote_view = "create"
        st.rerun()
        return

    quote = st.session_state.quote_preview

    st.markdown("### Preview Quote")

    # Build the quote header card HTML
    safe_name = escape(quote['recipient_name'])
    safe_phone = escape(quote['recipient_phone'])
    safe_valid = escape(quote['valid_until'])

    header_html = (
        '<div class="quote-header">'
        '<h1>LABBAIK</h1>'
        '<p>Penawaran Paket Umrah</p>'
        '<hr>'
        '<p class="field"><strong>Kepada:</strong> ' + safe_name + '</p>'
        '<p class="field"><strong>Telepon:</strong> ' + safe_phone + '</p>'
        '<p class="field"><strong>Berlaku sampai:</strong> ' + safe_valid + '</p>'
        '</div>'
    )
    st.markdown(header_html, unsafe_allow_html=True)

    safe_pkg = escape(quote['package_name'])
    st.markdown(f"### {safe_pkg}")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Detail Paket:**")
        st.markdown(f"- Durasi: {quote['duration']}")
        st.markdown(f"- Hotel Makkah: {quote['hotel_makkah']}")
        st.markdown(f"- Hotel Madinah: {quote['hotel_madinah']}")
        st.markdown(f"- Maskapai: {quote['airline']}")

    with col2:
        st.markdown(f"- Keberangkatan: {quote['origin']}")
        st.markdown(f"- Tipe Kamar: {quote['room']}")
        st.markdown(f"- Makan: {quote['meal']}")

    st.markdown("---")
    st.markdown("### Harga")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Harga Normal", format_rupiah(quote['base_price']))

    with col2:
        if quote['discount'] > 0:
            st.metric("Diskon", f"-{format_rupiah(quote['discount'])}")
        else:
            st.metric("Diskon", "-")

    with col3:
        st.metric("Harga Final", format_rupiah(quote['final_price']))

    if quote.get('notes'):
        st.markdown("---")
        st.markdown("**Catatan:**")
        st.write(quote['notes'])

    # AI Pricing Suggestion Section
    st.markdown("---")
    _render_ai_pricing_suggestion(quote)

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Edit", use_container_width=True):
            st.session_state.quote_view = "create"
            st.rerun()

    with col2:
        if st.button("Simpan", type="primary", use_container_width=True):
            # Save quote to database
            try:
                from services.crm import CRMRepository, Quote
                import json

                repo = CRMRepository()

                quote_obj = Quote(
                    package_config=quote,
                    base_price=quote['base_price'],
                    discount_amount=quote['discount'],
                    final_price=quote['final_price'],
                    valid_until=date.fromisoformat(quote['valid_until']),
                    status="draft"
                )

                quote_id = repo.create_quote(quote_obj)
                if quote_id:
                    st.success("Quote berhasil disimpan!")
                    st.session_state.quote_view = "list"
                    del st.session_state.quote_preview
                    st.rerun()
                else:
                    st.error("Gagal menyimpan quote")

            except Exception as e:
                logger.error(f"Failed to save quote: {e}")
                st.error(f"Gagal menyimpan: {str(e)}")

    with col3:
        wa_number = quote['recipient_phone'].replace("+", "").replace(" ", "")
        if wa_number.startswith("0"):
            wa_number = "62" + wa_number[1:]

        message = (
            "Assalamualaikum " + quote['recipient_name'] + ",\n\n"
            "Berikut penawaran paket umrah dari Labbaik:\n\n"
            "*" + quote['package_name'] + "*\n"
            "- Hotel Makkah: " + quote['hotel_makkah'] + "\n"
            "- Hotel Madinah: " + quote['hotel_madinah'] + "\n"
            "- Maskapai: " + quote['airline'] + "\n\n"
            "*Harga: " + format_rupiah(quote['final_price']) + "*\n\n"
            "Berlaku sampai: " + quote['valid_until'] + "\n\n"
            "Hubungi kami untuk informasi lebih lanjut!"
        )

        import urllib.parse
        encoded_message = urllib.parse.quote(message)
        st.link_button("Kirim WA", f"https://wa.me/{wa_number}?text={encoded_message}", use_container_width=True)


# =============================================================================
# AI PRICING SUGGESTION
# =============================================================================

def _render_ai_pricing_suggestion(quote):
    """Render AI-powered pricing analysis and suggestions."""
    st.markdown('<div class="ai-pricing-section">', unsafe_allow_html=True)
    st.markdown("### Saran Harga AI")

    if st.button("Analisis Harga dengan AI", use_container_width=True):
        with st.spinner("AI sedang menganalisis harga paket..."):
            base_price_str = format_rupiah(quote['base_price'])
            final_price_str = format_rupiah(quote['final_price'])
            discount_str = format_rupiah(quote['discount'])
            margin_pct = quote.get('margin_percentage', 15)
            nights_m = quote.get('nights_makkah', 4)
            nights_d = quote.get('nights_madinah', 4)

            prompt_text = (
                "Analisis penawaran paket umrah berikut:\n\n"
                "Paket: " + str(quote['package_name']) + "\n"
                "Durasi: " + str(quote['duration']) + "\n"
                "Hotel Makkah: " + str(quote['hotel_makkah']) + " (" + str(nights_m) + " malam)\n"
                "Hotel Madinah: " + str(quote['hotel_madinah']) + " (" + str(nights_d) + " malam)\n"
                "Maskapai: " + str(quote['airline']) + "\n"
                "Keberangkatan: " + str(quote['origin']) + "\n"
                "Tipe Kamar: " + str(quote['room']) + "\n"
                "Paket Makan: " + str(quote['meal']) + "\n"
                "Margin: " + str(margin_pct) + "%\n"
                "Harga Dasar: " + base_price_str + "\n"
                "Diskon: " + discount_str + "\n"
                "Harga Final: " + final_price_str + "\n\n"
                "Berikan analisis singkat:\n"
                "1. Apakah harga ini kompetitif di pasar umrah Indonesia?\n"
                "2. Saran margin yang optimal\n"
                "3. Tips strategi diskon untuk meningkatkan closing rate\n"
                "4. Rekomendasi paket add-on yang bisa ditawarkan\n"
                "Jawab dalam bahasa Indonesia, singkat dan praktis."
            )

            system_prompt = (
                "Kamu adalah konsultan pricing travel umrah berpengalaman di Indonesia. "
                "Berikan analisis harga yang praktis dan actionable untuk agen travel. "
                "Fokus pada strategi pricing yang kompetitif di pasar Indonesia. "
                "Gunakan bahasa Indonesia yang profesional."
            )

            response = ai_complete(prompt_text, system_prompt=system_prompt, max_tokens=1024)

            if response:
                # Gamification: +15 XP for AI analysis (first time)
                if not st.session_state.get("quote_ai_xp_awarded", False):
                    st.session_state.quote_ai_xp_awarded = True
                    add_xp_safe(15, "Analisis harga AI untuk quote")

                escaped = response.replace("<", "&lt;").replace(">", "&gt;")
                ai_html = _markdown_to_html_simple(escaped)
                card_html = (
                    '<div class="ai-card" role="status" aria-live="polite">'
                    '<h4>Analisis Harga AI</h4>'
                    '<p>' + ai_html + '</p>'
                    '</div>'
                )
                st.markdown(card_html, unsafe_allow_html=True)
            else:
                _render_fallback_pricing_tips(quote)

    st.markdown('</div>', unsafe_allow_html=True)


def _render_fallback_pricing_tips(quote):
    """Render fallback pricing tips when AI is unavailable."""
    margin_pct = quote.get('margin_percentage', 15)
    if margin_pct < 10:
        margin_tip = "Margin Anda di bawah 10%. Pertimbangkan menaikkan margin untuk menutupi biaya operasional."
    elif margin_pct > 25:
        margin_tip = "Margin di atas 25% mungkin kurang kompetitif. Pertimbangkan menurunkan sedikit untuk meningkatkan closing rate."
    else:
        margin_tip = "Margin " + str(margin_pct) + "% berada di kisaran standar industri travel umrah."

    has_discount = quote.get('discount', 0) > 0
    if has_discount:
        discount_tip = "Diskon yang diberikan dapat meningkatkan daya tarik penawaran."
    else:
        discount_tip = "Pertimbangkan memberikan diskon early bird atau grup untuk meningkatkan konversi."

    fallback_html = (
        '<div class="ai-card" role="status" aria-live="polite">'
        '<h4>Tips Pricing</h4>'
        '<p>'
        '<div style="margin-bottom:0.3rem;"><strong>Margin:</strong> ' + escape(margin_tip) + '</div>'
        '<div style="margin-bottom:0.3rem;"><strong>Diskon:</strong> ' + escape(discount_tip) + '</div>'
        '<div style="margin-bottom:0.3rem;"><strong>Tip:</strong> '
        'Tawarkan paket add-on seperti city tour, laundry, atau SIM card untuk meningkatkan nilai transaksi.</div>'
        '</p>'
        '</div>'
    )
    st.markdown(fallback_html, unsafe_allow_html=True)


# =============================================================================
# QUOTE LIST
# =============================================================================

def render_quote_list():
    """Render saved quotes list."""
    st.markdown("### Daftar Quote")

    try:
        from services.crm import CRMRepository
        repo = CRMRepository()

        # For now, show placeholder
        st.info("Belum ada quote tersimpan. Buat quote baru untuk memulai.")

    except Exception as e:
        logger.error(f"Failed to load quotes: {e}")
        st.info("Tidak dapat memuat daftar quote")


# =============================================================================
# INVOICE GENERATOR
# =============================================================================

def render_invoice_generator():
    """Generate invoice from booking."""
    st.markdown("### Generate Invoice")

    st.info("Pilih booking untuk generate invoice")

    try:
        from services.crm import CRMRepository
        repo = CRMRepository()

        bookings = repo.get_bookings(limit=20)

        if bookings:
            booking_options = {f"{b.booking_code} - {b.package_name}": b for b in bookings}
            selected = st.selectbox("Pilih Booking", options=list(booking_options.keys()))
            booking = booking_options[selected]

            st.markdown("---")
            st.markdown(f"### Invoice untuk {booking.booking_code}")

            col1, col2 = st.columns(2)

            with col1:
                invoice_type = st.selectbox(
                    "Tipe Invoice",
                    options=["dp", "installment", "final", "full"],
                    format_func=lambda x: {
                        "dp": "DP (Uang Muka)",
                        "installment": "Cicilan",
                        "final": "Pelunasan",
                        "full": "Full Payment"
                    }.get(x, x)
                )

            with col2:
                if invoice_type == "dp":
                    amount = int(booking.total_price * 0.3)
                elif invoice_type == "full":
                    amount = booking.total_price
                else:
                    amount = booking.amount_remaining or 0

                amount = st.number_input("Jumlah", value=amount, step=100000)

            due_date = st.date_input("Jatuh Tempo", value=date.today() + timedelta(days=7))

            if st.button("Generate Invoice", type="primary"):
                from services.crm import Invoice

                invoice = Invoice(
                    booking_id=booking.id,
                    invoice_type=invoice_type,
                    subtotal=amount,
                    total=amount,
                    due_date=due_date,
                    status="unpaid"
                )

                invoice_id = repo.create_invoice(invoice)
                if invoice_id:
                    st.success("Invoice berhasil dibuat!")

                    # Show invoice preview
                    st.markdown("---")

                    invoice_number = escape(str(repo.generate_invoice_number()))
                    booking_code = escape(str(booking.booking_code))
                    package_name = escape(str(booking.package_name))
                    total_str = escape(format_rupiah(amount))
                    due_str = escape(format_date(due_date))

                    invoice_html = (
                        '<div class="invoice-card">'
                        '<h2>INVOICE</h2>'
                        '<p class="subtitle">LABBAIK TRAVEL</p>'
                        '<hr>'
                        '<p class="field"><strong>No. Invoice:</strong> ' + invoice_number + '</p>'
                        '<p class="field"><strong>Booking:</strong> ' + booking_code + '</p>'
                        '<p class="field"><strong>Paket:</strong> ' + package_name + '</p>'
                        '<hr>'
                        '<p class="field"><strong>Total:</strong> ' + total_str + '</p>'
                        '<p class="field"><strong>Jatuh Tempo:</strong> ' + due_str + '</p>'
                        '</div>'
                    )
                    st.markdown(invoice_html, unsafe_allow_html=True)
                else:
                    st.error("Gagal membuat invoice")
        else:
            st.info("Belum ada booking. Buat booking terlebih dahulu.")

    except Exception as e:
        logger.error(f"Failed to generate invoice: {e}")
        st.error("Gagal memuat data booking")


# =============================================================================
# MAIN PAGE ENTRY POINT
# =============================================================================

def render_crm_quotes_page():
    """Main quotes page."""
    try:
        from services.analytics import track_page
        track_page("crm_quotes")
    except Exception:
        pass

    init_session_state()

    # Inject shared + page-specific CSS
    inject_css(HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS, QUOTES_CSS)

    st.markdown("# Quote & Invoice")

    tab1, tab2, tab3 = st.tabs(["Buat Quote", "Daftar Quote", "Invoice"])

    with tab1:
        if st.session_state.quote_view == "preview":
            render_quote_preview()
        else:
            render_quote_generator()

    with tab2:
        render_quote_list()

    with tab3:
        render_invoice_generator()


__all__ = ["render_crm_quotes_page"]
