"""
LABBAIK AI v6.0 - FAQ Knowledge Base
===================================
Frequently asked questions about Umrah.
"""

from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class FAQ:
    """FAQ entry."""
    id: str
    question: str
    answer: str
    category: str
    keywords: List[str]
    related_faqs: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "question": self.question,
            "answer": self.answer,
            "category": self.category,
            "keywords": self.keywords,
        }


# =============================================================================
# GENERAL UMRAH FAQ
# =============================================================================

GENERAL_FAQ = [
    FAQ(
        id="gen_001",
        question="Apa itu Umrah?",
        answer="""Umrah adalah ibadah yang dilakukan dengan mengunjungi Ka'bah di Masjidil Haram, Makkah, 
dengan melaksanakan serangkaian ritual ibadah yaitu: Ihram, Tawaf, Sa'i, dan Tahallul. 
Umrah sering disebut "haji kecil" dan dapat dilakukan kapan saja sepanjang tahun, 
berbeda dengan haji yang hanya dilaksanakan pada waktu tertentu.""",
        category="general",
        keywords=["umrah", "definisi", "pengertian", "apa"]
    ),
    FAQ(
        id="gen_002",
        question="Apa perbedaan antara Umrah dan Haji?",
        answer="""Perbedaan utama antara Umrah dan Haji:

1. **Waktu Pelaksanaan**
   - Umrah: Dapat dilakukan kapan saja sepanjang tahun
   - Haji: Hanya pada tanggal tertentu di bulan Dzulhijjah

2. **Hukum**
   - Umrah: Sunnah Muakkadah (sangat dianjurkan)
   - Haji: Wajib sekali seumur hidup bagi yang mampu

3. **Rukun**
   - Umrah: 4 rukun (Ihram, Tawaf, Sa'i, Tahallul)
   - Haji: 6 rukun (ditambah Wukuf di Arafah dan Mabit di Muzdalifah)

4. **Durasi**
   - Umrah: 2-3 jam untuk ritual utama
   - Haji: 5-6 hari untuk rangkaian manasik""",
        category="general",
        keywords=["perbedaan", "haji", "beda"]
    ),
    FAQ(
        id="gen_003",
        question="Berapa lama waktu yang dibutuhkan untuk Umrah?",
        answer="""Waktu yang dibutuhkan untuk Umrah bervariasi:

1. **Ritual Umrah saja**: 2-4 jam
   - Tawaf: 45-90 menit
   - Sa'i: 30-60 menit
   - Tahallul: 10-30 menit

2. **Paket perjalanan Umrah**:
   - Singkat: 9-10 hari
   - Reguler: 12-14 hari
   - Plus: 15-21 hari

Waktu di luar ritual digunakan untuk:
- Shalat di Masjidil Haram dan Masjid Nabawi
- Ziarah ke tempat-tempat bersejarah
- Istirahat dan persiapan""",
        category="general",
        keywords=["waktu", "durasi", "lama", "berapa hari"]
    ),
    FAQ(
        id="gen_004",
        question="Kapan waktu terbaik untuk Umrah?",
        answer="""Waktu terbaik untuk Umrah tergantung preferensi:

**Paling Utama:**
- Bulan Ramadan (pahala seperti haji bersama Nabi SAW)

**Cuaca Nyaman:**
- November - Februari (musim dingin, suhu 15-25°C)

**Lebih Sepi & Ekonomis:**
- Mei - September (musim panas, hindari peak season)
- Diluar bulan Ramadan dan musim haji

**Hindari:**
- Musim haji (8-13 Dzulhijjah) - sangat padat
- Liburan sekolah Indonesia - harga tinggi

**Tips:** Umrah di 10 hari terakhir Ramadan sangat utama untuk mencari Lailatul Qadr.""",
        category="general",
        keywords=["waktu", "terbaik", "kapan", "musim"]
    ),
    FAQ(
        id="gen_005",
        question="Berapa biaya Umrah?",
        answer="""Biaya Umrah bervariasi tergantung beberapa faktor:

**Kisaran Biaya (2024-2025):**
- Backpacker/Ekonomis: Rp 20-25 juta
- Reguler: Rp 25-35 juta
- Plus: Rp 35-50 juta
- VIP: Rp 50-100 juta

**Komponen Biaya:**
1. Tiket pesawat: 40-50%
2. Hotel: 25-35%
3. Visa: Rp 3-5 juta
4. Handling & muthawif: 10-15%
5. Asuransi & lainnya: 5-10%

**Faktor yang Mempengaruhi:**
- Musim (Ramadan lebih mahal)
- Jarak hotel ke Masjidil Haram
- Bintang hotel
- Maskapai penerbangan
- Kota keberangkatan

*Gunakan fitur Simulasi Biaya LABBAIK AI untuk estimasi akurat.*""",
        category="general",
        keywords=["biaya", "harga", "berapa", "cost"]
    ),
]

# =============================================================================
# PREPARATION FAQ
# =============================================================================

PREPARATION_FAQ = [
    FAQ(
        id="prep_001",
        question="Apa saja dokumen yang diperlukan untuk Umrah?",
        answer="""Dokumen yang diperlukan untuk Umrah:

**Wajib:**
1. **Paspor** - Masa berlaku minimal 6 bulan dari tanggal keberangkatan
2. **Visa Umrah** - Diurus melalui travel agent
3. **Tiket Pesawat** - Pulang-pergi
4. **Bukti Vaksinasi** - Meningitis dan vaksin lain sesuai ketentuan

**Pendukung:**
- KTP asli & fotokopi
- Kartu Keluarga fotokopi
- Buku nikah (untuk pasangan)
- Akta kelahiran (untuk anak)
- Surat izin mahram (untuk wanita di bawah 45 tahun)
- Pas foto 4x6 (latar putih, 80% wajah)

**Tips:**
- Siapkan dokumen 2-3 bulan sebelum keberangkatan
- Bawa fotokopi semua dokumen
- Simpan scan dokumen di cloud storage""",
        category="preparation",
        keywords=["dokumen", "syarat", "persyaratan", "paspor", "visa"]
    ),
    FAQ(
        id="prep_002",
        question="Bagaimana cara mengurus visa Umrah?",
        answer="""Cara mengurus Visa Umrah:

**Melalui Travel Agent (Rekomendasi):**
1. Pilih travel agent resmi berizin Kemenag
2. Serahkan dokumen yang diperlukan
3. Travel agent akan memproses ke Kedutaan Saudi
4. Proses: 3-7 hari kerja
5. Biaya: Rp 3-5 juta (termasuk dalam paket)

**Dokumen untuk Visa:**
- Paspor asli (min. 6 bulan berlaku)
- Foto 4x6 latar putih
- Bukti vaksinasi meningitis
- Formulir aplikasi visa
- Surat keterangan kerja/izin usaha (opsional)

**Ketentuan Khusus:**
- Wanita di bawah 45 tahun: Harus dengan mahram
- Wanita 45+ tahun: Boleh tanpa mahram dengan surat izin

**Masa Berlaku Visa:** 90 hari sejak diterbitkan""",
        category="preparation",
        keywords=["visa", "cara", "mengurus", "proses"]
    ),
    FAQ(
        id="prep_003",
        question="Apa saja yang harus dibawa ke Umrah?",
        answer="""Daftar perlengkapan Umrah:

**Pakaian:**
- Ihram (2 set untuk pria)
- Mukena (wanita)
- Pakaian harian nyaman
- Sandal/sepatu yang mudah dilepas
- Jaket/sweater (AC masjid dingin)

**Ibadah:**
- Al-Quran kecil
- Buku doa & dzikir
- Tasbih
- Sajadah travel

**Kesehatan:**
- Obat-obatan pribadi
- P3K mini
- Masker
- Hand sanitizer
- Sunblock

**Lainnya:**
- Tas pinggang/selempang kecil
- Power bank
- Adaptor colokan (Saudi: Type G)
- Kacamata hitam
- Payung lipat

**Tips:**
- Bawa koper yang ringan dan mudah dikenali
- Label semua barang dengan nama & nomor HP
- Jangan bawa barang berlebihan""",
        category="preparation",
        keywords=["perlengkapan", "bawa", "tas", "barang"]
    ),
    FAQ(
        id="prep_004",
        question="Vaksin apa yang diperlukan untuk Umrah?",
        answer="""Vaksinasi yang diperlukan untuk Umrah:

**Wajib:**
1. **Meningitis Meningokokus (ACYW135)**
   - Wajib untuk semua jamaah
   - Berlaku 3 tahun
   - Dilakukan minimal 10 hari sebelum berangkat
   - Tempat: KKP (Kantor Kesehatan Pelabuhan)

**Sesuai Ketentuan Saudi (dapat berubah):**
2. **COVID-19** - Sesuai kebijakan terbaru
3. **Polio** - Untuk beberapa negara
4. **Yellow Fever** - Jika transit di negara endemis

**Dokumen:**
- International Certificate of Vaccination (ICV/Buku Kuning)

**Tips:**
- Cek persyaratan terbaru sebelum keberangkatan
- Vaksinasi 2-4 minggu sebelum berangkat
- Bawa bukti vaksinasi fisik dan digital""",
        category="preparation",
        keywords=["vaksin", "vaksinasi", "suntik", "meningitis"]
    ),
]

# =============================================================================
# RITUAL FAQ
# =============================================================================

RITUAL_FAQ = [
    FAQ(
        id="ritual_001",
        question="Apa saja rukun Umrah?",
        answer="""Rukun Umrah ada 4:

**1. Ihram**
- Niat memasuki ritual Umrah
- Memakai pakaian ihram (pria: 2 kain tanpa jahitan)
- Dimulai dari miqat (batas tempat)

**2. Tawaf**
- Mengelilingi Ka'bah 7 kali
- Dimulai dan diakhiri di Hajar Aswad
- Searah jarum jam dengan Ka'bah di sebelah kiri

**3. Sa'i**
- Berjalan 7 kali antara bukit Safa dan Marwah
- Dimulai dari Safa, diakhiri di Marwah
- Boleh berlari kecil di area tertentu (untuk pria)

**4. Tahallul**
- Mencukur atau memotong rambut
- Pria: dicukur habis (dianjurkan) atau dipotong minimal 3 helai
- Wanita: memotong ujung rambut sepanjang ruas jari

Jika salah satu rukun tidak dilakukan, Umrah tidak sah.""",
        category="ritual",
        keywords=["rukun", "wajib", "syarat"]
    ),
    FAQ(
        id="ritual_002",
        question="Bagaimana tata cara ihram?",
        answer="""Tata cara Ihram:

**Persiapan (Sunnah):**
1. Mandi besar (janabah/ihram)
2. Memotong kuku dan merapikan rambut
3. Memakai wewangian di badan (bukan pakaian)

**Memakai Pakaian Ihram:**
- Pria: 2 kain putih tanpa jahitan (rida' dan izar)
- Wanita: Pakaian biasa menutup aurat, tidak bercadar/sarung tangan

**Niat di Miqat:**
- Menghadap kiblat
- Shalat sunnah 2 rakaat (sunnah)
- Mengucapkan: "Labbaika Allahumma 'Umratan"
- Membaca talbiyah dengan keras (pria)

**Larangan Selama Ihram:**
1. Memakai pakaian berjahit (pria)
2. Menutup kepala (pria) / wajah (wanita)
3. Memakai wewangian
4. Memotong kuku/rambut
5. Memburu/membunuh binatang darat
6. Akad nikah
7. Berhubungan suami istri""",
        category="ritual",
        keywords=["ihram", "cara", "tata", "niat"]
    ),
    FAQ(
        id="ritual_003",
        question="Bagaimana tata cara Tawaf?",
        answer="""Tata cara Tawaf:

**Persiapan:**
- Dalam keadaan suci (berwudhu)
- Menutup aurat
- Niat tawaf

**Pelaksanaan:**
1. **Mulai dari Hajar Aswad**
   - Menghadap Hajar Aswad
   - Membaca "Bismillahi Allahu Akbar"
   - Mengangkat tangan seperti takbir

2. **Mengelilingi Ka'bah 7 kali**
   - Ka'bah di sebelah kiri
   - Searah jarum jam
   - Boleh membaca doa bebas

3. **Sunnah dalam Tawaf:**
   - Idhtiba' (membuka bahu kanan) - putaran 1-7
   - Raml (jalan cepat) - putaran 1-3 saja
   - Istilam Hajar Aswad setiap putaran

4. **Doa Khusus:**
   - Antara Rukun Yamani dan Hajar Aswad:
   "Rabbana atina fid dunya hasanah..."

**Setelah Tawaf:**
- Shalat 2 rakaat di belakang Maqam Ibrahim
- Minum air zamzam""",
        category="ritual",
        keywords=["tawaf", "cara", "tata", "keliling"]
    ),
    FAQ(
        id="ritual_004",
        question="Bagaimana tata cara Sa'i?",
        answer="""Tata cara Sa'i:

**Persiapan:**
- Selesai tawaf dan shalat 2 rakaat
- Boleh tidak berwudhu (lebih utama berwudhu)

**Pelaksanaan:**
1. **Menuju Bukit Safa**
   - Membaca: "Innash shafa wal marwata min sya'airillah"
   - Naik ke bukit Safa menghadap Ka'bah

2. **Di Atas Safa:**
   - Membaca takbir, tahlil, dan doa
   - "La ilaha illallah wahdahu la syarikalah..."

3. **Berjalan ke Marwah (Hitungan 1)**
   - Berjalan biasa
   - Pria: berlari kecil di area lampu hijau
   - Membaca doa dan dzikir

4. **Di Atas Marwah:**
   - Menghadap Ka'bah
   - Membaca doa seperti di Safa

5. **Kembali ke Safa (Hitungan 2)**
   - Ulangi hingga 7 kali
   - Berakhir di Marwah

**Total:** 7 perjalanan (4x ke Marwah, 3x ke Safa)""",
        category="ritual",
        keywords=["sai", "sa'i", "cara", "tata", "safa", "marwah"]
    ),
]

# =============================================================================
# WOMEN FAQ
# =============================================================================

WOMEN_FAQ = [
    FAQ(
        id="women_001",
        question="Apakah wanita haid boleh melakukan Umrah?",
        answer="""Ketentuan wanita haid dalam Umrah:

**Yang BOLEH dilakukan:**
- Ihram dan niat Umrah
- Sa'i (menurut sebagian ulama)
- Semua aktivitas selain masuk masjid
- Membaca doa dan dzikir
- Tahallul setelah suci

**Yang TIDAK BOLEH:**
- Memasuki Masjidil Haram
- Tawaf (harus dalam keadaan suci)

**Solusi:**
1. **Menunggu suci** - Jika waktu memungkinkan
2. **Tawaf di akhir** - Lakukan sa'i dulu (jika memilih pendapat ini)
3. **Konsultasi muthawif** - Untuk kondisi khusus

**Tips Praktis:**
- Bawa pembalut/tampon secukupnya
- Catat jadwal haid sebelum berangkat
- Siapkan pakaian ganti
- Konsultasi dengan ustadz/ustadzah pendamping""",
        category="women",
        keywords=["haid", "wanita", "menstruasi", "perempuan"]
    ),
    FAQ(
        id="women_002",
        question="Apakah wanita boleh Umrah tanpa mahram?",
        answer="""Ketentuan mahram untuk wanita Umrah:

**Ketentuan Saudi Arabia (terbaru):**
- Wanita usia 45+ tahun: Boleh tanpa mahram
- Wanita di bawah 45 tahun: Harus dengan mahram

**Siapa yang Termasuk Mahram:**
- Suami
- Ayah/kakek
- Anak laki-laki/cucu
- Saudara laki-laki
- Paman (adik/kakak ayah/ibu)
- Keponakan laki-laki
- Ayah/anak tiri
- Ayah/anak mertua

**Syarat Mahram:**
- Muslim
- Baligh
- Berakal
- Mampu menjaga

**Dokumen yang Diperlukan:**
- KK/Akta untuk bukti hubungan mahram
- Surat nikah (jika dengan suami)

**Untuk Wanita 45+ Tanpa Mahram:**
- Surat pernyataan tidak ada mahram
- Bergabung dengan rombongan resmi""",
        category="women",
        keywords=["mahram", "wanita", "pendamping", "perempuan"]
    ),
]

# =============================================================================
# HEALTH FAQ
# =============================================================================

HEALTH_FAQ = [
    FAQ(
        id="health_001",
        question="Bagaimana menjaga kesehatan selama Umrah?",
        answer="""Tips menjaga kesehatan selama Umrah:

**Sebelum Berangkat:**
- Medical check-up
- Vaksinasi lengkap
- Siapkan obat-obatan pribadi
- Latihan fisik (jalan kaki)

**Selama di Saudi:**
1. **Hidrasi:** Minum air minimal 2-3 liter/hari
2. **Nutrisi:** Makan teratur, pilih makanan bersih
3. **Istirahat:** Tidur cukup 6-8 jam
4. **Kebersihan:** Cuci tangan sering, pakai masker jika perlu

**Hindari:**
- Minuman es berlebihan
- Makanan dari pedagang tidak higienis
- Kelelahan berlebihan
- Dehidrasi

**Obat yang Perlu Dibawa:**
- Obat flu/batuk/demam
- Obat maag
- Obat diare
- Obat alergi
- Vitamin
- Plester/koyo
- Obat rutin (jika ada)""",
        category="health",
        keywords=["kesehatan", "sakit", "obat", "sehat"]
    ),
    FAQ(
        id="health_002",
        question="Bagaimana jika sakit selama Umrah?",
        answer="""Penanganan jika sakit selama Umrah:

**Langkah Pertama:**
1. Istirahat di hotel
2. Minum obat yang dibawa
3. Perbanyak minum air
4. Lapor ke muthawif/tour leader

**Jika Perlu ke Dokter:**
- Gunakan asuransi perjalanan
- Minta bantuan muthawif
- Klinik tersedia di sekitar hotel
- RS rujukan: RS Ajyad, RS King Faisal

**Kondisi Darurat:**
- Hubungi: 997 (Saudi Emergency)
- KBRI Riyadh: +966-11-488-2800
- KJRI Jeddah: +966-12-667-6020

**Tips:**
- Jangan memaksakan diri jika sakit
- Ibadah bisa ditunda hingga sembuh
- Tawaf dengan kursi roda tersedia
- Simpan nomor darurat di HP""",
        category="health",
        keywords=["sakit", "dokter", "rumah sakit", "darurat"]
    ),
]

# =============================================================================
# SAFETY FAQ - Keamanan & Keselamatan
# =============================================================================

SAFETY_FAQ = [
    FAQ(
        id="safety_001",
        question="Bagaimana cara menjaga anak agar tidak hilang di Masjidil Haram?",
        answer="""Tips menjaga anak di Masjidil Haram:

**1. Gelang RFID GRATIS dari Otoritas Masjidil Haram**
Tersedia gelang identitas pintar RFID GRATIS khusus untuk anak-anak dan lansia!

**Lokasi Pengambilan (24 Jam):**
- Ajyad Gate 3 (Pintu Ajyad 3)
- King Abdulaziz Gate (Pintu King Abdulaziz)
- King Fahd Gate No. 79 (Pintu King Fahd No. 79)

**Cara Kerja:**
- Daftarkan nomor kontak wali di gelang
- Jika anak terpisah, petugas akan memindai gelang
- Wali langsung dihubungi untuk penjemputan

**2. Tips Tambahan:**
- Pakaikan anak baju warna mencolok
- Foto anak sebelum masuk masjid (untuk identifikasi)
- Ajarkan anak titik kumpul jika terpisah
- Simpan kartu identitas di saku anak
- Jangan biarkan anak jauh dari jangkauan

**Sumber:** HIMPUH (Desember 2024)""",
        category="safety",
        keywords=["anak", "hilang", "terpisah", "gelang", "rfid", "keamanan", "lost", "child"]
    ),
    FAQ(
        id="safety_002",
        question="Apa itu gelang RFID di Masjidil Haram?",
        answer="""**Gelang RFID Masjidil Haram**

Gelang identitas pintar dengan teknologi RFID (Radio Frequency Identification) yang disediakan GRATIS oleh Otoritas Umum Pengelolaan Urusan Masjidil Haram dan Masjid Nabawi.

**Untuk Siapa:**
- Anak-anak
- Lansia
- Jamaah yang rentan terpisah dalam kerumunan

**Lokasi Pengambilan (24 Jam):**
1. Ajyad Gate 3
2. King Abdulaziz Gate
3. King Fahd Gate No. 79

**Cara Mendapatkan:**
1. Kunjungi gerbang di atas
2. Isi data kontak wali/pendamping
3. Gelang langsung dipasang

**Cara Kerja:**
- Nomor kontak wali tercantum di gelang
- Jika jamaah terpisah, petugas memindai gelang
- Sistem menghubungi wali untuk penjemputan

**Tips:**
- Gunakan nomor WA yang aktif
- Bisa pakai nomor Indonesia atau Saudi
- Pastikan anak/lansia memahami fungsi gelang

**Sumber:** HIMPUH (Desember 2024)""",
        category="safety",
        keywords=["gelang", "rfid", "wristband", "identitas", "safety", "keamanan"]
    ),
    FAQ(
        id="safety_003",
        question="Bagaimana menjaga lansia agar tidak terpisah saat umrah?",
        answer="""Tips menjaga lansia di Masjidil Haram:

**1. Gunakan Gelang RFID GRATIS**
Tersedia di gerbang Masjidil Haram (24 jam):
- Ajyad Gate 3
- King Abdulaziz Gate
- King Fahd Gate No. 79

**2. Fasilitas untuk Lansia:**
- Kursi roda tersedia GRATIS di pintu masuk
- Jalur khusus lansia di beberapa area
- Petugas siap membantu

**3. Tips Praktis:**
- Pakaikan gelang RFID dengan nomor kontak Anda
- Foto lansia sebelum masuk (untuk identifikasi)
- Tentukan titik kumpul jika terpisah
- Bawa tongkat atau alat bantu jalan
- Jangan tinggalkan lansia sendirian
- Pilih waktu ibadah yang tidak terlalu ramai
- Gunakan kursi roda jika perlu

**4. Nomor Darurat:**
- Saudi Emergency: 997
- KBRI Riyadh: +966-11-488-2800
- KJRI Jeddah: +966-12-667-6020

**Sumber:** HIMPUH (Desember 2024)""",
        category="safety",
        keywords=["lansia", "orangtua", "elderly", "terpisah", "hilang", "kursi roda"]
    ),
    FAQ(
        id="safety_004",
        question="Apa saja nomor darurat di Arab Saudi?",
        answer="""**Nomor Darurat di Arab Saudi:**

**Layanan Darurat Saudi:**
- 🚨 Polisi: **999**
- 🚑 Ambulans: **997**
- 🚒 Pemadam Kebakaran: **998**
- 🚦 Kecelakaan Lalu Lintas: **993**

**Kedutaan/Konsulat Indonesia:**
- KBRI Riyadh: **+966-11-488-2800**
- KJRI Jeddah: **+966-12-667-6020**
- Hotline Perlindungan WNI: **+966-54-308-0009**

**Rumah Sakit Rujukan:**
- RS Ajyad (dekat Masjidil Haram)
- RS King Faisal
- RS King Abdullah

**Tips:**
- Simpan semua nomor di HP sebelum berangkat
- Buat kartu darurat dengan info penting
- Informasikan nomor kontak ke keluarga di Indonesia
- Aktifkan roaming atau beli SIM lokal Saudi

**Layanan di Masjidil Haram:**
- Lost & Found: Tanya petugas di pintu gerbang
- Gelang RFID untuk anak/lansia: Gratis di Gate 3, King Abdulaziz, King Fahd 79""",
        category="safety",
        keywords=["darurat", "emergency", "polisi", "ambulans", "nomor", "telepon", "kbri", "kjri"]
    ),
]

# =============================================================================
# COLLECTION FUNCTIONS
# =============================================================================

def get_all_faqs() -> List[FAQ]:
    """Get all FAQs."""
    all_faqs = []
    all_faqs.extend(GENERAL_FAQ)
    all_faqs.extend(PREPARATION_FAQ)
    all_faqs.extend(RITUAL_FAQ)
    all_faqs.extend(WOMEN_FAQ)
    all_faqs.extend(HEALTH_FAQ)
    all_faqs.extend(SAFETY_FAQ)
    return all_faqs


def get_faqs_by_category(category: str) -> List[FAQ]:
    """Get FAQs by category."""
    all_faqs = get_all_faqs()
    return [f for f in all_faqs if f.category == category]


def get_faq_categories() -> List[str]:
    """Get all unique categories."""
    return ["general", "preparation", "ritual", "women", "health", "safety"]


def search_faqs(query: str) -> List[FAQ]:
    """Search FAQs by keyword."""
    query = query.lower()
    all_faqs = get_all_faqs()
    
    results = []
    for faq in all_faqs:
        score = 0
        
        # Check keywords
        for kw in faq.keywords:
            if kw in query or query in kw:
                score += 2
        
        # Check question
        if query in faq.question.lower():
            score += 3
        
        # Check answer
        if query in faq.answer.lower():
            score += 1
        
        if score > 0:
            results.append((faq, score))
    
    # Sort by score
    results.sort(key=lambda x: x[1], reverse=True)
    return [f for f, _ in results]


def get_faq_count() -> int:
    """Get total FAQ count."""
    return len(get_all_faqs())


# Export for RAG
FAQ_TEXT = "\n\n".join([
    f"**Q: {f.question}**\n\n{f.answer}"
    for f in get_all_faqs()
])
