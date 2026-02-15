"""
LABBAIK AI - 3D Manasik Simulator
=================================
Interactive 3D visualization of Umrah rituals:
- 3D Ka'bah view with rotation
- Step-by-step ritual guide
- Interactive hotspots
- Audio doa playback
"""

import streamlit as st
from typing import Dict, List, Any
from enum import Enum
from dataclasses import dataclass

from services.ai.helpers import ai_complete, add_xp_safe
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS, AI_CARD_CSS

# =============================================================================
# RITUAL DATA
# =============================================================================

class RitualStep(str, Enum):
    MIQAT = "miqat"
    IHRAM = "ihram"
    TAWAF = "tawaf"
    SHOLAT_TAWAF = "sholat_tawaf"
    SAI = "sai"
    TAHALLUL = "tahallul"


@dataclass
class RitualInfo:
    """Information about a ritual step."""
    id: RitualStep
    name: str
    arabic: str
    icon: str
    location: str
    description: str
    steps: List[str]
    dua: str
    dua_translation: str
    tips: List[str]
    common_mistakes: List[str]


RITUALS_DATA = {
    RitualStep.MIQAT: RitualInfo(
        id=RitualStep.MIQAT,
        name="Miqat",
        arabic="ميقات",
        icon="📍",
        location="Sebelum memasuki Makkah",
        description="Miqat adalah batas tempat dimana jamaah harus sudah berihram sebelum memasuki Makkah.",
        steps=[
            "Mandi sunnah (ghusl)",
            "Memakai pakaian ihram",
            "Sholat sunnah 2 rakaat",
            "Niat ihram umrah",
            "Membaca talbiyah"
        ],
        dua="لَبَّيْكَ اللَّهُمَّ عُمْرَةً",
        dua_translation="Labbaika Allahumma 'Umratan - Ya Allah, aku memenuhi panggilan-Mu untuk umrah",
        tips=[
            "Pastikan sudah mandi dan bersih",
            "Potong kuku dan rapikan badan",
            "Siapkan mental untuk ibadah"
        ],
        common_mistakes=[
            "Lupa niat sebelum melewati miqat",
            "Tidak memakai ihram dengan benar"
        ]
    ),
    
    RitualStep.IHRAM: RitualInfo(
        id=RitualStep.IHRAM,
        name="Ihram",
        arabic="إحرام",
        icon="⚪",
        location="Dimulai dari Miqat",
        description="Ihram adalah niat memasuki ibadah umrah dengan memakai pakaian ihram dan menjauhi larangan-larangannya.",
        steps=[
            "Niat ihram dalam hati",
            "Pria: 2 lembar kain putih tidak berjahit",
            "Wanita: Pakaian menutup aurat, wajah & telapak tangan terbuka",
            "Membaca talbiyah dengan lantang",
            "Menjaga larangan ihram"
        ],
        dua="لَبَّيْكَ اللَّهُمَّ لَبَّيْكَ، لَبَّيْكَ لَا شَرِيكَ لَكَ لَبَّيْكَ، إِنَّ الْحَمْدَ وَالنِّعْمَةَ لَكَ وَالْمُلْكَ، لَا شَرِيكَ لَكَ",
        dua_translation="Labbaik Allahumma Labbaik... - Aku memenuhi panggilan-Mu ya Allah...",
        tips=[
            "Talbiyah dibaca sepanjang perjalanan",
            "Jaga dari larangan ihram (potong kuku, pakai wangi, dll)",
            "Pria tidak boleh tutup kepala"
        ],
        common_mistakes=[
            "Memakai pakaian berjahit (pria)",
            "Menggunakan wewangian setelah ihram",
            "Memotong rambut/kuku"
        ]
    ),
    
    RitualStep.TAWAF: RitualInfo(
        id=RitualStep.TAWAF,
        name="Tawaf",
        arabic="طواف",
        icon="🔄",
        location="Masjidil Haram - Ka'bah",
        description="Tawaf adalah mengelilingi Ka'bah sebanyak 7 kali putaran, dimulai dan diakhiri di Hajar Aswad.",
        steps=[
            "Masuk Masjidil Haram dengan kaki kanan",
            "Baca doa masuk masjid",
            "Menuju Hajar Aswad (pojok tenggara Ka'bah)",
            "Niat tawaf sambil menghadap Hajar Aswad",
            "Istilam (isyarat ke Hajar Aswad) + Takbir",
            "Mulai tawaf berlawanan arah jarum jam",
            "Putaran 1-3: Idhtiba (pria) + Raml (jalan cepat)",
            "Putaran 4-7: Jalan biasa",
            "Setiap melewati Hajar Aswad: Istilam + Takbir",
            "Selesai 7 putaran di Hajar Aswad"
        ],
        dua="رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الْآخِرَةِ حَسَنَةً وَقِنَا عَذَابَ النَّارِ",
        dua_translation="Rabbana atina fid-dunya hasanah... - Ya Tuhan kami, berilah kami kebaikan di dunia dan akhirat...",
        tips=[
            "Jaga wudhu selama tawaf",
            "Tidak perlu menyentuh/mencium Hajar Aswad jika ramai",
            "Boleh berdoa dengan bahasa sendiri",
            "Batas tawaf: Hijr Ismail termasuk dalam putaran"
        ],
        common_mistakes=[
            "Arah putaran salah (harus counter-clockwise)",
            "Tidak mulai dari Hajar Aswad",
            "Memaksa menyentuh Hajar Aswad hingga menyakiti orang lain",
            "Tawaf tidak mengelilingi Hijr Ismail"
        ]
    ),
    
    RitualStep.SHOLAT_TAWAF: RitualInfo(
        id=RitualStep.SHOLAT_TAWAF,
        name="Sholat Sunnah Tawaf",
        arabic="صلاة الطواف",
        icon="🤲",
        location="Maqam Ibrahim (jika memungkinkan)",
        description="Setelah menyelesaikan tawaf, disunnahkan sholat 2 rakaat di belakang Maqam Ibrahim.",
        steps=[
            "Menuju Maqam Ibrahim (jika tidak ramai)",
            "Atau sholat di tempat lain dalam Masjidil Haram",
            "Sholat 2 rakaat sunnah",
            "Rakaat 1: Al-Fatihah + Al-Kafirun",
            "Rakaat 2: Al-Fatihah + Al-Ikhlas",
            "Setelah sholat, berdoa",
            "Minum air Zamzam"
        ],
        dua="اللَّهُمَّ إِنِّي أَسْأَلُكَ عِلْمًا نَافِعًا وَرِزْقًا وَاسِعًا وَشِفَاءً مِنْ كُلِّ دَاءٍ",
        dua_translation="Ya Allah, aku memohon ilmu yang bermanfaat, rizki yang luas, dan kesembuhan dari segala penyakit",
        tips=[
            "Tidak harus tepat di belakang Maqam Ibrahim",
            "Jangan menghalangi jamaah tawaf",
            "Minum Zamzam sambil berdiri menghadap Ka'bah"
        ],
        common_mistakes=[
            "Memaksakan diri sholat di Maqam Ibrahim yang sangat ramai",
            "Lupa minum Zamzam"
        ]
    ),
    
    RitualStep.SAI: RitualInfo(
        id=RitualStep.SAI,
        name="Sa'i",
        arabic="سعي",
        icon="🚶",
        location="Mas'a (antara Shafa dan Marwah)",
        description="Sa'i adalah berjalan 7 kali antara bukit Shafa dan Marwah, mengikuti jejak Siti Hajar.",
        steps=[
            "Menuju bukit Shafa",
            "Naik ke Shafa, menghadap Ka'bah",
            "Baca doa di Shafa",
            "Turun menuju Marwah (hitungan 1)",
            "Pria: Berlari kecil di area lampu hijau",
            "Naik ke Marwah, baca doa",
            "Kembali ke Shafa (hitungan 2)",
            "Ulangi hingga 7 kali",
            "Berakhir di Marwah (hitungan 7)"
        ],
        dua="إِنَّ الصَّفَا وَالْمَرْوَةَ مِنْ شَعَائِرِ اللَّهِ",
        dua_translation="Sesungguhnya Shafa dan Marwah adalah sebagian dari syiar Allah",
        tips=[
            "Dimulai dari Shafa, berakhir di Marwah",
            "Shafa → Marwah = 1 kali, Marwah → Shafa = 1 kali",
            "Wanita tidak perlu berlari",
            "Boleh istirahat jika lelah"
        ],
        common_mistakes=[
            "Menghitung Shafa-Marwah-Shafa sebagai 1 kali (seharusnya 2)",
            "Tidak memulai dari Shafa",
            "Wanita ikut berlari di lampu hijau"
        ]
    ),
    
    RitualStep.TAHALLUL: RitualInfo(
        id=RitualStep.TAHALLUL,
        name="Tahallul",
        arabic="تحلل",
        icon="✂️",
        location="Setelah Sa'i",
        description="Tahallul adalah mencukur atau memotong rambut sebagai tanda selesainya umrah.",
        steps=[
            "Setelah selesai sa'i di Marwah",
            "Pria: Cukur habis (lebih utama) atau potong pendek",
            "Wanita: Potong ujung rambut sekitar 1-3 cm",
            "Niat tahallul",
            "Setelah tahallul, semua larangan ihram gugur",
            "Umrah selesai! Alhamdulillah"
        ],
        dua="الْحَمْدُ لِلَّهِ الَّذِي بِنِعْمَتِهِ تَتِمُّ الصَّالِحَاتُ",
        dua_translation="Segala puji bagi Allah yang dengan nikmat-Nya sempurnalah amal shalih",
        tips=[
            "Cukur habis lebih utama dari potong",
            "Banyak tukang cukur di sekitar Marwah",
            "Setelah tahallul boleh ganti baju biasa"
        ],
        common_mistakes=[
            "Hanya memotong beberapa helai rambut",
            "Lupa tahallul dan langsung ganti baju"
        ]
    ),
}


# =============================================================================
# 3D VIEWER COMPONENT (HTML/JS)
# =============================================================================

KAABA_3D_HTML = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { margin: 0; overflow: hidden; background: #0a0a0a; }
        #container { width: 100%; height: 400px; }
        #controls {
            position: absolute;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 10px;
        }
        .btn {
            background: linear-gradient(135deg, #d4af37, #b8962e);
            color: #1a1a1a;
            border: none;
            padding: 10px 20px;
            border-radius: 20px;
            cursor: pointer;
            font-weight: bold;
        }
        .btn:hover { opacity: 0.9; }
        #info {
            position: absolute;
            top: 20px;
            left: 20px;
            color: #d4af37;
            font-family: Arial, sans-serif;
            background: rgba(0,0,0,0.7);
            padding: 15px;
            border-radius: 10px;
            max-width: 250px;
        }
        #hotspot {
            position: absolute;
            padding: 8px 15px;
            background: rgba(212, 175, 55, 0.9);
            color: #1a1a1a;
            border-radius: 15px;
            font-size: 12px;
            display: none;
            pointer-events: none;
        }
    </style>
</head>
<body>
    <div id="container"></div>
    <div id="info">
        <h3 style="margin: 0 0 10px 0;">🕋 Ka'bah Virtual</h3>
        <p style="margin: 0; font-size: 14px;">Drag untuk memutar<br>Scroll untuk zoom</p>
    </div>
    <div id="hotspot"></div>
    <div id="controls">
        <button class="btn" onclick="resetView()" aria-label="Reset tampilan">🔄 Reset</button>
        <button class="btn" onclick="toggleRotation()" aria-label="Putar otomatis">⏯️ Auto Rotate</button>
        <button class="btn" onclick="showHajarAswad()" aria-label="Lihat Hajar Aswad">⬛ Hajar Aswad</button>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script>
        let scene, camera, renderer, kaaba, controls;
        let autoRotate = true;
        
        function init() {
            // Scene
            scene = new THREE.Scene();
            scene.background = new THREE.Color(0x0a0a0a);
            
            // Camera
            camera = new THREE.PerspectiveCamera(75, window.innerWidth / 400, 0.1, 1000);
            camera.position.set(0, 5, 10);
            
            // Renderer
            renderer = new THREE.WebGLRenderer({ antialias: true });
            renderer.setSize(window.innerWidth, 400);
            document.getElementById('container').appendChild(renderer.domElement);
            
            // Lighting
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
            scene.add(ambientLight);
            
            const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
            directionalLight.position.set(5, 10, 5);
            scene.add(directionalLight);
            
            // Ka'bah (simplified cube with black material)
            const kaabaGeometry = new THREE.BoxGeometry(4, 5, 4);
            const kaabaMaterial = new THREE.MeshPhongMaterial({ 
                color: 0x1a1a1a,
                specular: 0x222222,
                shininess: 30
            });
            kaaba = new THREE.Mesh(kaabaGeometry, kaabaMaterial);
            kaaba.position.y = 2.5;
            scene.add(kaaba);
            
            // Gold band (Kiswah band)
            const bandGeometry = new THREE.BoxGeometry(4.1, 0.5, 4.1);
            const bandMaterial = new THREE.MeshPhongMaterial({ 
                color: 0xd4af37,
                specular: 0xffffff,
                shininess: 100
            });
            const band = new THREE.Mesh(bandGeometry, bandMaterial);
            band.position.y = 4;
            scene.add(band);
            
            // Hajar Aswad (black stone corner)
            const hajarGeometry = new THREE.SphereGeometry(0.3, 16, 16);
            const hajarMaterial = new THREE.MeshPhongMaterial({ color: 0x2a2a2a });
            const hajarAswad = new THREE.Mesh(hajarGeometry, hajarMaterial);
            hajarAswad.position.set(2, 1.5, 2);
            hajarAswad.name = 'hajarAswad';
            scene.add(hajarAswad);
            
            // Ground (Mataf area)
            const groundGeometry = new THREE.CircleGeometry(15, 64);
            const groundMaterial = new THREE.MeshPhongMaterial({ 
                color: 0x2d2d2d,
                side: THREE.DoubleSide
            });
            const ground = new THREE.Mesh(groundGeometry, groundMaterial);
            ground.rotation.x = -Math.PI / 2;
            scene.add(ground);
            
            // Tawaf direction indicator (arrow ring)
            const ringGeometry = new THREE.TorusGeometry(6, 0.1, 8, 100);
            const ringMaterial = new THREE.MeshBasicMaterial({ color: 0xd4af37 });
            const ring = new THREE.Mesh(ringGeometry, ringMaterial);
            ring.rotation.x = -Math.PI / 2;
            ring.position.y = 0.1;
            scene.add(ring);
            
            // Mouse controls
            let isDragging = false;
            let previousMousePosition = { x: 0, y: 0 };
            
            renderer.domElement.addEventListener('mousedown', (e) => {
                isDragging = true;
                autoRotate = false;
            });
            
            renderer.domElement.addEventListener('mouseup', () => {
                isDragging = false;
            });
            
            renderer.domElement.addEventListener('mousemove', (e) => {
                if (isDragging) {
                    const deltaMove = {
                        x: e.offsetX - previousMousePosition.x,
                        y: e.offsetY - previousMousePosition.y
                    };
                    
                    camera.position.x = camera.position.x * Math.cos(deltaMove.x * 0.01) - camera.position.z * Math.sin(deltaMove.x * 0.01);
                    camera.position.z = camera.position.z * Math.cos(deltaMove.x * 0.01) + camera.position.x * Math.sin(deltaMove.x * 0.01);
                    camera.lookAt(0, 2.5, 0);
                }
                previousMousePosition = { x: e.offsetX, y: e.offsetY };
            });
            
            // Zoom
            renderer.domElement.addEventListener('wheel', (e) => {
                e.preventDefault();
                const zoom = e.deltaY > 0 ? 1.1 : 0.9;
                camera.position.multiplyScalar(zoom);
                camera.position.clampLength(5, 20);
            });
            
            animate();
        }
        
        function animate() {
            requestAnimationFrame(animate);
            
            if (autoRotate) {
                camera.position.x = camera.position.x * Math.cos(0.002) - camera.position.z * Math.sin(0.002);
                camera.position.z = camera.position.z * Math.cos(0.002) + camera.position.x * Math.sin(0.002);
            }
            
            camera.lookAt(0, 2.5, 0);
            renderer.render(scene, camera);
        }
        
        function resetView() {
            camera.position.set(0, 5, 10);
            camera.lookAt(0, 2.5, 0);
        }
        
        function toggleRotation() {
            autoRotate = !autoRotate;
        }
        
        function showHajarAswad() {
            camera.position.set(4, 2, 4);
            camera.lookAt(2, 1.5, 2);
            autoRotate = false;
            
            const hotspot = document.getElementById('hotspot');
            hotspot.innerHTML = '⬛ Hajar Aswad<br><small>Pojok tenggara Ka\\'bah</small>';
            hotspot.style.display = 'block';
            hotspot.style.top = '150px';
            hotspot.style.left = '60%';
            
            setTimeout(() => { hotspot.style.display = 'none'; }, 3000);
        }
        
        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth / 400;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, 400);
        });
        
        init();
    </script>
</body>
</html>
"""


# =============================================================================
# RENDER FUNCTIONS
# =============================================================================

def render_3d_kaaba():
    """Render interactive 3D Ka'bah viewer."""
    
    st.markdown("### 🕋 Ka'bah 3D Virtual")
    st.caption("Drag untuk memutar, scroll untuk zoom")
    
    # Embed 3D viewer
    st.components.v1.html(KAABA_3D_HTML, height=450)


def render_ritual_step_card(ritual: RitualInfo, expanded: bool = False):
    """Render a ritual step card."""
    
    with st.expander(f"{ritual.icon} {ritual.name} ({ritual.arabic})", expanded=expanded):
        st.markdown(f"**📍 Lokasi:** {ritual.location}")
        st.markdown(ritual.description)
        
        # Steps
        st.markdown("#### 📋 Langkah-langkah:")
        for i, step in enumerate(ritual.steps, 1):
            st.markdown(f"{i}. {step}")
        
        # Dua
        st.markdown("#### 🤲 Doa:")
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a1a, #2d2d2d); padding: 1rem; border-radius: 10px; text-align: center; border: 1px solid #d4af37;">
            <div style="font-family: 'Traditional Arabic', serif; font-size: 1.5rem; color: #d4af37; direction: rtl; margin-bottom: 0.5rem;">{ritual.dua}</div>
            <div style="color: #b0b0b0; font-size: 0.9rem; font-style: italic;">{ritual.dua_translation}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Tips and Mistakes
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 💡 Tips:")
            for tip in ritual.tips:
                st.markdown(f"- ✅ {tip}")
        
        with col2:
            st.markdown("#### ⚠️ Kesalahan Umum:")
            for mistake in ritual.common_mistakes:
                st.markdown(f"- ❌ {mistake}")


def render_ritual_progress():
    """Render ritual progress tracker."""
    
    # Initialize with all ritual steps if empty
    if "manasik_progress" not in st.session_state or not st.session_state.manasik_progress:
        st.session_state.manasik_progress = {step.value: False for step in RitualStep}
    
    progress = st.session_state.manasik_progress
    completed = sum(1 for v in progress.values() if v)
    total = len(RitualStep)  # Use enum length, not dict length
    
    st.markdown("### 📊 Progress Umrah Anda")
    
    # Safe division
    progress_pct = completed / total if total > 0 else 0
    st.progress(progress_pct)
    st.caption(f"{completed}/{total} rukun selesai")
    
    # Checkboxes for each step
    cols = st.columns(3)
    for i, (step, ritual) in enumerate(RITUALS_DATA.items()):
        with cols[i % 3]:
            checked = st.checkbox(
                f"{ritual.icon} {ritual.name}",
                value=progress.get(step.value, False),
                key=f"progress_{step.value}"
            )
            progress[step.value] = checked
    
    if completed == total:
        st.balloons()
        st.success("🎉 Alhamdulillah! Umrah Anda telah selesai!")


def render_manasik_page():
    """Full manasik simulator page."""

    inject_css(HERO_CSS, CARD_CSS, AI_CARD_CSS)

    if not st.session_state.get("manasik_xp_awarded"):
        add_xp_safe(10, "Belajar manasik umrah")
        st.session_state.manasik_xp_awarded = True

    st.markdown("""
        <div class="page-hero">
            <h1>🕋 Manasik Umrah 3D</h1>
            <div class="subtitle">Panduan interaktif manasik umrah dengan visualisasi 3D</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["🎮 3D Ka'bah", "📖 Panduan Lengkap", "✅ Progress"])
    
    with tab1:
        render_3d_kaaba()
        
        st.markdown("### 🔵 Titik Penting")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div style="background: #1a1a1a; padding: 1rem; border-radius: 10px; text-align: center;">
                <div style="font-size: 2rem;">⬛</div>
                <div style="color: #d4af37; font-weight: bold;">Hajar Aswad</div>
                <div style="color: #b0b0b0; font-size: 0.8rem;">Titik mulai & akhir tawaf</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="background: #1a1a1a; padding: 1rem; border-radius: 10px; text-align: center;">
                <div style="font-size: 2rem;">🏛️</div>
                <div style="color: #d4af37; font-weight: bold;">Maqam Ibrahim</div>
                <div style="color: #b0b0b0; font-size: 0.8rem;">Tempat sholat tawaf</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div style="background: #1a1a1a; padding: 1rem; border-radius: 10px; text-align: center;">
                <div style="font-size: 2rem;">🌙</div>
                <div style="color: #d4af37; font-weight: bold;">Hijr Ismail</div>
                <div style="color: #b0b0b0; font-size: 0.8rem;">Wajib diputari saat tawaf</div>
            </div>
            """, unsafe_allow_html=True)
    
    with tab2:
        st.markdown("### 📖 Rukun Umrah")
        st.caption("Klik setiap rukun untuk melihat detail")
        
        for step, ritual in RITUALS_DATA.items():
            render_ritual_step_card(ritual, expanded=False)
    
    with tab3:
        render_ritual_progress()
    
    # Quick reference
    st.divider()
    st.markdown("### 📌 Ringkasan Cepat")
    
    st.markdown("""
    | Rukun | Lokasi | Jumlah |
    |-------|--------|--------|
    | 1. Ihram | Miqat | 1x niat |
    | 2. Tawaf | Ka'bah | 7 putaran |
    | 3. Sa'i | Shafa-Marwah | 7 kali |
    | 4. Tahallul | Setelah Sa'i | Cukur/potong |
    """)

    st.markdown("---")
    if st.button("🤖 Tips Manasik dari AI", key="manasik_ai_tips"):
        with st.spinner("Menganalisis..."):
            tips = ai_complete(
                "Berikan 4 tips penting untuk jamaah yang baru pertama kali melakukan manasik umrah. "
                "Termasuk tips tawaf, sai, dan ihram. Bahasa Indonesia.",
                system_prompt="Kamu adalah pembimbing manasik umrah berpengalaman.",
                max_tokens=400,
            )
            if tips:
                st.markdown(f'''
                    <div class="ai-card">
                        <h4>🤖 Tips AI Manasik Umrah</h4>
                        <p>{tips}</p>
                    </div>
                ''', unsafe_allow_html=True)
            else:
                st.info("AI tidak tersedia saat ini")


def render_manasik_mini_widget():
    """Mini widget for sidebar."""
    
    # Ensure manasik_progress is initialized
    if "manasik_progress" not in st.session_state or not st.session_state.manasik_progress:
        st.session_state.manasik_progress = {step.value: False for step in RitualStep}
    
    progress = st.session_state.get("manasik_progress", {})
    completed = sum(1 for v in progress.values() if v)
    total = len(RitualStep)  # Use enum length, always 6
    
    # Safe percentage calculation
    pct = (completed / total * 100) if total > 0 else 0
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1a1a1a, #2d2d2d); padding: 1rem; border-radius: 15px; border: 1px solid #d4af37;">
        <div style="color: #d4af37; font-size: 0.8rem;">🕋 Manasik Progress</div>
        <div style="background: #333; border-radius: 10px; height: 10px; margin: 0.5rem 0; overflow: hidden;">
            <div style="width: {pct}%; height: 100%; background: linear-gradient(90deg, #d4af37, #f4d03f);"></div>
        </div>
        <div style="color: #b0b0b0; font-size: 0.75rem;">{completed}/{total} rukun selesai</div>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    "render_3d_kaaba",
    "render_manasik_page",
    "render_manasik_mini_widget",
    "render_ritual_step_card",
    "RITUALS_DATA",
    "RitualStep",
]
