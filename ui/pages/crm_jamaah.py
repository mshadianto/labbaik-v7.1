"""
LABBAIK AI - Jamaah Database & Document Checklist
===================================================
UI for managing jamaah database and documents.
"""

import streamlit as st
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

from services.ai.helpers import ai_complete, add_xp_safe
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS, AI_CARD_CSS

from ui.components.crm_helpers import format_date


def init_session_state():
    """Initialize session state."""
    if "jamaah_view" not in st.session_state:
        st.session_state.jamaah_view = "list"
    if "selected_jamaah" not in st.session_state:
        st.session_state.selected_jamaah = None


def render_jamaah_stats():
    """Render jamaah statistics."""
    try:
        from services.crm import CRMRepository
        repo = CRMRepository()
        stats = repo.get_crm_stats()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Jamaah", stats.total_jamaah)
        with col2:
            # Count with complete docs
            st.metric("Dokumen Lengkap", "-")
        with col3:
            st.metric("Repeat Customer", "-")
        with col4:
            st.metric("Referral", "-")

    except Exception as e:
        logger.error(f"Failed to load stats: {e}")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Jamaah", 0)
        with col2:
            st.metric("Dokumen Lengkap", 0)
        with col3:
            st.metric("Repeat Customer", 0)
        with col4:
            st.metric("Referral", 0)


def render_jamaah_list():
    """Render jamaah list."""
    search = st.text_input("Cari jamaah", placeholder="Nama, telepon, atau paspor...")

    try:
        from services.crm import CRMRepository
        repo = CRMRepository()

        jamaah_list = repo.get_jamaah_list(search=search if search else None, limit=50)

        if jamaah_list:
            for jamaah in jamaah_list:
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

                    with col1:
                        st.markdown(f"**{jamaah.full_name}**")
                        st.caption(f"📞 {jamaah.phone}")

                    with col2:
                        st.caption(f"Paspor: {jamaah.passport_number or '-'}")
                        if jamaah.passport_expiry:
                            days_left = (jamaah.passport_expiry - date.today()).days
                            if days_left < 240:  # Less than 8 months
                                st.caption(f"⚠️ Expired: {format_date(jamaah.passport_expiry)}")
                            else:
                                st.caption(f"Exp: {format_date(jamaah.passport_expiry)}")

                    with col3:
                        st.caption(f"Umrah: {jamaah.umrah_count}x")
                        st.caption(jamaah.city or "-")

                    with col4:
                        if st.button("📝", key=f"jamaah_{jamaah.id}", help="Detail"):
                            st.session_state.selected_jamaah = jamaah.id
                            st.session_state.jamaah_view = "detail"
                            st.rerun()

                    st.divider()
        else:
            st.info("Belum ada data jamaah. Tambahkan jamaah baru atau buat booking.")

    except Exception as e:
        logger.error(f"Failed to load jamaah: {e}")
        st.info("Belum ada data jamaah atau database belum terhubung.")


def render_add_jamaah_form():
    """Render add jamaah form."""
    st.markdown("### Tambah Jamaah Baru")

    with st.form("add_jamaah_form"):
        st.markdown("**Data Pribadi**")
        col1, col2 = st.columns(2)

        with col1:
            full_name = st.text_input("Nama Lengkap *", placeholder="Sesuai paspor")
            nik = st.text_input("NIK", placeholder="16 digit")
            birth_place = st.text_input("Tempat Lahir")
            birth_date = st.date_input("Tanggal Lahir", value=None)

        with col2:
            gender = st.selectbox("Jenis Kelamin", options=["", "Laki-laki", "Perempuan"])
            blood_type = st.selectbox("Golongan Darah", options=["", "A", "B", "AB", "O"])
            passport_number = st.text_input("Nomor Paspor")
            passport_expiry = st.date_input("Berlaku Sampai", value=None)

        st.markdown("---")
        st.markdown("**Kontak**")
        col1, col2 = st.columns(2)

        with col1:
            phone = st.text_input("No. Telepon *", placeholder="08xxxxxxxxxx")
            whatsapp = st.text_input("WhatsApp", placeholder="Kosongkan jika sama")
            email = st.text_input("Email")

        with col2:
            address = st.text_area("Alamat", placeholder="Alamat lengkap")
            city = st.text_input("Kota")
            province = st.text_input("Provinsi")

        st.markdown("---")
        st.markdown("**Kontak Darurat**")
        col1, col2, col3 = st.columns(3)

        with col1:
            emergency_name = st.text_input("Nama Kontak Darurat")
        with col2:
            emergency_phone = st.text_input("Telepon Darurat")
        with col3:
            emergency_relation = st.selectbox(
                "Hubungan",
                options=["", "Suami", "Istri", "Anak", "Orang Tua", "Saudara", "Lainnya"]
            )

        st.markdown("---")
        st.markdown("**Informasi Kesehatan**")
        health_notes = st.text_area("Riwayat Kesehatan", placeholder="Alergi, penyakit kronis, dll")
        special_needs = st.text_area("Kebutuhan Khusus", placeholder="Kursi roda, diet khusus, dll")

        submitted = st.form_submit_button("Simpan Jamaah", type="primary", use_container_width=True)

        if submitted:
            if not full_name or not phone:
                st.error("Nama dan nomor telepon wajib diisi!")
            else:
                try:
                    from services.crm import CRMRepository, Jamaah
                    from services.crm.security import (
                        validate_phone, validate_email, validate_nik, validate_passport,
                        check_rate_limit, audit_log, AuditAction
                    )

                    # Rate limiting: max 10 jamaah per minute per session
                    session_key = st.session_state.get("session_id", "anonymous")
                    if not check_rate_limit(f"create_jamaah:{session_key}", max_requests=10, window_seconds=60):
                        st.error("Terlalu banyak permintaan. Silakan tunggu sebentar.")
                        st.stop()

                    repo = CRMRepository()

                    # Input validation
                    validated_phone = validate_phone(phone)
                    if not validated_phone:
                        st.error("Format nomor telepon tidak valid! Gunakan format 08xx atau +628xx")
                        st.stop()

                    validated_email = None
                    if email:
                        validated_email = validate_email(email)
                        if not validated_email:
                            st.error("Format email tidak valid!")
                            st.stop()

                    validated_nik = None
                    if nik:
                        validated_nik = validate_nik(nik)
                        if not validated_nik:
                            st.error("NIK harus 16 digit angka!")
                            st.stop()

                    validated_passport = None
                    if passport_number:
                        validated_passport = validate_passport(passport_number)
                        if not validated_passport:
                            st.error("Format nomor paspor tidak valid!")
                            st.stop()

                    jamaah = Jamaah(
                        full_name=full_name.strip(),
                        nik=validated_nik,
                        passport_number=validated_passport,
                        passport_expiry=passport_expiry,
                        phone=validated_phone,
                        whatsapp=whatsapp.strip() if whatsapp else validated_phone,
                        email=validated_email,
                        address=address if address else None,
                        city=city if city else None,
                        province=province if province else None,
                        birth_date=birth_date,
                        birth_place=birth_place if birth_place else None,
                        gender=gender if gender else None,
                        blood_type=blood_type if blood_type else None,
                        emergency_name=emergency_name if emergency_name else None,
                        emergency_phone=emergency_phone if emergency_phone else None,
                        emergency_relation=emergency_relation if emergency_relation else None,
                        health_notes=health_notes if health_notes else None,
                        special_needs=special_needs if special_needs else None
                    )

                    jamaah_id = repo.create_jamaah(jamaah)
                    if jamaah_id:
                        # Audit log
                        user = st.session_state.get("user")
                        audit_log(
                            action=AuditAction.CREATE,
                            entity_type="jamaah",
                            entity_id=jamaah_id,
                            user_id=getattr(user, "id", None),
                            user_email=getattr(user, "email", None),
                            details={"full_name": full_name.strip(), "phone": validated_phone}
                        )
                        st.success("Jamaah berhasil ditambahkan!")
                        add_xp_safe(15, "Menambahkan data jamaah baru")
                        st.session_state.jamaah_view = "list"
                        st.rerun()
                    else:
                        st.error("Gagal menyimpan jamaah")

                except Exception as e:
                    logger.error(f"Failed to create jamaah: {e}")
                    st.error(f"Gagal menyimpan: {str(e)}")


def render_jamaah_detail(jamaah_id: str):
    """Render jamaah detail and document checklist."""
    try:
        from services.crm import CRMRepository
        repo = CRMRepository()
        jamaah = repo.get_jamaah(jamaah_id)

        if not jamaah:
            st.error("Jamaah tidak ditemukan")
            return

        # Header
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"## 👤 {jamaah.full_name}")
            st.caption(f"📞 {jamaah.phone} | 📧 {jamaah.email or '-'}")

        with col2:
            if st.button("← Kembali"):
                st.session_state.jamaah_view = "list"
                st.session_state.selected_jamaah = None
                st.rerun()

        st.markdown("---")

        # Tabs
        tab1, tab2, tab3 = st.tabs(["📋 Data Pribadi", "📄 Dokumen", "📅 Riwayat Booking"])

        with tab1:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Data Identitas**")
                st.markdown(f"- NIK: {jamaah.nik or '-'}")
                st.markdown(f"- Paspor: {jamaah.passport_number or '-'}")
                if jamaah.passport_expiry:
                    days_left = (jamaah.passport_expiry - date.today()).days
                    if days_left < 240:
                        st.markdown(f"- Berlaku: ⚠️ {format_date(jamaah.passport_expiry)} ({days_left} hari)")
                    else:
                        st.markdown(f"- Berlaku: {format_date(jamaah.passport_expiry)}")

                st.markdown("**Data Lahir**")
                st.markdown(f"- Tempat: {jamaah.birth_place or '-'}")
                st.markdown(f"- Tanggal: {format_date(jamaah.birth_date)}")
                st.markdown(f"- Gender: {jamaah.gender or '-'}")
                st.markdown(f"- Gol. Darah: {jamaah.blood_type or '-'}")

            with col2:
                st.markdown("**Alamat**")
                st.markdown(jamaah.address or "-")
                st.markdown(f"{jamaah.city or ''}, {jamaah.province or ''}")

                st.markdown("**Kontak Darurat**")
                st.markdown(f"- Nama: {jamaah.emergency_name or '-'}")
                st.markdown(f"- Telepon: {jamaah.emergency_phone or '-'}")
                st.markdown(f"- Hubungan: {jamaah.emergency_relation or '-'}")

            if jamaah.health_notes or jamaah.special_needs:
                st.markdown("---")
                st.markdown("**Catatan Kesehatan**")
                if jamaah.health_notes:
                    st.write(jamaah.health_notes)
                if jamaah.special_needs:
                    st.markdown("**Kebutuhan Khusus:**")
                    st.write(jamaah.special_needs)

            st.markdown("---")
            st.markdown("**Riwayat Umrah**")
            st.markdown(f"- Total: {jamaah.umrah_count}x")
            st.markdown(f"- Terakhir: {format_date(jamaah.last_umrah_date)}")

        with tab2:
            render_document_checklist(jamaah_id)

        with tab3:
            st.markdown("### Riwayat Booking")
            st.info("Belum ada riwayat booking")

    except Exception as e:
        logger.error(f"Failed to load jamaah detail: {e}")
        st.error("Gagal memuat detail jamaah")


def render_document_checklist(jamaah_id: str):
    """Render document checklist for jamaah."""
    st.markdown("### Checklist Dokumen")

    try:
        from services.crm import CRMRepository
        from services.crm.config import get_required_documents, get_optional_documents

        repo = CRMRepository()

        required_docs = get_required_documents()
        optional_docs = get_optional_documents()

        # Get existing documents
        existing = repo.get_documents_for_jamaah(jamaah_id)
        existing_map = {d.doc_type: d for d in existing}

        st.markdown("**Dokumen Wajib**")
        for doc in required_docs:
            doc_type = doc["code"]
            existing_doc = existing_map.get(doc_type)

            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                if existing_doc and existing_doc.status == "verified":
                    st.markdown(f"✅ **{doc['label']}**")
                elif existing_doc and existing_doc.status == "uploaded":
                    st.markdown(f"📤 **{doc['label']}** (menunggu verifikasi)")
                elif existing_doc and existing_doc.status == "rejected":
                    st.markdown(f"❌ **{doc['label']}** (ditolak)")
                else:
                    st.markdown(f"⬜ **{doc['label']}**")
                st.caption(doc.get("description", ""))

            with col2:
                status = existing_doc.status if existing_doc else "pending"
                status_label = {
                    "pending": "Belum",
                    "uploaded": "Uploaded",
                    "verified": "Verified",
                    "rejected": "Ditolak"
                }.get(status, status)
                st.caption(status_label)

            with col3:
                if not existing_doc or existing_doc.status in ["pending", "rejected"]:
                    if st.button("Upload", key=f"upload_{doc_type}"):
                        st.session_state[f"upload_doc_{doc_type}"] = True
                        st.rerun()

            st.divider()

        st.markdown("**Dokumen Tambahan**")
        for doc in optional_docs:
            doc_type = doc["code"]
            existing_doc = existing_map.get(doc_type)

            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                if existing_doc and existing_doc.status == "verified":
                    st.markdown(f"✅ {doc['label']}")
                elif existing_doc:
                    st.markdown(f"📤 {doc['label']}")
                else:
                    st.markdown(f"⬜ {doc['label']}")
                st.caption(doc.get("description", ""))

            with col2:
                if existing_doc:
                    st.caption(existing_doc.status)

            with col3:
                if not existing_doc:
                    if st.button("Upload", key=f"upload_{doc_type}"):
                        st.info("Fitur upload dokumen akan segera tersedia")

            st.divider()

        # Summary
        verified_count = sum(1 for d in existing if d.status == "verified")
        total_required = len(required_docs)

        if verified_count == total_required:
            st.success(f"Semua dokumen wajib sudah terverifikasi ({verified_count}/{total_required})")
        else:
            st.warning(f"Dokumen terverifikasi: {verified_count}/{total_required}")

    except Exception as e:
        logger.error(f"Failed to load document checklist: {e}")
        st.info("Tidak dapat memuat checklist dokumen")


def render_crm_jamaah_page():
    """Main jamaah page."""
    try:
        from services.analytics import track_page
        track_page("crm_jamaah")
    except Exception:
        pass

    init_session_state()

    inject_css(HERO_CSS, CARD_CSS, AI_CARD_CSS)

    # Hero
    st.markdown("""
        <div class="page-hero">
            <h1>👥 Database Jamaah</h1>
            <div class="subtitle">Kelola data jamaah dan dokumen perjalanan</div>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        pass
    with col2:
        if st.button("➕ Tambah Jamaah", type="primary", use_container_width=True):
            st.session_state.jamaah_view = "add"
            st.rerun()

    st.markdown("---")

    # Stats
    render_jamaah_stats()

    st.markdown("---")

    # View
    if st.session_state.jamaah_view == "add":
        render_add_jamaah_form()
    elif st.session_state.jamaah_view == "detail" and st.session_state.selected_jamaah:
        render_jamaah_detail(st.session_state.selected_jamaah)
    else:
        render_jamaah_list()

        # AI Insights
        st.markdown("---")
        if st.button("🤖 Analisis Data Jamaah", use_container_width=True):
            with st.spinner("Menganalisis data jamaah..."):
                insight = ai_complete(
                    "Berikan 3 tips singkat untuk mengelola database jamaah umrah secara efektif. "
                    "Termasuk tips tentang kelengkapan dokumen, follow-up, dan retensi jamaah. "
                    "Format: nomor dan tips. Bahasa Indonesia.",
                    system_prompt="Kamu adalah CRM expert untuk travel umrah.",
                    max_tokens=400,
                )
                if insight:
                    escaped = insight.replace("<", "&lt;").replace(">", "&gt;")
                    st.markdown(f"""
                        <div class="ai-card" role="status" aria-live="polite">
                            <h4>Tips Manajemen Jamaah</h4>
                            <p>{escaped}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    if not st.session_state.get("crm_jamaah_ai_xp"):
                        st.session_state.crm_jamaah_ai_xp = True
                        add_xp_safe(10, "Menggunakan AI analisis jamaah")
                else:
                    st.info("AI tidak tersedia saat ini")


__all__ = ["render_crm_jamaah_page"]
