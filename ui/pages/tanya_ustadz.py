"""
================================================================================
LABBAIK AI - TANYA USTADZ AI
================================================================================
Lokasi: ui/pages/tanya_ustadz.py
Fitur: Community Tanya Ustadz AI - Q&A fiqih umrah dengan dalil & rujukan
        + Database fiqih pre-answered, search, history, helpful rating
================================================================================
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional
import os
import re

from services.ai.helpers import ai_complete, add_xp_safe
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS, EMPTY_STATE_CSS, SKELETON_CSS, render_skeleton

# =============================================================================
# CONSTANTS & DATA
# =============================================================================

USTADZ_SYSTEM_PROMPT = """Anda adalah AI ustadz yang ahli dalam fiqih umrah dan haji, terutama berdasarkan madzhab Syafi'i (mayoritas Indonesia).

Panduan menjawab:
1. Gunakan Bahasa Indonesia yang jelas dan mudah dipahami
2. Sertakan dalil Al-Quran atau Hadits yang relevan
3. Rujuk kitab fiqih klasik jika memungkinkan (Al-Majmu', Fathul Qarib, dll)
4. Berikan kesimpulan singkat di akhir
5. Jika pertanyaan di luar konteks umrah/ibadah, arahkan kembali ke topik umrah
6. Hindari kontroversi antar madzhab - fokus pada pendapat yang lebih kuat di madzhab Syafi'i

Format jawaban:
**Jawaban:**
[Penjelasan utama 2-3 paragraf]

**Dalil:**
[Ayat Al-Quran atau Hadits jika relevan]

**Rujukan:**
[Nama kitab atau ulama]

**Kesimpulan:**
[Ringkasan singkat 1-2 kalimat]"""

CATEGORIES = {
    "semua": {"icon": "📋", "label": "Semua"},
    "tawaf": {"icon": "🕋", "label": "Tawaf"},
    "sai": {"icon": "🏃", "label": "Sa'i"},
    "ihram": {"icon": "🤍", "label": "Ihram"},
    "doa": {"icon": "🤲", "label": "Doa & Dzikir"},
    "umum": {"icon": "📖", "label": "Umum"},
}

POPULAR_QUESTIONS = [
    {"q": "Apa saja rukun umrah yang wajib dilaksanakan?", "cat": "umum"},
    {"q": "Bolehkah wanita umrah tanpa mahram?", "cat": "umum"},
    {"q": "Apa yang membatalkan umrah?", "cat": "umum"},
    {"q": "Berapa kali putaran tawaf dan bagaimana tata caranya?", "cat": "tawaf"},
    {"q": "Doa apa yang dibaca saat sa'i antara Safa dan Marwah?", "cat": "sai"},
    {"q": "Apa saja larangan saat ihram?", "cat": "ihram"},
    {"q": "Bolehkah memakai parfum saat ihram?", "cat": "ihram"},
    {"q": "Bagaimana tata cara umrah saat haid?", "cat": "umum"},
    {"q": "Doa apa yang dibaca saat melihat Ka'bah pertama kali?", "cat": "doa"},
    {"q": "Apakah boleh umrah berkali-kali dalam satu perjalanan?", "cat": "umum"},
]

# =============================================================================
# QA DATABASE - Pre-answered fiqih Q&A entries (Syafi'i madhab)
# =============================================================================

QA_DATABASE = [
    {
        "id": "qa_01",
        "question": "Apa saja rukun umrah dan wajib umrah?",
        "answer": (
            "**Jawaban:**\n"
            "Menurut madzhab Syafi'i, rukun umrah ada empat: (1) Ihram, yaitu berniat masuk dalam "
            "ibadah umrah dari miqat yang telah ditentukan; (2) Tawaf mengelilingi Ka'bah sebanyak "
            "7 putaran dimulai dari Hajar Aswad; (3) Sa'i antara bukit Safa dan Marwah sebanyak 7 kali; "
            "(4) Tahallul, yaitu mencukur atau memotong rambut minimal 3 helai.\n\n"
            "Adapun wajib umrah ada dua: (1) Berihram dari miqat yang telah ditentukan; (2) Menjauhi "
            "seluruh larangan ihram. Perbedaan antara rukun dan wajib adalah jika rukun ditinggalkan "
            "maka umrah tidak sah, sedangkan jika wajib ditinggalkan maka umrah tetap sah namun "
            "wajib membayar dam (denda berupa menyembelih kambing).\n\n"
            "**Dalil:**\n"
            "\"Dan sempurnakanlah ibadah haji dan umrah karena Allah.\" (QS. Al-Baqarah: 196)\n\n"
            "**Rujukan:**\n"
            "- Al-Majmu' Syarh al-Muhadzdzab, Imam Nawawi\n"
            "- Fathul Qarib, Ibnu Qasim al-Ghazi\n\n"
            "**Kesimpulan:**\n"
            "Rukun umrah ada 4 (ihram, tawaf, sa'i, tahallul) dan wajib umrah ada 2 "
            "(ihram dari miqat, menjauhi larangan ihram)."
        ),
        "category": "umum",
        "views": 0,
        "helpful": 0,
    },
    {
        "id": "qa_02",
        "question": "Bagaimana tata cara tawaf yang benar (7 putaran dari Hajar Aswad)?",
        "answer": (
            "**Jawaban:**\n"
            "Tawaf adalah mengelilingi Ka'bah sebanyak 7 putaran dengan Ka'bah berada di sebelah kiri. "
            "Setiap putaran dimulai dari garis sejajar Hajar Aswad (ditandai garis hijau di lantai) dan "
            "berakhir kembali di titik yang sama. Sebelum memulai, disunnahkan menghadap Hajar Aswad, "
            "mengangkat tangan kanan, dan mengucapkan 'Bismillahi Allahu Akbar'.\n\n"
            "Syarat sah tawaf antara lain: suci dari hadats besar dan kecil, menutup aurat, Ka'bah "
            "berada di sebelah kiri, 7 putaran penuh tanpa terputus tanpa uzur, dan dilakukan di dalam "
            "Masjidil Haram. Sunnahnya antara lain: al-idhtiba' (membuka bahu kanan) pada tawaf qudum, "
            "raml (jalan cepat) pada 3 putaran pertama tawaf qudum, dan berdoa sepanjang tawaf.\n\n"
            "Setelah selesai 7 putaran, disunnahkan shalat 2 rakaat di belakang Maqam Ibrahim. "
            "Jika tempat penuh, boleh shalat di mana saja dalam Masjidil Haram.\n\n"
            "**Dalil:**\n"
            "\"Dan hendaklah mereka melakukan tawaf sekeliling rumah yang tua itu (Baitullah).\" "
            "(QS. Al-Hajj: 29)\n\n"
            "**Rujukan:**\n"
            "- Fathul Mu'in, Syaikh Zainuddin al-Malibari\n"
            "- Al-Majmu', Imam Nawawi\n\n"
            "**Kesimpulan:**\n"
            "Tawaf dilakukan 7 putaran dari Hajar Aswad dengan Ka'bah di sebelah kiri, "
            "dalam keadaan suci dan menutup aurat."
        ),
        "category": "tawaf",
        "views": 0,
        "helpful": 0,
    },
    {
        "id": "qa_03",
        "question": "Bagaimana tata cara sa'i antara Safa dan Marwah?",
        "answer": (
            "**Jawaban:**\n"
            "Sa'i adalah berjalan dari bukit Safa ke bukit Marwah dan sebaliknya sebanyak 7 kali "
            "perjalanan (dimulai dari Safa dan berakhir di Marwah). Perjalanan dari Safa ke Marwah "
            "dihitung satu kali, dan dari Marwah ke Safa dihitung satu kali, sehingga total ada "
            "7 perjalanan.\n\n"
            "Sebelum memulai, disunnahkan naik ke bukit Safa dan menghadap Ka'bah sambil berdoa. "
            "Di antara dua tanda hijau (pilar hijau), disunnahkan bagi laki-laki untuk berlari kecil "
            "(raml). Wanita cukup berjalan biasa. Selama sa'i dianjurkan memperbanyak dzikir dan doa.\n\n"
            "Syarat sa'i antara lain: dilakukan setelah tawaf, dimulai dari Safa dan berakhir di "
            "Marwah, serta 7 kali perjalanan penuh. Sa'i tidak disyaratkan suci dari hadats, "
            "namun lebih utama dalam keadaan suci.\n\n"
            "**Dalil:**\n"
            "\"Sesungguhnya Safa dan Marwah adalah sebagian dari syi'ar Allah.\" "
            "(QS. Al-Baqarah: 158)\n\n"
            "**Rujukan:**\n"
            "- Al-Majmu', Imam Nawawi\n"
            "- Kifayatul Akhyar, Imam Taqiyuddin\n\n"
            "**Kesimpulan:**\n"
            "Sa'i dilakukan 7 kali perjalanan dari Safa ke Marwah, dimulai dari Safa dan "
            "berakhir di Marwah, setelah tawaf."
        ),
        "category": "sai",
        "views": 0,
        "helpful": 0,
    },
    {
        "id": "qa_04",
        "question": "Apa saja larangan saat ihram dan apa konsekuensinya?",
        "answer": (
            "**Jawaban:**\n"
            "Larangan ihram terbagi menjadi beberapa kelompok. Bagi laki-laki: (1) Memakai pakaian "
            "berjahit yang membungkus anggota badan; (2) Menutup kepala dengan sesuatu yang melekat. "
            "Bagi wanita: menutup wajah (memakai cadar) dan memakai sarung tangan. "
            "Bagi keduanya: (1) Memakai wangi-wangian; (2) Memotong kuku; (3) Mencukur/mencabut "
            "rambut; (4) Membunuh binatang buruan darat; (5) Menikah atau menikahkan; "
            "(6) Berjima' (hubungan suami istri); (7) Pendahuluan jima' (ciuman, sentuhan syahwat).\n\n"
            "Konsekuensi melanggar larangan ihram bervariasi: jika berjima' sebelum tahallul pertama, "
            "umrah batal dan wajib membayar dam besar (menyembelih unta); jika melanggar larangan "
            "lain seperti memakai wangi-wangian atau memotong rambut, wajib membayar fidyah berupa "
            "puasa 3 hari, memberi makan 6 orang miskin, atau menyembelih kambing.\n\n"
            "**Dalil:**\n"
            "\"Barangsiapa di antara kamu ada yang sakit atau ada gangguan di kepalanya (lalu dia "
            "bercukur), maka wajiblah atasnya fidyah.\" (QS. Al-Baqarah: 196)\n\n"
            "**Rujukan:**\n"
            "- Fathul Qarib, Ibnu Qasim al-Ghazi\n"
            "- Al-Iqna', Syaikh al-Khatib asy-Syarbini\n\n"
            "**Kesimpulan:**\n"
            "Larangan ihram meliputi pakaian berjahit (pria), wangi-wangian, memotong kuku/rambut, "
            "dan berjima'. Pelanggar wajib membayar dam atau fidyah."
        ),
        "category": "ihram",
        "views": 0,
        "helpful": 0,
    },
    {
        "id": "qa_05",
        "question": "Bagaimana niat dan tata cara ihram untuk umrah?",
        "answer": (
            "**Jawaban:**\n"
            "Ihram adalah niat masuk ke dalam ibadah umrah yang dilakukan di miqat. Tata caranya: "
            "(1) Mandi sunnah (ghusl) sebelum ihram; (2) Memakai pakaian ihram - bagi laki-laki "
            "2 lembar kain putih tidak berjahit (izar dan rida'), bagi wanita pakaian biasa yang "
            "menutup aurat; (3) Shalat sunnah ihram 2 rakaat; (4) Berniat ihram umrah dengan "
            "mengucapkan 'Labbaika Allahumma 'Umratan' atau cukup dalam hati.\n\n"
            "Setelah berniat, jamaah disunnahkan membaca talbiyah: 'Labbaikallahumma labbaik, "
            "labbaika laa syariika laka labbaik, innal hamda wan ni'mata laka wal mulk, "
            "laa syariika lak'. Talbiyah terus dibaca hingga mulai tawaf di Masjidil Haram.\n\n"
            "Penting diketahui bahwa ihram harus dilakukan di miqat atau sebelumnya. Jika melewati "
            "miqat tanpa ihram, wajib kembali ke miqat atau membayar dam.\n\n"
            "**Dalil:**\n"
            "Hadits Rasulullah SAW: \"Sesungguhnya amalan itu tergantung pada niatnya.\" "
            "(HR. Bukhari dan Muslim)\n\n"
            "**Rujukan:**\n"
            "- Fathul Mu'in, Syaikh Zainuddin al-Malibari\n"
            "- Al-Majmu', Imam Nawawi\n\n"
            "**Kesimpulan:**\n"
            "Ihram dimulai dengan mandi, memakai pakaian ihram, shalat sunnah, lalu niat umrah "
            "di miqat. Talbiyah dibaca sampai mulai tawaf."
        ),
        "category": "ihram",
        "views": 0,
        "helpful": 0,
    },
    {
        "id": "qa_06",
        "question": "Doa apa saja yang dibaca saat tawaf?",
        "answer": (
            "**Jawaban:**\n"
            "Tidak ada doa khusus yang wajib dibaca saat tawaf, kecuali doa di antara Rukun Yamani "
            "dan Hajar Aswad: 'Rabbana atina fid-dunya hasanatan wa fil-akhirati hasanatan waqina "
            "'adzab an-nar'. Di luar itu, jamaah bebas berdoa dengan doa apa saja, baik dari "
            "Al-Quran, hadits, maupun doa pribadi dalam bahasa apa pun.\n\n"
            "Beberapa doa yang dianjurkan saat tawaf antara lain: (1) Saat memulai di Hajar Aswad: "
            "'Bismillahi Allahu Akbar'; (2) Memperbanyak istighfar dan shalawat; "
            "(3) Membaca Al-Quran juga termasuk dzikir yang utama saat tawaf. Yang terpenting "
            "adalah khusyuk dan merendahkan diri kepada Allah SWT.\n\n"
            "Perlu diperhatikan bahwa membaca doa dari buku panduan secara berjamaah dengan suara "
            "keras tidaklah disunnahkan. Lebih baik berdoa sendiri-sendiri dengan suara pelan.\n\n"
            "**Dalil:**\n"
            "\"Rabbana atina fid-dunya hasanatan wa fil-akhirati hasanatan waqina 'adzab an-nar.\" "
            "(QS. Al-Baqarah: 201)\n\n"
            "**Rujukan:**\n"
            "- Al-Adzkar, Imam Nawawi\n"
            "- Fathul Bari, Ibnu Hajar al-Asqalani\n\n"
            "**Kesimpulan:**\n"
            "Saat tawaf, berdoa bebas dengan doa apa saja. Doa wajib hanya antara Rukun Yamani "
            "dan Hajar Aswad: 'Rabbana atina fid-dunya hasanatan...'."
        ),
        "category": "doa",
        "views": 0,
        "helpful": 0,
    },
    {
        "id": "qa_07",
        "question": "Doa apa yang dibaca saat sa'i antara Safa dan Marwah?",
        "answer": (
            "**Jawaban:**\n"
            "Saat naik ke bukit Safa untuk pertama kali, disunnahkan menghadap Ka'bah dan membaca: "
            "'Innash-Shafa wal-Marwata min sya'a'irillah, abda'u bima bada'allahu bihi' "
            "(Sesungguhnya Safa dan Marwah termasuk syi'ar Allah, aku memulai dengan apa yang "
            "Allah mulai). Kemudian bertakbir 3 kali dan berdoa.\n\n"
            "Di atas Safa dan Marwah, disunnahkan berdoa: 'La ilaha illallahu wahdahu la syarika "
            "lah, lahul mulku wa lahul hamdu wa huwa 'ala kulli syai'in qadir. La ilaha illallahu "
            "wahdahu, anjaza wa'dahu, wa nashara 'abdahu, wa hazamal ahzaba wahdahu'. "
            "Doa ini dibaca 3 kali di setiap bukit.\n\n"
            "Di antara Safa dan Marwah, jamaah bebas berdoa dengan doa apa saja dan memperbanyak "
            "dzikir. Tidak ada doa khusus yang diwajibkan selama perjalanan sa'i.\n\n"
            "**Dalil:**\n"
            "\"Sesungguhnya Safa dan Marwah adalah sebagian dari syi'ar Allah. Maka barangsiapa "
            "yang beribadah haji ke Baitullah ataupun berumrah, maka tidak ada dosa baginya "
            "mengerjakan sa'i antara keduanya.\" (QS. Al-Baqarah: 158)\n\n"
            "**Rujukan:**\n"
            "- Al-Adzkar, Imam Nawawi\n"
            "- Shahih Muslim, kitab al-Hajj\n\n"
            "**Kesimpulan:**\n"
            "Di Safa dan Marwah baca doa 'La ilaha illallahu wahdahu...' 3 kali. "
            "Di antara keduanya, bebas berdoa dan berdzikir."
        ),
        "category": "doa",
        "views": 0,
        "helpful": 0,
    },
    {
        "id": "qa_08",
        "question": "Bagaimana hukum wanita haid atau nifas saat umrah?",
        "answer": (
            "**Jawaban:**\n"
            "Wanita yang sedang haid atau nifas tetap boleh melaksanakan umrah, namun tidak boleh "
            "melakukan tawaf sampai suci. Semua amalan umrah lainnya tetap boleh dilakukan: "
            "ihram, sa'i (menurut qaul mu'tamad Syafi'iyah sa'i harus setelah tawaf), "
            "dan tahallul. Jika sudah terlanjur ihram lalu haid, maka tetap menunggu sampai suci "
            "untuk kemudian tawaf.\n\n"
            "Langkah yang disarankan: (1) Tetap ihram dari miqat seperti biasa; "
            "(2) Jika haid sebelum tawaf, tunggu hingga suci, mandi, lalu tawaf; "
            "(3) Jika waktu tidak memungkinkan (misal jadwal pesawat), konsultasikan dengan "
            "muthawwif atau ulama tentang pilihan yang ada; (4) Selama menunggu, tetap "
            "memperbanyak dzikir, doa, dan istighfar.\n\n"
            "Wanita haid boleh duduk dan berdoa di area sekitar Masjidil Haram (di luar masjid), "
            "membaca dzikir dan shalawat, namun tidak boleh masuk ke dalam masjid.\n\n"
            "**Dalil:**\n"
            "Hadits Aisyah ra.: Rasulullah SAW bersabda kepadanya saat haid di Sarif: "
            "\"Lakukanlah apa yang dilakukan oleh orang yang berhaji, kecuali jangan tawaf "
            "di Baitullah sampai engkau suci.\" (HR. Bukhari dan Muslim)\n\n"
            "**Rujukan:**\n"
            "- Al-Majmu', Imam Nawawi\n"
            "- Mughni al-Muhtaj, Syaikh al-Khatib asy-Syarbini\n\n"
            "**Kesimpulan:**\n"
            "Wanita haid/nifas boleh ihram dan umrah, tetapi harus menunggu suci "
            "untuk melakukan tawaf. Amalan lain tetap boleh dilakukan."
        ),
        "category": "umum",
        "views": 0,
        "helpful": 0,
    },
    {
        "id": "qa_09",
        "question": "Apakah anak-anak boleh umrah dan bagaimana tata caranya?",
        "answer": (
            "**Jawaban:**\n"
            "Anak-anak boleh melaksanakan umrah dan umrahnya sah, namun tidak menggugurkan "
            "kewajiban umrah setelah baligh. Jika anak sudah mumayyiz (sekitar 7 tahun ke atas), "
            "ia melakukan sendiri semua amalan umrah dengan bimbingan orang tua. "
            "Jika belum mumayyiz, maka walinya yang berniat atas namanya.\n\n"
            "Tata cara umrah anak-anak: (1) Wali atau orang tua memandikan anak dan memakaikan "
            "pakaian ihram; (2) Wali berniat ihram atas nama anak yang belum mumayyiz; "
            "(3) Anak dibawa tawaf - jika belum bisa jalan, digendong; (4) Demikian juga sa'i; "
            "(5) Rambut anak dicukur atau dipotong untuk tahallul.\n\n"
            "Pahala umrah anak-anak diberikan kepada orang tuanya yang membimbing. Orang tua "
            "mendapat pahala tambahan karena mengajarkan ibadah sejak dini.\n\n"
            "**Dalil:**\n"
            "Hadits Ibnu Abbas ra.: Seorang wanita mengangkat anaknya dan bertanya, \"Apakah "
            "anak ini boleh berhaji?\" Rasulullah SAW menjawab, \"Ya, dan bagimu pahala.\" "
            "(HR. Muslim)\n\n"
            "**Rujukan:**\n"
            "- Al-Majmu', Imam Nawawi\n"
            "- Fathul Mu'in, Syaikh Zainuddin al-Malibari\n\n"
            "**Kesimpulan:**\n"
            "Anak-anak boleh umrah, tetapi tidak menggugurkan kewajiban setelah baligh. "
            "Anak mumayyiz beribadah sendiri, anak kecil diwakili walinya."
        ),
        "category": "umum",
        "views": 0,
        "helpful": 0,
    },
    {
        "id": "qa_10",
        "question": "Apa perbedaan antara umrah dan haji?",
        "answer": (
            "**Jawaban:**\n"
            "Perbedaan utama antara umrah dan haji terletak pada amalan, waktu, dan hukumnya. "
            "Haji hanya bisa dilaksanakan pada bulan Dzulhijjah (8-13 Dzulhijjah) dan merupakan "
            "rukun Islam kelima yang wajib sekali seumur hidup bagi yang mampu. Umrah bisa "
            "dilaksanakan kapan saja sepanjang tahun dan hukumnya wajib sekali seumur hidup "
            "menurut madzhab Syafi'i.\n\n"
            "Rukun haji lebih banyak: ihram, wuquf di Arafah, tawaf ifadhah, sa'i, tahallul, "
            "dan tertib. Sedangkan rukun umrah hanya 4: ihram, tawaf, sa'i, dan tahallul. "
            "Haji juga memiliki wajib tambahan: bermalam di Muzdalifah, melempar jumrah, "
            "bermalam di Mina, dan tawaf wada'. Umrah tidak memiliki wuquf, melempar jumrah, "
            "atau bermalam di Mina dan Muzdalifah.\n\n"
            "**Dalil:**\n"
            "\"Mengerjakan haji adalah kewajiban manusia terhadap Allah, yaitu (bagi) orang "
            "yang sanggup mengadakan perjalanan ke Baitullah.\" (QS. Ali Imran: 97)\n\n"
            "**Rujukan:**\n"
            "- Fathul Qarib, Ibnu Qasim al-Ghazi\n"
            "- Al-Fiqh al-Islami wa Adillatuhu, Wahbah az-Zuhaili\n\n"
            "**Kesimpulan:**\n"
            "Haji waktunya khusus (Dzulhijjah) dengan lebih banyak amalan (wuquf, jumrah). "
            "Umrah bisa kapan saja dengan 4 rukun utama."
        ),
        "category": "umum",
        "views": 0,
        "helpful": 0,
    },
    {
        "id": "qa_11",
        "question": "Kapan waktu terbaik untuk melaksanakan umrah?",
        "answer": (
            "**Jawaban:**\n"
            "Umrah bisa dilaksanakan kapan saja sepanjang tahun kecuali pada hari Arafah (9 "
            "Dzulhijjah) dan hari Tasyrik (11-13 Dzulhijjah) bagi yang sedang melaksanakan haji. "
            "Namun ada beberapa waktu yang lebih utama: (1) Bulan Ramadhan - Rasulullah SAW "
            "bersabda bahwa umrah di bulan Ramadhan setara dengan pahala haji; (2) Bulan "
            "Dzulqa'dah dan Syawal; (3) Di luar musim haji untuk kenyamanan dan menghindari "
            "kepadatan.\n\n"
            "Dari segi praktis, banyak jamaah Indonesia memilih bulan-bulan di luar musim haji "
            "(Muharram hingga Sya'ban) karena cuaca lebih bersahabat dan harga lebih terjangkau. "
            "Musim dingin (November-Februari) juga nyaman karena suhu di Makkah tidak terlalu "
            "panas. Hindari puncak musim liburan untuk mendapatkan harga yang lebih baik.\n\n"
            "**Dalil:**\n"
            "Hadits Rasulullah SAW: \"Umrah di bulan Ramadhan sebanding dengan haji\" - "
            "dalam riwayat lain \"sebanding dengan haji bersamaku.\" "
            "(HR. Bukhari dan Muslim)\n\n"
            "**Rujukan:**\n"
            "- Shahih Bukhari, kitab al-Umrah\n"
            "- Al-Majmu', Imam Nawawi\n\n"
            "**Kesimpulan:**\n"
            "Waktu terbaik umrah adalah bulan Ramadhan (pahala terbesar). "
            "Secara praktis, pilih di luar musim haji untuk kenyamanan dan harga terjangkau."
        ),
        "category": "umum",
        "views": 0,
        "helpful": 0,
    },
    {
        "id": "qa_12",
        "question": "Apa itu miqat dan apa saja jenisnya?",
        "answer": (
            "**Jawaban:**\n"
            "Miqat adalah batas tempat (miqat makani) atau batas waktu (miqat zamani) untuk "
            "memulai ihram. Miqat makani ada 5 yang ditetapkan Rasulullah SAW: "
            "(1) Dzulhulaifah (Bir Ali) untuk penduduk Madinah - ini miqat terjauh sekitar 450 km "
            "dari Makkah; (2) Al-Juhfah (dekat Rabigh) untuk penduduk Syam, Mesir, dan Maghrib; "
            "(3) Qarnul Manazil (as-Sail al-Kabir) untuk penduduk Najd; "
            "(4) Yalamlam (Sa'diyah) untuk penduduk Yaman dan Indonesia (jika via laut); "
            "(5) Dzatu Irq untuk penduduk Iraq dan timur.\n\n"
            "Bagi jamaah Indonesia yang terbang langsung ke Jeddah, miqatnya adalah saat pesawat "
            "melewati garis sejajar salah satu miqat di atas (biasanya sejajar Yalamlam atau "
            "Qarnul Manazil). Banyak jamaah memilih ihram di pesawat sebelum melewati miqat. "
            "Jika transit di Madinah dulu, miqatnya adalah Dzulhulaifah (Bir Ali).\n\n"
            "**Dalil:**\n"
            "Hadits Ibnu Abbas ra.: Rasulullah SAW menetapkan miqat bagi penduduk Madinah "
            "di Dzulhulaifah, bagi penduduk Syam di al-Juhfah... (HR. Bukhari dan Muslim)\n\n"
            "**Rujukan:**\n"
            "- Shahih Bukhari, kitab al-Hajj\n"
            "- Al-Majmu', Imam Nawawi\n\n"
            "**Kesimpulan:**\n"
            "Ada 5 miqat makani yang ditetapkan Nabi SAW. Jamaah Indonesia biasanya "
            "ihram di Bir Ali (via Madinah) atau di pesawat (via Jeddah langsung)."
        ),
        "category": "ihram",
        "views": 0,
        "helpful": 0,
    },
    {
        "id": "qa_13",
        "question": "Apa yang dimaksud dam dan kapan wajib membayarnya?",
        "answer": (
            "**Jawaban:**\n"
            "Dam secara bahasa artinya 'darah', dalam istilah fiqih berarti denda berupa "
            "penyembelihan hewan karena meninggalkan kewajiban atau melanggar larangan dalam "
            "ihram. Ada beberapa jenis dam: (1) Dam tartib dan ta'dil - untuk pelanggaran "
            "seperti memakai wangi-wangian, memotong rambut/kuku, berupa menyembelih kambing "
            "ATAU puasa 3 hari ATAU memberi makan 6 orang miskin; (2) Dam besar (badanah) - "
            "menyembelih unta karena berjima' sebelum tahallul; (3) Dam meninggalkan wajib - "
            "menyembelih kambing karena tidak ihram dari miqat.\n\n"
            "Dam wajib dibayar dalam beberapa kasus: meninggalkan salah satu wajib umrah (seperti "
            "melewati miqat tanpa ihram), melanggar larangan ihram (memakai wangi-wangian, "
            "memotong rambut, dll), dan berjima' saat ihram. Hewan dam disembelih di tanah "
            "Haram (Makkah) dan dagingnya dibagikan kepada fakir miskin.\n\n"
            "**Dalil:**\n"
            "\"Barangsiapa di antara kamu ada yang sakit atau ada gangguan di kepalanya "
            "(lalu dia bercukur), maka wajib atasnya fidyah, yaitu berpuasa, bersedekah, "
            "atau menyembelih kurban.\" (QS. Al-Baqarah: 196)\n\n"
            "**Rujukan:**\n"
            "- Al-Majmu', Imam Nawawi\n"
            "- Fathul Qarib, Ibnu Qasim al-Ghazi\n\n"
            "**Kesimpulan:**\n"
            "Dam adalah denda penyembelihan hewan karena pelanggaran ihram atau "
            "meninggalkan wajib umrah. Disembelih di Makkah untuk fakir miskin."
        ),
        "category": "ihram",
        "views": 0,
        "helpful": 0,
    },
    {
        "id": "qa_14",
        "question": "Doa apa yang dibaca saat pertama kali melihat Ka'bah?",
        "answer": (
            "**Jawaban:**\n"
            "Saat pertama kali melihat Ka'bah, disunnahkan mengangkat kedua tangan dan berdoa. "
            "Momen ini adalah saat yang sangat mustajab untuk berdoa. Doa yang diriwayatkan "
            "antara lain: 'Allahumma zid hadza al-baita tasyrifan wa ta'zhiman wa takriman "
            "wa mahabatan, wa zid man syarrafahu wa karramahu mimman hajjahu aw i'tamarahu "
            "tasyrifan wa takriman wa ta'zhiman wa birran' (Ya Allah, tambahkanlah kemuliaan, "
            "penghormatan, dan kecintaan pada rumah ini).\n\n"
            "Selain doa di atas, jamaah juga dianjurkan berdoa dengan doa-doa pribadi, "
            "memohon hajat yang paling penting, dan mengucapkan kalimat tauhid: "
            "'La ilaha illallahu wahdahu la syarika lah'. Rasulullah SAW mengajarkan bahwa "
            "doa tidak ditolak saat pertama melihat Ka'bah, maka manfaatkanlah momen ini.\n\n"
            "**Dalil:**\n"
            "Hadits riwayat al-Baihaqi tentang mustajabnya doa saat melihat Ka'bah: "
            "\"Terbuka pintu-pintu langit dan dikabulkan doa saat melihat Baitullah.\"\n\n"
            "**Rujukan:**\n"
            "- Al-Adzkar, Imam Nawawi\n"
            "- Ithaf as-Sadat al-Muttaqin, Imam az-Zabidi\n\n"
            "**Kesimpulan:**\n"
            "Saat pertama melihat Ka'bah, angkat tangan dan berdoa apa saja. "
            "Momen ini sangat mustajab - perbanyak doa pribadi dan kalimat tauhid."
        ),
        "category": "doa",
        "views": 0,
        "helpful": 0,
    },
    {
        "id": "qa_15",
        "question": "Apakah boleh umrah berkali-kali dalam satu perjalanan?",
        "answer": (
            "**Jawaban:**\n"
            "Menurut madzhab Syafi'i, boleh melaksanakan umrah berkali-kali dalam satu perjalanan "
            "dan hukumnya sunnah. Caranya adalah setelah selesai satu umrah, jamaah keluar ke "
            "tanah halal (biasanya ke Masjid Aisyah / Tan'im yang terdekat, sekitar 7 km dari "
            "Masjidil Haram), lalu berihram kembali untuk umrah berikutnya.\n\n"
            "Beberapa ulama Syafi'iyah mengatakan bahwa memperbanyak tawaf sunnah lebih utama "
            "daripada memperbanyak umrah, karena tawaf hanya bisa dilakukan di Makkah, sedangkan "
            "ihram bisa dilakukan di mana saja. Namun pendapat mu'tamad (yang dipegang) dalam "
            "madzhab Syafi'i adalah bahwa umrah berulang tetap disunnahkan.\n\n"
            "Rasulullah SAW sendiri melaksanakan 4 kali umrah dalam hidupnya, dan Aisyah ra. "
            "diminta beliau untuk umrah dari Tan'im setelah haji Wada'.\n\n"
            "**Dalil:**\n"
            "Hadits Rasulullah SAW: \"Umrah ke umrah berikutnya adalah penghapus dosa "
            "di antara keduanya.\" (HR. Bukhari dan Muslim)\n\n"
            "**Rujukan:**\n"
            "- Al-Majmu', Imam Nawawi\n"
            "- Tuhfatul Muhtaj, Ibnu Hajar al-Haitami\n\n"
            "**Kesimpulan:**\n"
            "Boleh dan sunnah umrah berkali-kali. Keluar ke Tan'im untuk ihram ulang. "
            "Namun sebagian ulama mengatakan tawaf sunnah lebih utama."
        ),
        "category": "umum",
        "views": 0,
        "helpful": 0,
    },
    {
        "id": "qa_16",
        "question": "Apa hukum tawaf wada' untuk umrah?",
        "answer": (
            "**Jawaban:**\n"
            "Tawaf wada' (tawaf perpisahan) untuk umrah hukumnya sunnah menurut madzhab Syafi'i, "
            "bukan wajib. Ini berbeda dengan haji, di mana tawaf wada' hukumnya wajib. "
            "Jadi jika jamaah umrah meninggalkan Makkah tanpa tawaf wada', umrahnya tetap sah "
            "dan tidak wajib membayar dam.\n\n"
            "Meskipun hukumnya sunnah, sangat dianjurkan untuk melakukan tawaf wada' sebelum "
            "meninggalkan Makkah sebagai bentuk penghormatan terakhir kepada Baitullah. "
            "Banyak jamaah Indonesia melakukan tawaf wada' di malam terakhir sebelum berangkat "
            "ke Madinah atau ke bandara.\n\n"
            "**Dalil:**\n"
            "Hadits Ibnu Abbas ra.: \"Tidak boleh seseorang pergi (dari Makkah setelah haji) "
            "sampai akhir urusannya adalah tawaf di Baitullah.\" (HR. Muslim) - "
            "Mayoritas ulama Syafi'iyah membatasi wajibnya pada haji saja.\n\n"
            "**Rujukan:**\n"
            "- Al-Majmu', Imam Nawawi\n"
            "- Mughni al-Muhtaj, asy-Syarbini\n\n"
            "**Kesimpulan:**\n"
            "Tawaf wada' untuk umrah hukumnya sunnah (bukan wajib). Tetap dianjurkan "
            "sebagai penghormatan terakhir sebelum meninggalkan Makkah."
        ),
        "category": "tawaf",
        "views": 0,
        "helpful": 0,
    },
    {
        "id": "qa_17",
        "question": "Apa yang membatalkan tawaf dan bagaimana mengulangnya?",
        "answer": (
            "**Jawaban:**\n"
            "Tawaf batal jika: (1) Berhadats (batal wudhu) di tengah tawaf - wajib berwudhu "
            "dulu lalu mengulang putaran yang terputus dari awal putaran tersebut; "
            "(2) Terbuka aurat yang wajib ditutup; (3) Melewati Hijr Ismail (masuk ke dalamnya) "
            "karena Hijr Ismail termasuk bagian Ka'bah, sehingga putaran tersebut tidak "
            "dianggap mengelilingi Ka'bah secara penuh.\n\n"
            "Jika ragu tentang jumlah putaran (misalnya lupa sudah 5 atau 6 putaran), "
            "maka ambil bilangan yang lebih sedikit (yakin) dan lanjutkan tawaf. Lebih baik "
            "menghitung dengan alat bantu seperti tasbih digital atau aplikasi penghitung.\n\n"
            "Jika tawaf terputus karena shalat fardhu (iqamah dikumandangkan), maka boleh "
            "shalat dulu kemudian melanjutkan tawaf dari putaran yang terputus.\n\n"
            "**Dalil:**\n"
            "Hadits Aisyah ra.: Rasulullah SAW bersabda, \"Tawaf di Baitullah adalah "
            "shalat, kecuali Allah memperbolehkan berbicara di dalamnya.\" "
            "(HR. an-Nasa'i dan at-Tirmidzi)\n\n"
            "**Rujukan:**\n"
            "- Al-Majmu', Imam Nawawi\n"
            "- Fathul Mu'in, Syaikh Zainuddin al-Malibari\n\n"
            "**Kesimpulan:**\n"
            "Tawaf batal karena hadats, aurat terbuka, atau melewati Hijr Ismail. "
            "Jika berhadats, wudhu dulu lalu ulang putaran dari awal."
        ),
        "category": "tawaf",
        "views": 0,
        "helpful": 0,
    },
    {
        "id": "qa_18",
        "question": "Bagaimana doa dan dzikir setelah shalat di Maqam Ibrahim?",
        "answer": (
            "**Jawaban:**\n"
            "Setelah menyelesaikan 7 putaran tawaf, disunnahkan shalat 2 rakaat di belakang "
            "Maqam Ibrahim. Pada rakaat pertama disunnahkan membaca Surah Al-Kafirun setelah "
            "Al-Fatihah, dan pada rakaat kedua membaca Surah Al-Ikhlas. Setelah salam, "
            "disunnahkan berdoa dengan khusyuk.\n\n"
            "Doa yang dianjurkan setelah shalat di Maqam Ibrahim antara lain: memohon "
            "ampunan dosa, memohon keberkahan, dan doa-doa pribadi. Kemudian disunnahkan "
            "minum air Zamzam sambil berdoa: 'Allahumma inni as'aluka 'ilman nafi'an, "
            "wa rizqan wasi'an, wa syifa'an min kulli da'in' (Ya Allah, aku memohon ilmu "
            "yang bermanfaat, rezeki yang luas, dan kesembuhan dari segala penyakit).\n\n"
            "Jika area Maqam Ibrahim terlalu padat, boleh shalat di mana saja di dalam "
            "Masjidil Haram. Kesempurnaan shalat di belakang Maqam Ibrahim adalah sunnah, "
            "bukan wajib.\n\n"
            "**Dalil:**\n"
            "\"Dan jadikanlah sebagian maqam Ibrahim sebagai tempat shalat.\" "
            "(QS. Al-Baqarah: 125)\n\n"
            "**Rujukan:**\n"
            "- Al-Adzkar, Imam Nawawi\n"
            "- Shahih Muslim, kitab al-Hajj\n\n"
            "**Kesimpulan:**\n"
            "Shalat 2 rakaat di Maqam Ibrahim setelah tawaf, baca Al-Kafirun dan Al-Ikhlas. "
            "Lalu minum Zamzam sambil berdoa."
        ),
        "category": "doa",
        "views": 0,
        "helpful": 0,
    },
]

# Fallback answers for when AI service is unavailable
FALLBACK_ANSWERS = {
    "rukun umrah": """**Jawaban:**
Rukun umrah ada empat menurut madzhab Syafi'i, yaitu: (1) Ihram, yakni berniat masuk ke dalam ibadah umrah dari miqat; (2) Tawaf mengelilingi Ka'bah sebanyak 7 putaran; (3) Sa'i antara bukit Safa dan Marwah sebanyak 7 kali; (4) Tahallul dengan mencukur atau memotong rambut.

Keempat rukun ini wajib dilakukan secara berurutan. Jika salah satu rukun ditinggalkan, maka umrah tidak sah dan harus diulang.

**Dalil:**
"Dan sempurnakanlah ibadah haji dan umrah karena Allah." (QS. Al-Baqarah: 196)

Hadits Rasulullah SAW tentang tata cara umrah diriwayatkan oleh Jabir bin Abdullah ra. dalam Shahih Muslim.

**Rujukan:**
- Al-Majmu' Syarh al-Muhadzdzab, Imam Nawawi
- Fathul Qarib, Ibnu Qasim al-Ghazi
- Kifayatul Akhyar, Imam Taqiyuddin

**Kesimpulan:**
Rukun umrah ada empat: Ihram, Tawaf, Sa'i, dan Tahallul. Semuanya wajib dilakukan berurutan agar umrah sah.""",

    "default": """**Jawaban:**
Terima kasih atas pertanyaan Anda. Ini adalah pertanyaan yang baik terkait fiqih umrah.

Untuk memberikan jawaban yang akurat dan lengkap dengan dalil yang tepat, layanan AI sedang tidak tersedia saat ini. Silakan coba beberapa saat lagi.

**Dalil:**
"Maka bertanyalah kepada orang yang mempunyai pengetahuan jika kamu tidak mengetahui." (QS. An-Nahl: 43)

**Rujukan:**
Konsultasikan pertanyaan Anda dengan ustadz atau ulama setempat.

**Kesimpulan:**
Pastikan API key sudah dikonfigurasi (GROQ_API_KEY) untuk mengaktifkan layanan Ustadz AI secara penuh.""",
}

# =============================================================================
# STYLING
# =============================================================================

TANYA_USTADZ_CSS = """
/* Page-specific styles for Tanya Ustadz */
.ustadz-hero {
    background: linear-gradient(135deg, #0d1b0d 0%, #1a3a1a 50%, #0d2b0d 100%);
    padding: 2.5rem 2rem;
    border-radius: 20px;
    text-align: center;
    margin-bottom: 1.5rem;
    border: 1px solid rgba(74, 222, 128, 0.3);
    position: relative;
    overflow: hidden;
}

.ustadz-hero::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: radial-gradient(circle at 50% 0%, rgba(74, 222, 128, 0.08) 0%, transparent 60%);
    pointer-events: none;
}

.ustadz-hero h1 {
    color: #4ade80;
    margin: 0 0 0.3rem 0;
    font-size: 2.2rem;
    font-family: 'Amiri', serif;
    position: relative;
}

.ustadz-hero .subtitle {
    color: #94a3b8;
    font-size: 1rem;
    margin-bottom: 1rem;
    position: relative;
}

.ustadz-hero .bismillah {
    color: #4ade80;
    font-family: 'Amiri', serif;
    font-size: 1.6rem;
    margin-bottom: 0.5rem;
    opacity: 0.85;
    position: relative;
}

.ustadz-hero .disclaimer {
    background: rgba(74, 222, 128, 0.08);
    border: 1px solid rgba(74, 222, 128, 0.2);
    border-radius: 10px;
    padding: 0.75rem 1rem;
    color: #94a3b8;
    font-size: 0.82rem;
    margin-top: 1rem;
    position: relative;
}

.category-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    justify-content: center;
    margin: 1rem 0;
}

.category-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.4rem 1rem;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    border: 1px solid #333;
    background: #1a1a2e;
    color: #94a3b8;
}

.category-pill.active {
    background: linear-gradient(135deg, #166534 0%, #15803d 100%);
    border-color: #4ade80;
    color: #fff;
    box-shadow: 0 0 12px rgba(74, 222, 128, 0.2);
}

.category-pill:hover {
    border-color: #4ade80;
    color: #4ade80;
}

.qa-card {
    background: linear-gradient(145deg, #111827 0%, #1a1a2e 100%);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    border-left: 4px solid #4ade80;
    transition: transform 0.2s;
}

.qa-card:hover {
    transform: translateY(-1px);
}

.qa-card .qa-question {
    color: #e2e8f0;
    font-size: 1.05rem;
    font-weight: 600;
    margin-bottom: 0.8rem;
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
}

.qa-card .qa-question .q-icon {
    color: #4ade80;
    font-size: 1.1rem;
    flex-shrink: 0;
    margin-top: 0.1rem;
}

.qa-card .qa-answer {
    color: #cbd5e1;
    font-size: 0.93rem;
    line-height: 1.7;
    padding-left: 0.5rem;
}

.qa-card .qa-answer strong {
    color: #4ade80;
}

.qa-card .qa-meta {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 0.8rem;
    padding-top: 0.6rem;
    border-top: 1px solid rgba(74, 222, 128, 0.1);
}

.qa-card .qa-meta .qa-category {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.2rem 0.6rem;
    border-radius: 12px;
    font-size: 0.75rem;
    background: rgba(74, 222, 128, 0.1);
    color: #4ade80;
    border: 1px solid rgba(74, 222, 128, 0.2);
}

.qa-card .qa-meta .qa-time {
    color: #64748b;
    font-size: 0.78rem;
}

.popular-card {
    background: linear-gradient(145deg, #111827 0%, #1e1e36 100%);
    border-radius: 12px;
    padding: 0.85rem 1rem;
    margin-bottom: 0.6rem;
    border: 1px solid #2d2d4a;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    gap: 0.6rem;
}

.popular-card:hover {
    border-color: #4ade80;
    background: linear-gradient(145deg, #162016 0%, #1a2a1a 100%);
    transform: translateX(4px);
}

.popular-card .pop-icon {
    font-size: 1.1rem;
    flex-shrink: 0;
}

.popular-card .pop-text {
    color: #e2e8f0;
    font-size: 0.88rem;
}

.popular-card .pop-cat {
    margin-left: auto;
    flex-shrink: 0;
    padding: 0.15rem 0.5rem;
    border-radius: 10px;
    font-size: 0.7rem;
    background: rgba(74, 222, 128, 0.1);
    color: #4ade80;
}

.stats-row {
    display: flex;
    justify-content: center;
    gap: 2rem;
    margin: 1rem 0;
}

.stat-item {
    text-align: center;
}

.stat-item .stat-num {
    color: #4ade80;
    font-size: 1.6rem;
    font-weight: 700;
}

.stat-item .stat-label {
    color: #64748b;
    font-size: 0.78rem;
}

.section-title {
    color: #e2e8f0;
    font-size: 1.15rem;
    font-weight: 600;
    margin: 1.5rem 0 0.8rem 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.empty-state {
    text-align: center;
    padding: 2.5rem 1rem;
    color: #64748b;
}

.empty-state .empty-icon {
    font-size: 3rem;
    margin-bottom: 0.5rem;
    opacity: 0.5;
}

.empty-state .empty-text {
    font-size: 0.95rem;
    color: #94a3b8;
}

.spinner-text {
    text-align: center;
    padding: 1.5rem;
    color: #4ade80;
    font-size: 0.95rem;
}

/* --- Q&A Database & Search Styles --- */

.qa-search-section {
    background: linear-gradient(145deg, #111827 0%, #1a1a2e 100%);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1.2rem;
    border: 1px solid #2d2d4a;
    position: relative;
}

.qa-search-section::before {
    content: '\\1F50D';
    position: absolute;
    top: 1.65rem;
    left: 1.2rem;
    font-size: 1.1rem;
    opacity: 0.5;
    pointer-events: none;
}

.qa-search-section .search-label {
    color: #e2e8f0;
    font-size: 1rem;
    font-weight: 600;
    margin-bottom: 0.6rem;
}

.qa-db-card {
    background: linear-gradient(145deg, #111827 0%, #1a1a2e 100%);
    border-radius: 16px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.8rem;
    border-left: 4px solid #d4af37;
    transition: transform 0.2s, box-shadow 0.2s;
}

.qa-db-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(212, 175, 55, 0.1);
}

.qa-db-card .qa-db-question {
    color: #e2e8f0;
    font-size: 1.02rem;
    font-weight: 600;
    margin-bottom: 0.4rem;
}

.qa-db-card .qa-db-meta {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    margin-top: 0.5rem;
    flex-wrap: wrap;
}

.qa-category-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.2rem 0.65rem;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 500;
}

.qa-category-badge.cat-tawaf {
    background: rgba(139, 92, 246, 0.15);
    color: #a78bfa;
    border: 1px solid rgba(139, 92, 246, 0.3);
}

.qa-category-badge.cat-sai {
    background: rgba(59, 130, 246, 0.15);
    color: #60a5fa;
    border: 1px solid rgba(59, 130, 246, 0.3);
}

.qa-category-badge.cat-ihram {
    background: rgba(236, 72, 153, 0.15);
    color: #f472b6;
    border: 1px solid rgba(236, 72, 153, 0.3);
}

.qa-category-badge.cat-doa {
    background: rgba(212, 175, 55, 0.15);
    color: #d4af37;
    border: 1px solid rgba(212, 175, 55, 0.3);
}

.qa-category-badge.cat-umum {
    background: rgba(74, 222, 128, 0.15);
    color: #4ade80;
    border: 1px solid rgba(74, 222, 128, 0.3);
}

.qa-views-count {
    color: #64748b;
    font-size: 0.78rem;
    display: inline-flex;
    align-items: center;
    gap: 0.2rem;
}

.qa-helpful-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.25rem 0.6rem;
    border-radius: 8px;
    font-size: 0.78rem;
    border: 1px solid #333;
    background: rgba(30, 30, 50, 0.6);
    color: #94a3b8;
    cursor: pointer;
    transition: all 0.2s;
}

.qa-helpful-btn:hover {
    border-color: #4ade80;
    color: #4ade80;
    background: rgba(74, 222, 128, 0.08);
}

.qa-helpful-count {
    color: #4ade80;
    font-weight: 600;
}

.qa-history-card {
    background: linear-gradient(145deg, #111827 0%, #1a1a2e 100%);
    border-radius: 14px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.7rem;
    border-left: 3px solid #3b82f6;
    transition: transform 0.15s;
}

.qa-history-card:hover {
    transform: translateX(3px);
}

.qa-history-card .history-q {
    color: #e2e8f0;
    font-size: 0.95rem;
    font-weight: 500;
    margin-bottom: 0.3rem;
}

.qa-history-card .history-time {
    color: #64748b;
    font-size: 0.75rem;
}

.qa-sort-info {
    color: #64748b;
    font-size: 0.82rem;
    margin-bottom: 0.8rem;
    display: flex;
    align-items: center;
    gap: 0.4rem;
}
"""

# =============================================================================
# SESSION STATE
# =============================================================================

def init_tanya_ustadz_state():
    """Initialize tanya ustadz session state."""
    if "tanya_history" not in st.session_state:
        st.session_state.tanya_history = []
    if "tanya_category" not in st.session_state:
        st.session_state.tanya_category = "semua"
    if "tanya_pending_question" not in st.session_state:
        st.session_state.tanya_pending_question = ""
    if "tanya_is_loading" not in st.session_state:
        st.session_state.tanya_is_loading = False
    # Q&A database view/helpful counters (keyed by qa id)
    if "qa_db_views" not in st.session_state:
        st.session_state.qa_db_views = {}
    if "qa_db_helpful" not in st.session_state:
        st.session_state.qa_db_helpful = {}
    # User's own Q&A history (asked questions + AI answers)
    if "ustadz_qa_history" not in st.session_state:
        st.session_state.ustadz_qa_history = []
    # Track which entries user already rated helpful
    if "qa_db_rated" not in st.session_state:
        st.session_state.qa_db_rated = set()


# =============================================================================
# AI SERVICE
# =============================================================================

def get_ai_answer(question: str, category: str) -> str:
    """Get AI answer for the given question using Groq service.

    Args:
        question: The user's fiqih question.
        category: The question category (tawaf, sai, ihram, doa, umum).

    Returns:
        The AI-generated answer string, or a fallback if unavailable.
    """
    category_info = CATEGORIES.get(category, CATEGORIES["umum"])
    category_label = category_info["label"]

    prompt_text = f"[Kategori: {category_label}]\n\nPertanyaan:\n{question}"

    response = ai_complete(prompt_text, system_prompt=USTADZ_SYSTEM_PROMPT, max_tokens=1500)

    if response:
        return response

    # Fallback: try to match a known answer
    q_lower = question.lower()
    if "rukun" in q_lower and "umrah" in q_lower:
        return FALLBACK_ANSWERS["rukun umrah"]

    return FALLBACK_ANSWERS["default"]


# =============================================================================
# GAMIFICATION
# =============================================================================

def _add_xp(amount: int, reason: str = ""):
    """Add XP — delegates to shared helper."""
    add_xp_safe(amount, reason)


# =============================================================================
# UI COMPONENTS
# =============================================================================

def render_hero():
    """Render hero section with disclaimer."""
    inject_css(HERO_CSS, CARD_CSS, EMPTY_STATE_CSS, TANYA_USTADZ_CSS)

    st.markdown("""
    <div class="ustadz-hero">
        <div class="bismillah">بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ</div>
        <h1>Tanya Ustadz AI</h1>
        <p class="subtitle">Tanya jawab seputar fiqih umrah berdasarkan madzhab Syafi'i</p>
        <div class="disclaimer">
            <strong>Catatan:</strong> Jawaban AI bersifat referensi edukatif.
            Konsultasikan dengan ustadz/ulama setempat untuk kasus spesifik Anda.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Stats row
    history = st.session_state.get("tanya_history", [])
    total_q = len(history)
    cats_used = len(set(entry.get("category", "umum") for entry in history)) if history else 0

    st.markdown(f"""
    <div class="stats-row">
        <div class="stat-item">
            <div class="stat-num">{total_q}</div>
            <div class="stat-label">Pertanyaan Dijawab</div>
        </div>
        <div class="stat-item">
            <div class="stat-num">{cats_used}</div>
            <div class="stat-label">Kategori Dijelajahi</div>
        </div>
        <div class="stat-item">
            <div class="stat-num">6</div>
            <div class="stat-label">Topik Tersedia</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_ask_form():
    """Render the question form with category selector and textarea."""
    st.markdown('<div class="section-title">💬 Ajukan Pertanyaan</div>', unsafe_allow_html=True)

    with st.container(border=True):
        # Category selector
        cat_options = list(CATEGORIES.keys())
        cat_labels = [f"{CATEGORIES[k]['icon']} {CATEGORIES[k]['label']}" for k in cat_options]

        current_cat = st.session_state.get("tanya_category", "semua")
        current_idx = cat_options.index(current_cat) if current_cat in cat_options else 0

        col_cat, col_spacer = st.columns([3, 1])
        with col_cat:
            selected_label = st.selectbox(
                "Kategori Pertanyaan",
                options=cat_labels,
                index=current_idx,
                label_visibility="collapsed",
                key="tanya_cat_select",
            )
            selected_cat = cat_options[cat_labels.index(selected_label)]
            st.session_state.tanya_category = selected_cat

        # Render category pills display (visual only)
        pills_html = ""
        for key, info in CATEGORIES.items():
            active_cls = "active" if key == selected_cat else ""
            pills_html += f'<span class="category-pill {active_cls}">{info["icon"]} {info["label"]}</span>'

        st.markdown(f'<div class="category-pills">{pills_html}</div>', unsafe_allow_html=True)

        # Question textarea
        pending = st.session_state.get("tanya_pending_question", "")
        question = st.text_area(
            "Tulis pertanyaan Anda",
            value=pending,
            height=100,
            placeholder="Contoh: Bagaimana tata cara tawaf yang benar menurut madzhab Syafi'i?",
            key="tanya_question_input",
        )

        # Submit
        col_submit, col_clear = st.columns([3, 1])

        with col_submit:
            submit = st.button(
                "Tanya Ustadz AI",
                type="primary",
                use_container_width=True,
                key="tanya_submit_btn",
                disabled=st.session_state.get("tanya_is_loading", False),
            )

        with col_clear:
            if st.button("Hapus", use_container_width=True, key="tanya_clear_btn"):
                st.session_state.tanya_pending_question = ""
                st.rerun()

        # Process submission
        if submit and question and question.strip():
            _process_question(question.strip(), selected_cat)


def _process_question(question: str, category: str):
    """Process a submitted question: call AI, store result, award XP."""
    st.session_state.tanya_is_loading = True

    skeleton_placeholder = st.empty()
    with skeleton_placeholder:
        st.markdown(SKELETON_CSS, unsafe_allow_html=True)
        render_skeleton(skeleton_type="text")
        render_skeleton(skeleton_type="cards", count=2)

    with st.spinner("Ustadz AI sedang menyiapkan jawaban..."):
        answer = get_ai_answer(question, category)

    skeleton_placeholder.empty()

    # Store in history (main display)
    entry = {
        "question": question,
        "answer": answer,
        "category": category,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    st.session_state.tanya_history.insert(0, entry)

    # Also store in persistent Q&A history (max 20 entries)
    qa_hist = st.session_state.get("ustadz_qa_history", [])
    qa_hist.insert(0, dict(entry))
    if len(qa_hist) > 20:
        qa_hist = qa_hist[:20]
    st.session_state.ustadz_qa_history = qa_hist

    # Clear pending question and loading state
    st.session_state.tanya_pending_question = ""
    st.session_state.tanya_is_loading = False

    # Gamification
    _add_xp(5, "Bertanya kepada Ustadz AI")

    # Track analytics
    try:
        from services.analytics import track_page
        track_page("tanya_ustadz_ask")
    except Exception:
        pass

    st.rerun()


def render_popular_questions():
    """Render popular pre-defined questions as clickable cards."""
    st.markdown('<div class="section-title">🔥 Pertanyaan Populer</div>', unsafe_allow_html=True)

    current_cat = st.session_state.get("tanya_category", "semua")

    # Filter by category
    if current_cat == "semua":
        filtered = POPULAR_QUESTIONS
    else:
        filtered = [pq for pq in POPULAR_QUESTIONS if pq["cat"] == current_cat]

    if not filtered:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">📭</div>
            <div class="empty-text">Belum ada pertanyaan populer untuk kategori ini.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Render as clickable buttons
    for i, pq in enumerate(filtered):
        cat_info = CATEGORIES.get(pq["cat"], CATEGORIES["umum"])
        cat_label = f'{cat_info["icon"]} {cat_info["label"]}'

        st.markdown(f"""
        <div class="popular-card">
            <span class="pop-icon">💡</span>
            <span class="pop-text">{pq['q']}</span>
            <span class="pop-cat">{cat_label}</span>
        </div>
        """, unsafe_allow_html=True)

        if st.button(
            f"Tanyakan: {pq['q'][:50]}...",
            key=f"popular_q_{i}",
            use_container_width=True,
            type="secondary",
        ):
            st.session_state.tanya_pending_question = pq["q"]
            st.session_state.tanya_category = pq["cat"]
            st.rerun()


def _fuzzy_match(query: str, text: str) -> bool:
    """Simple fuzzy matching: check if all query words appear in text (case-insensitive).

    Supports partial word matching so 'taw' matches 'tawaf', etc.
    """
    if not query or not query.strip():
        return True
    query_lower = query.lower().strip()
    text_lower = text.lower()
    words = query_lower.split()
    for word in words:
        if word not in text_lower:
            return False
    return True


def _get_qa_entry_views(qa_id: str) -> int:
    """Get the combined static + session view count for a QA entry."""
    # Static base from QA_DATABASE
    base_views = 0
    for entry in QA_DATABASE:
        if entry["id"] == qa_id:
            base_views = entry.get("views", 0)
            break
    session_views = st.session_state.get("qa_db_views", {}).get(qa_id, 0)
    return base_views + session_views


def _get_qa_entry_helpful(qa_id: str) -> int:
    """Get the combined static + session helpful count for a QA entry."""
    base_helpful = 0
    for entry in QA_DATABASE:
        if entry["id"] == qa_id:
            base_helpful = entry.get("helpful", 0)
            break
    session_helpful = st.session_state.get("qa_db_helpful", {}).get(qa_id, 0)
    return base_helpful + session_helpful


def _get_category_badge_html(category: str) -> str:
    """Return HTML for a colored category badge."""
    cat_info = CATEGORIES.get(category, CATEGORIES["umum"])
    css_class = f"cat-{category}" if category in ("tawaf", "sai", "ihram", "doa", "umum") else "cat-umum"
    return (
        f'<span class="qa-category-badge {css_class}">'
        f'{cat_info["icon"]} {cat_info["label"]}</span>'
    )


def render_qa_database():
    """Render the searchable Q&A fiqih database with category filter and helpful ratings."""
    st.markdown(
        '<div class="section-title"><span aria-hidden="true">📚</span> Database Fiqih Umrah</div>',
        unsafe_allow_html=True,
    )

    # --- Search box ---
    search_query = st.text_input(
        "Cari pertanyaan...",
        value="",
        placeholder="Ketik kata kunci, misal: tawaf, ihram, doa, haid...",
        key="qa_db_search_input",
    )

    # Award XP for searching (once per session per unique query)
    if search_query and search_query.strip():
        searched_set = st.session_state.get("_qa_searched_queries", set())
        query_key = search_query.strip().lower()
        if query_key not in searched_set:
            searched_set.add(query_key)
            st.session_state._qa_searched_queries = searched_set
            _add_xp(5, "Mencari di Database Fiqih")

    # --- Category filter ---
    cat_options_db = ["semua", "tawaf", "sai", "ihram", "doa", "umum"]
    cat_labels_db = [f"{CATEGORIES[k]['icon']} {CATEGORIES[k]['label']}" for k in cat_options_db]
    selected_cat_label = st.selectbox(
        "Filter Kategori",
        options=cat_labels_db,
        index=0,
        key="qa_db_cat_filter",
        label_visibility="collapsed",
    )
    selected_cat_db = cat_options_db[cat_labels_db.index(selected_cat_label)]

    # --- Sort ---
    col_sort, col_count = st.columns([2, 2])
    with col_sort:
        sort_mode = st.selectbox(
            "Urutkan",
            options=["Terpopuler", "Terbaru"],
            index=0,
            key="qa_db_sort",
            label_visibility="collapsed",
        )

    # --- Filter entries ---
    filtered_entries = []
    for entry in QA_DATABASE:
        # Category filter
        if selected_cat_db != "semua" and entry["category"] != selected_cat_db:
            continue
        # Search filter (fuzzy match on question + answer)
        if search_query and search_query.strip():
            combined_text = entry["question"] + " " + entry["answer"]
            if not _fuzzy_match(search_query, combined_text):
                continue
        filtered_entries.append(entry)

    # --- Sort entries ---
    if sort_mode == "Terpopuler":
        filtered_entries.sort(key=lambda e: _get_qa_entry_views(e["id"]), reverse=True)
    else:
        # "Terbaru" - reverse order of list (last entries are newest)
        filtered_entries = list(reversed(filtered_entries))

    with col_count:
        st.markdown(
            f'<div class="qa-sort-info">Menampilkan {len(filtered_entries)} dari '
            f'{len(QA_DATABASE)} pertanyaan</div>',
            unsafe_allow_html=True,
        )

    # --- Empty state ---
    if not filtered_entries:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon"><span aria-hidden="true">📭</span></div>
            <div class="empty-text">Tidak ditemukan pertanyaan yang cocok. Coba kata kunci lain.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # --- Render entries as expandable cards ---
    for entry in filtered_entries:
        qa_id = entry["id"]
        views = _get_qa_entry_views(qa_id)
        helpful = _get_qa_entry_helpful(qa_id)
        cat_badge = _get_category_badge_html(entry["category"])

        # Card header HTML
        st.markdown(f"""
        <div class="qa-db-card">
            <div class="qa-db-question"><span aria-hidden="true">&#10067;</span> {entry["question"]}</div>
            <div class="qa-db-meta">
                {cat_badge}
                <span class="qa-views-count"><span aria-hidden="true">&#128065;</span> {views} dilihat</span>
                <span class="qa-views-count"><span aria-hidden="true">&#128077;</span> {helpful} terbantu</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander(f"Lihat jawaban: {entry['question'][:60]}...", expanded=False):
            # Increment view count when expanded (track via button to avoid re-count)
            st.markdown(entry["answer"])

            # Mark as viewed
            if qa_id not in st.session_state.get("qa_db_views", {}):
                st.session_state.qa_db_views[qa_id] = 0
            st.session_state.qa_db_views[qa_id] = st.session_state.qa_db_views.get(qa_id, 0) + 1

            st.divider()

            # Helpful buttons
            st.markdown("**Apakah jawaban ini membantu?**")
            col_up, col_down, col_spacer = st.columns([1, 1, 3])

            rated_set = st.session_state.get("qa_db_rated", set())
            already_rated = qa_id in rated_set

            with col_up:
                if st.button(
                    f"Ya ({helpful})",
                    key=f"qa_helpful_up_{qa_id}",
                    use_container_width=True,
                    disabled=already_rated,
                    type="secondary",
                ):
                    st.session_state.qa_db_helpful[qa_id] = st.session_state.qa_db_helpful.get(qa_id, 0) + 1
                    if not isinstance(st.session_state.qa_db_rated, set):
                        st.session_state.qa_db_rated = set(st.session_state.qa_db_rated)
                    st.session_state.qa_db_rated.add(qa_id)
                    _add_xp(10, "Menilai jawaban fiqih membantu")
                    st.rerun()

            with col_down:
                if st.button(
                    "Tidak",
                    key=f"qa_helpful_down_{qa_id}",
                    use_container_width=True,
                    disabled=already_rated,
                    type="secondary",
                ):
                    if not isinstance(st.session_state.qa_db_rated, set):
                        st.session_state.qa_db_rated = set(st.session_state.qa_db_rated)
                    st.session_state.qa_db_rated.add(qa_id)
                    st.rerun()

            if already_rated:
                st.caption("Terima kasih atas penilaian Anda.")


def render_qa_history_tab():
    """Render user's Q&A history (asked questions + AI answers) with timestamps.

    Stored in st.session_state.ustadz_qa_history (max 20 entries).
    """
    st.markdown(
        '<div class="section-title"><span aria-hidden="true">&#128220;</span> Riwayat Tanya Jawab Anda</div>',
        unsafe_allow_html=True,
    )

    history = st.session_state.get("ustadz_qa_history", [])

    if not history:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon"><span aria-hidden="true">&#128332;</span></div>
            <div class="empty-text">Belum ada riwayat. Ajukan pertanyaan di tab "Tanya Baru" untuk mulai.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    st.caption(f"Menampilkan {len(history)} pertanyaan terakhir (maks 20)")

    for idx, entry in enumerate(history):
        question = entry.get("question", "")
        answer = entry.get("answer", "")
        category = entry.get("category", "umum")
        timestamp = entry.get("timestamp", "")
        cat_info = CATEGORIES.get(category, CATEGORIES["umum"])

        st.markdown(f"""
        <div class="qa-history-card">
            <div class="history-q"><span aria-hidden="true">&#10067;</span> {question}</div>
            <div class="history-time"><span aria-hidden="true">&#128336;</span> {timestamp}
                &nbsp;&middot;&nbsp; {cat_info["icon"]} {cat_info["label"]}</div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander(f"Lihat jawaban #{idx + 1}", expanded=False):
            st.markdown(f"**Pertanyaan:** {question}")
            st.divider()
            st.markdown(answer)

        # "Tanyakan lagi" button
        if st.button(
            f"Tanyakan lagi",
            key=f"qa_hist_reask_{idx}",
            type="secondary",
        ):
            st.session_state.tanya_pending_question = question
            st.session_state.tanya_category = category
            st.rerun()


def render_qa_history():
    """Render Q&A history filtered by selected category, newest first."""
    st.markdown('<div class="section-title">📜 Riwayat Tanya Jawab</div>', unsafe_allow_html=True)

    history = st.session_state.get("tanya_history", [])
    current_cat = st.session_state.get("tanya_category", "semua")

    # Filter by category
    if current_cat == "semua":
        filtered = history
    else:
        filtered = [entry for entry in history if entry.get("category") == current_cat]

    if not filtered:
        if history:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-icon">🔍</div>
                <div class="empty-text">Tidak ada pertanyaan untuk kategori ini. Coba pilih "Semua".</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-icon">🕌</div>
                <div class="empty-text">Belum ada pertanyaan. Ajukan pertanyaan pertama Anda di atas!</div>
            </div>
            """, unsafe_allow_html=True)
        return

    # Render cards
    for idx, entry in enumerate(filtered):
        question = entry.get("question", "")
        answer = entry.get("answer", "")
        category = entry.get("category", "umum")
        timestamp = entry.get("timestamp", "")
        cat_info = CATEGORIES.get(category, CATEGORIES["umum"])
        cat_label = f'{cat_info["icon"]} {cat_info["label"]}'

        # Format answer for HTML display - escape basic HTML but allow our formatting
        answer_html = answer.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        # Re-apply bold markers for display
        answer_html = answer_html.replace("**Jawaban:**", "<strong>📖 Jawaban:</strong>")
        answer_html = answer_html.replace("**Dalil:**", "<strong>📜 Dalil:</strong>")
        answer_html = answer_html.replace("**Rujukan:**", "<strong>📚 Rujukan:</strong>")
        answer_html = answer_html.replace("**Kesimpulan:**", "<strong>✅ Kesimpulan:</strong>")
        # Generic bold
        answer_html = re.sub(
            r"\*\*(.+?)\*\*",
            r"<strong>\1</strong>",
            answer_html,
        )
        # Convert newlines for HTML
        answer_html = answer_html.replace("\n\n", "<br><br>").replace("\n", "<br>")

        st.markdown(f"""
        <div class="qa-card">
            <div class="qa-question">
                <span class="q-icon">❓</span>
                <span>{question}</span>
            </div>
            <div class="qa-answer" role="status" aria-live="polite">{answer_html}</div>
            <div class="qa-meta">
                <span class="qa-category">{cat_label}</span>
                <span class="qa-time">🕐 {timestamp}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Also render in native markdown for accessibility via expander
        with st.expander(f"📋 Lihat jawaban lengkap #{idx + 1}", expanded=False):
            st.markdown(f"**Pertanyaan:** {question}")
            st.divider()
            st.markdown(answer)

    # Show count
    total = len(history)
    showing = len(filtered)
    if current_cat != "semua" and showing < total:
        st.caption(f"Menampilkan {showing} dari {total} pertanyaan (filter: {cat_info['label']})")


# =============================================================================
# MAIN PAGE RENDERER
# =============================================================================

def render_tanya_ustadz_page():
    """Main entry point for Tanya Ustadz AI page."""

    # Track page view
    try:
        from services.analytics import track_page
        track_page("tanya_ustadz")
    except Exception:
        pass

    # Initialize state
    init_tanya_ustadz_state()

    # Hero section with disclaimer
    render_hero()

    st.divider()

    # --- Tabbed interface ---
    tab_tanya, tab_database, tab_riwayat = st.tabs([
        "Tanya Baru",
        "Database Fiqih",
        "Riwayat",
    ])

    with tab_tanya:
        # Ask form (category selector + textarea + submit)
        render_ask_form()

        st.divider()

        # Popular questions (clickable, fills textarea)
        render_popular_questions()

        st.divider()

        # Q&A history (filtered by category, newest first)
        render_qa_history()

    with tab_database:
        render_qa_database()

    with tab_riwayat:
        render_qa_history_tab()

    # Footer
    st.divider()
    st.markdown("""
    <div style="text-align:center; padding: 1rem 0;">
        <p style="color: #64748b; font-size: 0.82rem; margin-bottom: 0.3rem;">
            <strong style="color: #94a3b8;">Tanya Ustadz AI</strong> - Powered by LABBAIK AI
        </p>
        <p style="color: #4a5568; font-size: 0.75rem;">
            Jawaban AI bersifat referensi edukatif. Konsultasikan dengan ustadz/ulama setempat untuk kasus spesifik Anda.
        </p>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# EXPORT
# =============================================================================

__all__ = ["render_tanya_ustadz_page"]
