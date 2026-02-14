"""
Peta Locations - Database POI (Point of Interest) untuk Makkah dan Madinah.

Modul ini berisi data lengkap titik-titik penting yang relevan bagi jamaah
Umrah Indonesia, termasuk tempat ibadah, area hotel, restoran, money changer,
fasilitas kesehatan, dan transportasi.
"""

from enum import Enum
from typing import List, Dict, Optional


# ---------------------------------------------------------------------------
# Enum Kategori POI
# ---------------------------------------------------------------------------

class POICategory(str, Enum):
    IBADAH = "ibadah"
    HOTEL_AREA = "hotel_area"
    KULINER = "kuliner"
    MONEY_CHANGER = "money_changer"
    KESEHATAN = "kesehatan"
    TRANSPORT = "transport"


# ---------------------------------------------------------------------------
# Informasi Kategori (nama, ikon, warna, deskripsi)
# ---------------------------------------------------------------------------

CATEGORY_INFO: Dict[POICategory, Dict] = {
    POICategory.IBADAH: {
        "name": "Ibadah & Ziarah",
        "icon": "\U0001f54b",
        "color": "#228B22",
        "description": "Tempat ibadah utama dan lokasi ziarah bersejarah bagi jamaah Umrah.",
    },
    POICategory.HOTEL_AREA: {
        "name": "Area Hotel",
        "icon": "\U0001f3e8",
        "color": "#4169E1",
        "description": "Kawasan penginapan populer untuk jamaah Umrah dengan berbagai kelas harga.",
    },
    POICategory.KULINER: {
        "name": "Restoran & Kuliner",
        "icon": "\U0001f37d\ufe0f",
        "color": "#FF6347",
        "description": "Restoran dan tempat makan yang ramah jamaah Indonesia.",
    },
    POICategory.MONEY_CHANGER: {
        "name": "Money Changer",
        "icon": "\U0001f4b1",
        "color": "#FFD700",
        "description": "Tempat penukaran mata uang asing ke Riyal Saudi.",
    },
    POICategory.KESEHATAN: {
        "name": "Klinik & RS",
        "icon": "\U0001f3e5",
        "color": "#DC143C",
        "description": "Fasilitas kesehatan, rumah sakit, dan apotek terdekat dari lokasi jamaah.",
    },
    POICategory.TRANSPORT: {
        "name": "Transportasi",
        "icon": "\U0001f684",
        "color": "#008080",
        "description": "Stasiun kereta, terminal bus, dan titik transportasi umum.",
    },
}


# ---------------------------------------------------------------------------
# POI Kota Makkah
# ---------------------------------------------------------------------------

MAKKAH_POIS: List[Dict] = [
    # ========== IBADAH ==========
    {
        "id": "makkah_haram_main",
        "name": "Masjidil Haram",
        "name_ar": "\u0627\u0644\u0645\u0633\u062c\u062f \u0627\u0644\u062d\u0631\u0627\u0645",
        "category": "ibadah",
        "city": "makkah",
        "lat": 21.4225,
        "lng": 39.8262,
        "description": (
            "Masjidil Haram adalah masjid terbesar di dunia dan merupakan kiblat "
            "umat Islam. Di dalamnya terdapat Ka'bah, Maqam Ibrahim, serta area "
            "Sa'i antara Safa dan Marwah. Masjid ini mampu menampung lebih dari "
            "2 juta jamaah pada musim haji."
        ),
        "tips": (
            "Gunakan pintu masuk yang sesuai dengan lokasi hotel Anda untuk "
            "menghindari kerumunan. Waktu paling sepi untuk tawaf biasanya "
            "setelah Isya hingga sebelum Subuh. Simpan nomor pintu masuk Anda "
            "sebagai patokan agar tidak tersesat saat keluar."
        ),
        "icon": "\U0001f54b",
        "color": "#228B22",
    },
    {
        "id": "makkah_kabah",
        "name": "Ka'bah",
        "name_ar": "\u0627\u0644\u0643\u0639\u0628\u0629",
        "category": "ibadah",
        "city": "makkah",
        "lat": 21.42252,
        "lng": 39.82621,
        "description": (
            "Ka'bah adalah bangunan suci yang menjadi pusat tawaf dan kiblat "
            "shalat umat Islam di seluruh dunia. Dibangun pertama kali oleh Nabi "
            "Ibrahim AS dan putranya Nabi Ismail AS."
        ),
        "tips": (
            "Saat tawaf, usahakan tetap di jalur luar jika membawa orang tua "
            "atau anak-anak karena lebih longgar. Lantai atas biasanya lebih "
            "sejuk dan tidak terlalu padat. Pastikan dalam keadaan wudhu "
            "sebelum memulai tawaf."
        ),
        "icon": "\U0001f54b",
        "color": "#228B22",
    },
    {
        "id": "makkah_safa_marwah",
        "name": "Safa & Marwah",
        "name_ar": "\u0627\u0644\u0635\u0641\u0627 \u0648\u0627\u0644\u0645\u0631\u0648\u0629",
        "category": "ibadah",
        "city": "makkah",
        "lat": 21.4226,
        "lng": 39.8268,
        "description": (
            "Bukit Safa dan Marwah adalah lokasi pelaksanaan Sa'i, salah satu "
            "rukun Umrah. Jamaah berjalan 7 kali antara kedua bukit ini mengikuti "
            "jejak Siti Hajar AS yang mencari air untuk putranya Ismail AS."
        ),
        "tips": (
            "Jalur Sa'i cukup panjang (sekitar 450 meter sekali jalan). Gunakan "
            "kursi roda yang tersedia gratis di lantai dasar jika kesulitan "
            "berjalan. Bawa botol minum dan minum air Zamzam yang tersedia di "
            "sepanjang jalur Sa'i."
        ),
        "icon": "\U0001f54b",
        "color": "#228B22",
    },
    {
        "id": "makkah_hajar_aswad",
        "name": "Hajar Aswad",
        "name_ar": "\u0627\u0644\u062d\u062c\u0631 \u0627\u0644\u0623\u0633\u0648\u062f",
        "category": "ibadah",
        "city": "makkah",
        "lat": 21.42251,
        "lng": 39.82620,
        "description": (
            "Hajar Aswad (Batu Hitam) terletak di sudut tenggara Ka'bah dan "
            "menjadi titik awal serta akhir setiap putaran tawaf. Batu ini "
            "diyakini berasal dari surga."
        ),
        "tips": (
            "Mencium Hajar Aswad sangat sulit karena kerumunan yang padat. "
            "Cukup mengangkat tangan kanan dan mengucapkan 'Bismillahi Allahu "
            "Akbar' dari kejauhan sebagai isyarat saat memulai tawaf. Jangan "
            "memaksakan diri menerobos kerumunan."
        ),
        "icon": "\U0001f54b",
        "color": "#228B22",
    },
    {
        "id": "makkah_maqam_ibrahim",
        "name": "Maqam Ibrahim",
        "name_ar": "\u0645\u0642\u0627\u0645 \u0625\u0628\u0631\u0627\u0647\u064a\u0645",
        "category": "ibadah",
        "city": "makkah",
        "lat": 21.42248,
        "lng": 39.82625,
        "description": (
            "Maqam Ibrahim adalah batu tempat berdirinya Nabi Ibrahim AS saat "
            "membangun Ka'bah. Setelah menyelesaikan tawaf, jamaah disunahkan "
            "shalat 2 rakaat di belakang Maqam Ibrahim."
        ),
        "tips": (
            "Area di belakang Maqam Ibrahim sangat padat. Jika tidak "
            "memungkinkan shalat di dekatnya, boleh shalat di mana saja di "
            "dalam Masjidil Haram selama Maqam Ibrahim berada di antara Anda "
            "dan Ka'bah."
        ),
        "icon": "\U0001f54b",
        "color": "#228B22",
    },
    {
        "id": "makkah_jabal_nur",
        "name": "Jabal Nur / Gua Hira",
        "name_ar": "\u062c\u0628\u0644 \u0627\u0644\u0646\u0648\u0631",
        "category": "ibadah",
        "city": "makkah",
        "lat": 21.4577,
        "lng": 39.8562,
        "description": (
            "Jabal Nur (Gunung Cahaya) memiliki ketinggian sekitar 642 meter. "
            "Di puncaknya terdapat Gua Hira, tempat Nabi Muhammad SAW menerima "
            "wahyu pertama dari Malaikat Jibril AS."
        ),
        "tips": (
            "Pendakian membutuhkan waktu 1-2 jam. Gunakan alas kaki yang kuat "
            "dan bawa air minum yang cukup. Hindari mendaki saat tengah hari "
            "karena panas yang ekstrem. Pendakian bukan bagian dari ibadah "
            "Umrah, jadi tidak wajib dilakukan."
        ),
        "icon": "\U0001f54b",
        "color": "#228B22",
    },
    {
        "id": "makkah_jabal_tsur",
        "name": "Jabal Tsur",
        "name_ar": "\u062c\u0628\u0644 \u062b\u0648\u0631",
        "category": "ibadah",
        "city": "makkah",
        "lat": 21.3733,
        "lng": 39.8211,
        "description": (
            "Jabal Tsur adalah gunung tempat Gua Tsur berada. Di gua inilah "
            "Nabi Muhammad SAW dan Abu Bakar ash-Shiddiq bersembunyi selama "
            "3 hari saat hijrah ke Madinah."
        ),
        "tips": (
            "Pendakian Jabal Tsur lebih berat dari Jabal Nur. Sebaiknya hanya "
            "dilakukan oleh jamaah yang kondisi fisiknya prima. Tidak "
            "disarankan untuk lansia. Waktu terbaik mendaki adalah pagi hari "
            "sebelum matahari tinggi."
        ),
        "icon": "\U0001f54b",
        "color": "#228B22",
    },
    {
        "id": "makkah_mina",
        "name": "Mina",
        "name_ar": "\u0645\u0646\u0649",
        "category": "ibadah",
        "city": "makkah",
        "lat": 21.4133,
        "lng": 39.8933,
        "description": (
            "Mina adalah lembah yang terletak sekitar 5 km dari Masjidil Haram. "
            "Tempat ini dikenal sebagai 'Kota Tenda' karena ratusan ribu tenda "
            "putih didirikan untuk menampung jamaah haji. Di sini terdapat 3 "
            "Jamarat untuk melontar jumrah."
        ),
        "tips": (
            "Mina terutama digunakan saat musim haji. Jamaah Umrah bisa "
            "mengunjungi area ini untuk ziarah. Perjalanan dari Masjidil Haram "
            "sekitar 15-20 menit dengan kendaraan. Bawa topi atau payung "
            "karena cuaca sangat panas."
        ),
        "icon": "\U0001f54b",
        "color": "#228B22",
    },
    {
        "id": "makkah_arafah",
        "name": "Arafah",
        "name_ar": "\u0639\u0631\u0641\u0629",
        "category": "ibadah",
        "city": "makkah",
        "lat": 21.3549,
        "lng": 39.9842,
        "description": (
            "Padang Arafah adalah lokasi wukuf, rukun haji yang paling utama. "
            "Di sini terdapat Jabal Rahmah (Bukit Kasih Sayang) yang menjadi "
            "tempat bertemunya Nabi Adam AS dan Hawa."
        ),
        "tips": (
            "Arafah berjarak sekitar 22 km dari Masjidil Haram. Jamaah Umrah "
            "bisa berkunjung untuk ziarah di luar musim haji. Sediakan air "
            "minum yang banyak dan pelindung dari sinar matahari. Area ini "
            "sangat luas dan terbuka."
        ),
        "icon": "\U0001f54b",
        "color": "#228B22",
    },
    {
        "id": "makkah_muzdalifah",
        "name": "Muzdalifah",
        "name_ar": "\u0645\u0632\u062f\u0644\u0641\u0629",
        "category": "ibadah",
        "city": "makkah",
        "lat": 21.3892,
        "lng": 39.9333,
        "description": (
            "Muzdalifah terletak antara Arafah dan Mina. Pada saat haji, jamaah "
            "bermalam di sini setelah wukuf di Arafah dan mengumpulkan kerikil "
            "untuk melontar jumrah di Mina."
        ),
        "tips": (
            "Di luar musim haji, Muzdalifah bisa dikunjungi sebagai bagian "
            "dari city tour Makkah. Area ini merupakan lahan terbuka tanpa "
            "banyak fasilitas, jadi pastikan membawa perbekalan sendiri."
        ),
        "icon": "\U0001f54b",
        "color": "#228B22",
    },
    {
        "id": "makkah_abraj_al_bait",
        "name": "Abraj Al-Bait Clock Tower",
        "name_ar": "\u0628\u0631\u062c \u0627\u0644\u0633\u0627\u0639\u0629",
        "category": "ibadah",
        "city": "makkah",
        "lat": 21.4189,
        "lng": 39.8258,
        "description": (
            "Abraj Al-Bait (Menara Jam) adalah kompleks gedung pencakar langit "
            "tertinggi di Makkah yang terletak tepat di seberang Masjidil Haram. "
            "Terdapat museum, pusat perbelanjaan, dan hotel mewah. Menara jamnya "
            "merupakan salah satu yang terbesar di dunia."
        ),
        "tips": (
            "Clock Tower Mall di lantai bawah memiliki banyak restoran dan toko. "
            "Museum Menara Jam bisa dikunjungi untuk melihat panorama Makkah dari "
            "ketinggian. Harga makanan dan belanja di sini relatif lebih mahal "
            "dari area lain."
        ),
        "icon": "\U0001f54b",
        "color": "#228B22",
    },

    # ========== HOTEL AREA ==========
    {
        "id": "makkah_hotel_ajyad",
        "name": "Area Hotel Ajyad",
        "name_ar": "\u0623\u062c\u064a\u0627\u062f",
        "category": "hotel_area",
        "city": "makkah",
        "lat": 21.4195,
        "lng": 39.8245,
        "description": (
            "Kawasan Ajyad merupakan area hotel premium yang sangat dekat dengan "
            "Masjidil Haram. Jarak tempuh hanya 5-10 menit berjalan kaki. "
            "Tersedia hotel bintang 4 dan 5 dengan pemandangan langsung ke "
            "Masjidil Haram."
        ),
        "tips": (
            "Hotel di area ini termasuk yang termahal di Makkah, terutama saat "
            "musim haji dan Ramadhan. Booking jauh-jauh hari (3-6 bulan) untuk "
            "mendapat harga terbaik. Banyak restoran dan minimarket di sekitar "
            "area ini."
        ),
        "icon": "\U0001f3e8",
        "color": "#4169E1",
    },
    {
        "id": "makkah_hotel_misfalah",
        "name": "Area Hotel Misfalah",
        "name_ar": "\u0645\u0633\u0641\u0644\u0629",
        "category": "hotel_area",
        "city": "makkah",
        "lat": 21.4180,
        "lng": 39.8210,
        "description": (
            "Kawasan Misfalah menawarkan hotel kelas menengah dengan jarak "
            "15-20 menit berjalan kaki ke Masjidil Haram. Area ini populer di "
            "kalangan travel Umrah Indonesia karena harga yang lebih terjangkau "
            "namun masih bisa dijangkau dengan jalan kaki."
        ),
        "tips": (
            "Pastikan hotel menyediakan shuttle bus gratis ke Masjidil Haram. "
            "Banyak warung dan restoran Indonesia di sekitar Misfalah. "
            "Medan jalan cukup menanjak, siapkan fisik yang baik jika memilih "
            "berjalan kaki."
        ),
        "icon": "\U0001f3e8",
        "color": "#4169E1",
    },
    {
        "id": "makkah_hotel_aziziyah",
        "name": "Area Hotel Aziziyah",
        "name_ar": "\u0627\u0644\u0639\u0632\u064a\u0632\u064a\u0629",
        "category": "hotel_area",
        "city": "makkah",
        "lat": 21.4050,
        "lng": 39.8100,
        "description": (
            "Aziziyah adalah kawasan hotel budget yang berjarak 4-5 km dari "
            "Masjidil Haram. Harga hotel jauh lebih murah dibanding area dekat "
            "Haram. Kebanyakan paket Umrah ekonomis menggunakan hotel di area ini."
        ),
        "tips": (
            "Wajib memastikan hotel menyediakan bus shuttle ke Masjidil Haram "
            "karena jarak terlalu jauh untuk jalan kaki. Jadwal shuttle biasanya "
            "mengikuti waktu shalat. Banyak restoran murah dan supermarket di "
            "area ini."
        ),
        "icon": "\U0001f3e8",
        "color": "#4169E1",
    },
    {
        "id": "makkah_hotel_syisyah",
        "name": "Area Hotel Syisyah",
        "name_ar": "\u0627\u0644\u0634\u064a\u0634\u0629",
        "category": "hotel_area",
        "city": "makkah",
        "lat": 21.4350,
        "lng": 39.8180,
        "description": (
            "Kawasan Syisyah terletak sekitar 2-3 km di utara Masjidil Haram. "
            "Menawarkan hotel kelas menengah dengan akses yang cukup baik "
            "melalui transportasi umum atau shuttle hotel."
        ),
        "tips": (
            "Beberapa hotel di area ini sudah terhubung jalur pedestrian "
            "menuju Masjidil Haram. Cek apakah hotel menyediakan layanan "
            "antar-jemput. Harga lebih terjangkau dari Ajyad tapi lebih mahal "
            "dari Aziziyah."
        ),
        "icon": "\U0001f3e8",
        "color": "#4169E1",
    },

    # ========== KULINER ==========
    {
        "id": "makkah_albaik_haram",
        "name": "Al Baik dekat Haram",
        "name_ar": "\u0627\u0644\u0628\u064a\u0643",
        "category": "kuliner",
        "city": "makkah",
        "lat": 21.4210,
        "lng": 39.8250,
        "description": (
            "Al Baik adalah restoran cepat saji lokal Saudi yang sangat populer "
            "dan wajib dicoba. Terkenal dengan ayam goreng renyah dan udang "
            "gorengnya. Cabang ini terletak dekat Masjidil Haram sehingga "
            "selalu ramai."
        ),
        "tips": (
            "Antrean bisa sangat panjang terutama setelah shalat. Datang di "
            "luar jam makan utama untuk menghindari kerumunan. Menu favorit "
            "jamaah Indonesia: Broasted Chicken dan Shrimp Meal. Harga sangat "
            "terjangkau, sekitar 15-20 SAR per paket."
        ),
        "icon": "\U0001f37d\ufe0f",
        "color": "#FF6347",
    },
    {
        "id": "makkah_albaik_aziziyah",
        "name": "Al Baik Aziziyah",
        "name_ar": "\u0627\u0644\u0628\u064a\u0643 \u0627\u0644\u0639\u0632\u064a\u0632\u064a\u0629",
        "category": "kuliner",
        "city": "makkah",
        "lat": 21.4060,
        "lng": 39.8110,
        "description": (
            "Cabang Al Baik di kawasan Aziziyah yang biasanya lebih sepi "
            "dibandingkan cabang dekat Haram. Menu dan harga sama dengan "
            "cabang lainnya."
        ),
        "tips": (
            "Pilihan lebih baik jika hotel Anda di area Aziziyah. Antrean "
            "biasanya lebih pendek. Buka 24 jam sehingga cocok untuk makan "
            "setelah ibadah malam. Tersedia layanan drive-thru."
        ),
        "icon": "\U0001f37d\ufe0f",
        "color": "#FF6347",
    },
    {
        "id": "makkah_herfy",
        "name": "Herfy Burger",
        "name_ar": "\u0647\u0631\u0641\u064a",
        "category": "kuliner",
        "city": "makkah",
        "lat": 21.4200,
        "lng": 39.8255,
        "description": (
            "Herfy adalah jaringan restoran burger asal Saudi Arabia. "
            "Menyajikan burger, ayam, dan makanan cepat saji lainnya dengan "
            "cita rasa khas Timur Tengah."
        ),
        "tips": (
            "Alternatif bagus jika antrean Al Baik terlalu panjang. Menu "
            "cukup bervariasi dengan harga terjangkau (20-35 SAR). Tersedia "
            "menu sarapan pagi. Cocok untuk jamaah yang ingin variasi dari "
            "makanan Arab."
        ),
        "icon": "\U0001f37d\ufe0f",
        "color": "#FF6347",
    },
    {
        "id": "makkah_kudu",
        "name": "Kudu Restaurant",
        "name_ar": "\u0643\u062f\u0648",
        "category": "kuliner",
        "city": "makkah",
        "lat": 21.4185,
        "lng": 39.8230,
        "description": (
            "Kudu adalah jaringan restoran cepat saji populer di Arab Saudi "
            "yang menyajikan sandwich, burger, dan sarapan. Dikenal dengan "
            "sandwich khasnya yang menggunakan roti Arab."
        ),
        "tips": (
            "Cocok untuk sarapan dengan pilihan croissant dan sandwich yang "
            "enak. Harga lebih terjangkau dari restoran di dalam mall. "
            "Tersedia menu kopi dan jus segar. Cabang tersebar di banyak "
            "lokasi di Makkah."
        ),
        "icon": "\U0001f37d\ufe0f",
        "color": "#FF6347",
    },
    {
        "id": "makkah_romansiah",
        "name": "Al Romansiah",
        "name_ar": "\u0627\u0644\u0631\u0648\u0645\u0627\u0646\u0633\u064a\u0629",
        "category": "kuliner",
        "city": "makkah",
        "lat": 21.4175,
        "lng": 39.8220,
        "description": (
            "Al Romansiah adalah restoran masakan Arab tradisional yang terkenal "
            "dengan nasi kebuli (kabsa), daging kambing, dan ayam panggang. "
            "Porsi besar cocok untuk makan bersama rombongan."
        ),
        "tips": (
            "Sangat direkomendasikan untuk makan bersama karena porsi besar "
            "dan bisa sharing. Pesan Kabsa Chicken atau Lamb Mandi untuk "
            "pengalaman kuliner Arab autentik. Harga sekitar 30-60 SAR per "
            "porsi. Tersedia area keluarga terpisah."
        ),
        "icon": "\U0001f37d\ufe0f",
        "color": "#FF6347",
    },

    # ========== MONEY CHANGER ==========
    {
        "id": "makkah_alrajhi_clock_tower",
        "name": "Al Rajhi Bank - Clock Tower",
        "name_ar": "\u0645\u0635\u0631\u0641 \u0627\u0644\u0631\u0627\u062c\u062d\u064a",
        "category": "money_changer",
        "city": "makkah",
        "lat": 21.4190,
        "lng": 39.8260,
        "description": (
            "Al Rajhi Bank adalah salah satu bank terbesar di Saudi Arabia. "
            "Cabang di Clock Tower Mall menyediakan layanan penukaran mata uang "
            "asing dengan kurs yang kompetitif dan terpercaya."
        ),
        "tips": (
            "Kurs di bank resmi biasanya lebih baik dan aman dari money changer "
            "kecil. Bawa paspor asli untuk transaksi penukaran. Hindari "
            "menukar uang di pedagang kaki lima. Jam operasional mengikuti "
            "jam bank (biasanya tutup saat shalat)."
        ),
        "icon": "\U0001f4b1",
        "color": "#FFD700",
    },
    {
        "id": "makkah_mc_ajyad",
        "name": "Money Changer Ajyad",
        "name_ar": "\u0635\u0631\u0627\u0641\u0629 \u0623\u062c\u064a\u0627\u062f",
        "category": "money_changer",
        "city": "makkah",
        "lat": 21.4198,
        "lng": 39.8248,
        "description": (
            "Deretan money changer di kawasan Ajyad yang mudah diakses dari "
            "hotel-hotel terdekat. Menyediakan penukaran berbagai mata uang "
            "termasuk Rupiah Indonesia."
        ),
        "tips": (
            "Bandingkan kurs di beberapa money changer sebelum menukar. "
            "Simpan bukti transaksi penukaran. Tukarkan uang secukupnya saja, "
            "sisa Riyal bisa ditukar kembali di Indonesia. Bawa pecahan USD "
            "besar (100 USD) untuk mendapat kurs lebih baik."
        ),
        "icon": "\U0001f4b1",
        "color": "#FFD700",
    },

    # ========== KESEHATAN ==========
    {
        "id": "makkah_rs_ajyad",
        "name": "Ajyad Hospital",
        "name_ar": "\u0645\u0633\u062a\u0634\u0641\u0649 \u0623\u062c\u064a\u0627\u062f",
        "category": "kesehatan",
        "city": "makkah",
        "lat": 21.4170,
        "lng": 39.8235,
        "description": (
            "Rumah Sakit Ajyad adalah RS pemerintah yang terletak dekat "
            "Masjidil Haram. Menyediakan layanan IGD 24 jam dan pelayanan "
            "medis dasar untuk jamaah. Pelayanan gratis untuk jamaah haji "
            "dan Umrah."
        ),
        "tips": (
            "Bawa fotokopi paspor dan kartu identitas saat berobat. Layanan "
            "untuk jamaah biasanya gratis di RS pemerintah Saudi. Tersedia "
            "penerjemah bahasa di beberapa RS besar. Simpan nomor darurat "
            "KBRI: +966-12-5422555."
        ),
        "icon": "\U0001f3e5",
        "color": "#DC143C",
    },
    {
        "id": "makkah_rs_hera",
        "name": "Hera General Hospital",
        "name_ar": "\u0645\u0633\u062a\u0634\u0641\u0649 \u0647\u0631\u0627\u0621 \u0627\u0644\u0639\u0627\u0645",
        "category": "kesehatan",
        "city": "makkah",
        "lat": 21.4455,
        "lng": 39.8510,
        "description": (
            "Hera General Hospital adalah rumah sakit umum yang lebih besar "
            "dengan fasilitas lengkap termasuk radiologi, laboratorium, dan "
            "unit perawatan intensif. Terletak di area utara Makkah."
        ),
        "tips": (
            "RS ini menangani kasus yang lebih serius. Jika kondisi darurat, "
            "hubungi ambulans di nomor 997 atau minta bantuan petugas hotel. "
            "Bawa obat-obatan pribadi dari Indonesia sebagai cadangan. "
            "Konsultasi dengan dokter travel sebelum berangkat Umrah."
        ),
        "icon": "\U0001f3e5",
        "color": "#DC143C",
    },
    {
        "id": "makkah_apotek_aldawa",
        "name": "Apotek Al Dawa",
        "name_ar": "\u0635\u064a\u062f\u0644\u064a\u0629 \u0627\u0644\u062f\u0648\u0627\u0621",
        "category": "kesehatan",
        "city": "makkah",
        "lat": 21.4205,
        "lng": 39.8253,
        "description": (
            "Al Dawa Pharmacy adalah jaringan apotek terbesar di Arab Saudi. "
            "Cabang ini dekat Masjidil Haram dan menyediakan obat-obatan umum, "
            "vitamin, masker, dan perlengkapan kesehatan."
        ),
        "tips": (
            "Obat tanpa resep tersedia langsung. Untuk obat resep, bawa resep "
            "dokter dari Indonesia atau berobat di klinik Saudi terlebih dahulu. "
            "Stok obat flu, batuk, dan vitamin sebelum berangkat karena harga "
            "di Saudi bisa lebih mahal. Buka hingga larut malam."
        ),
        "icon": "\U0001f3e5",
        "color": "#DC143C",
    },

    # ========== TRANSPORT ==========
    {
        "id": "makkah_haramain_station",
        "name": "Stasiun Haramain Makkah",
        "name_ar": "\u0645\u062d\u0637\u0629 \u0627\u0644\u062d\u0631\u0645\u064a\u0646 \u0627\u0644\u0633\u0631\u064a\u0639",
        "category": "transport",
        "city": "makkah",
        "lat": 21.3803,
        "lng": 39.8004,
        "description": (
            "Stasiun Kereta Cepat Haramain di Makkah menghubungkan Makkah "
            "dengan Madinah melalui Jeddah dan Bandara KAAIA. Perjalanan "
            "Makkah-Madinah memakan waktu sekitar 2 jam dengan kecepatan "
            "hingga 300 km/jam."
        ),
        "tips": (
            "Beli tiket online melalui aplikasi SAR (Saudi Arabia Railways) "
            "untuk menghindari antrean di stasiun. Datang minimal 30 menit "
            "sebelum keberangkatan. Tersedia kelas Ekonomi dan Bisnis. "
            "Tiket Ekonomi sekitar 150-250 SAR. Bawa paspor asli saat naik "
            "kereta. Stasiun berjarak sekitar 7 km dari Masjidil Haram."
        ),
        "icon": "\U0001f684",
        "color": "#008080",
    },
]


# ---------------------------------------------------------------------------
# POI Kota Madinah
# ---------------------------------------------------------------------------

MADINAH_POIS: List[Dict] = [
    # ========== IBADAH ==========
    {
        "id": "madinah_nabawi",
        "name": "Masjid Nabawi",
        "name_ar": "\u0627\u0644\u0645\u0633\u062c\u062f \u0627\u0644\u0646\u0628\u0648\u064a",
        "category": "ibadah",
        "city": "madinah",
        "lat": 24.4672,
        "lng": 39.6112,
        "description": (
            "Masjid Nabawi adalah masjid kedua tersuci dalam Islam, dibangun "
            "oleh Nabi Muhammad SAW setelah hijrah ke Madinah. Di dalamnya "
            "terdapat makam Rasulullah SAW, Abu Bakar ash-Shiddiq, dan Umar "
            "bin Khattab. Shalat di Masjid Nabawi pahalanya 1000 kali lipat."
        ),
        "tips": (
            "Untuk ziarah ke makam Nabi, ikuti jalur yang sudah ditentukan "
            "petugas. Antrian bisa sangat panjang, terutama setelah shalat "
            "wajib. Pakai pakaian rapi dan sopan. Area taman di dalam masjid "
            "dengan payung raksasa sangat nyaman untuk istirahat. Bawa sajadah "
            "tipis sendiri agar lebih nyaman."
        ),
        "icon": "\U0001f54c",
        "color": "#228B22",
    },
    {
        "id": "madinah_raudhah",
        "name": "Raudhah",
        "name_ar": "\u0627\u0644\u0631\u0648\u0636\u0629 \u0627\u0644\u0634\u0631\u064a\u0641\u0629",
        "category": "ibadah",
        "city": "madinah",
        "lat": 24.4675,
        "lng": 39.6115,
        "description": (
            "Raudhah (Taman Surga) adalah area istimewa di dalam Masjid Nabawi "
            "yang terletak antara mimbar dan makam Nabi Muhammad SAW. Nabi "
            "bersabda bahwa area ini adalah salah satu taman surga. Ditandai "
            "dengan karpet hijau yang berbeda dari area lainnya."
        ),
        "tips": (
            "Akses Raudhah untuk jamaah wanita biasanya dijadwalkan pada waktu "
            "tertentu (biasanya pagi hari). Untuk jamaah pria, datang di luar "
            "jam shalat wajib agar lebih mudah masuk. Antrean bisa sangat "
            "panjang, siapkan kesabaran. Shalat dan berdoa di Raudhah sangat "
            "dianjurkan."
        ),
        "icon": "\U0001f54c",
        "color": "#228B22",
    },
    {
        "id": "madinah_bab_salam",
        "name": "Bab Salam",
        "name_ar": "\u0628\u0627\u0628 \u0627\u0644\u0633\u0644\u0627\u0645",
        "category": "ibadah",
        "city": "madinah",
        "lat": 24.4680,
        "lng": 39.6120,
        "description": (
            "Bab Salam (Pintu Salam) adalah salah satu pintu utama Masjid "
            "Nabawi yang digunakan jamaah untuk masuk saat ziarah ke makam "
            "Rasulullah SAW. Merupakan pintu masuk yang disunahkan saat "
            "memasuki masjid untuk pertama kali."
        ),
        "tips": (
            "Masuk melalui Bab Salam sambil membaca doa masuk masjid dan "
            "mendahulukan kaki kanan. Setelah masuk, lanjutkan ke Raudhah "
            "atau langsung ke area makam Nabi SAW untuk mengucapkan salam. "
            "Ikuti petunjuk petugas dan jangan berhenti di tengah jalur."
        ),
        "icon": "\U0001f54c",
        "color": "#228B22",
    },
    {
        "id": "madinah_bab_jibril",
        "name": "Bab Jibril",
        "name_ar": "\u0628\u0627\u0628 \u062c\u0628\u0631\u064a\u0644",
        "category": "ibadah",
        "city": "madinah",
        "lat": 24.4665,
        "lng": 39.6105,
        "description": (
            "Bab Jibril (Pintu Jibril) adalah pintu bersejarah di sisi selatan "
            "Masjid Nabawi. Dinamakan demikian karena konon Malaikat Jibril AS "
            "sering menemui Nabi Muhammad SAW melalui arah pintu ini."
        ),
        "tips": (
            "Pintu ini sering digunakan sebagai titik keluar setelah ziarah. "
            "Area di sekitar Bab Jibril biasanya lebih sepi dibanding Bab Salam. "
            "Cocok sebagai alternatif pintu masuk jika Bab Salam sangat ramai."
        ),
        "icon": "\U0001f54c",
        "color": "#228B22",
    },
    {
        "id": "madinah_quba",
        "name": "Masjid Quba",
        "name_ar": "\u0645\u0633\u062c\u062f \u0642\u0628\u0627\u0621",
        "category": "ibadah",
        "city": "madinah",
        "lat": 24.4393,
        "lng": 39.6178,
        "description": (
            "Masjid Quba adalah masjid pertama yang dibangun dalam sejarah "
            "Islam. Nabi Muhammad SAW bersabda bahwa shalat di Masjid Quba "
            "pahalanya setara dengan Umrah. Terletak sekitar 5 km di selatan "
            "Masjid Nabawi."
        ),
        "tips": (
            "Sangat dianjurkan berkunjung pada hari Sabtu mengikuti sunah Nabi. "
            "Shalat 2 rakaat di Masjid Quba mendapatkan pahala setara Umrah. "
            "Tersedia taksi dan bus dari Masjid Nabawi. Perjalanan sekitar "
            "10-15 menit. Setelah shalat, bisa mampir ke pasar kurma terdekat."
        ),
        "icon": "\U0001f54c",
        "color": "#228B22",
    },
    {
        "id": "madinah_qiblatain",
        "name": "Masjid Qiblatain",
        "name_ar": "\u0645\u0633\u062c\u062f \u0627\u0644\u0642\u0628\u0644\u062a\u064a\u0646",
        "category": "ibadah",
        "city": "madinah",
        "lat": 24.4850,
        "lng": 39.6222,
        "description": (
            "Masjid Qiblatain (Masjid Dua Kiblat) adalah tempat bersejarah "
            "di mana turunnya perintah untuk mengubah arah kiblat dari "
            "Masjidil Aqsa (Yerusalem) ke Ka'bah (Makkah) saat shalat "
            "Zhuhur sedang berlangsung."
        ),
        "tips": (
            "Biasanya termasuk dalam paket city tour Madinah. Masjid ini "
            "berukuran relatif kecil. Kunjungan singkat 15-30 menit sudah "
            "cukup untuk shalat dan berfoto. Letaknya di utara Masjid Nabawi, "
            "sekitar 10 menit berkendara."
        ),
        "icon": "\U0001f54c",
        "color": "#228B22",
    },
    {
        "id": "madinah_jabal_uhud",
        "name": "Jabal Uhud",
        "name_ar": "\u062c\u0628\u0644 \u0623\u062d\u062f",
        "category": "ibadah",
        "city": "madinah",
        "lat": 24.5000,
        "lng": 39.6100,
        "description": (
            "Jabal Uhud adalah gunung yang terletak di utara Madinah, terkenal "
            "sebagai lokasi Perang Uhud. Nabi Muhammad SAW bersabda: 'Uhud "
            "adalah gunung yang mencintai kami dan kami mencintainya.' Di "
            "kakinya terdapat makam para syuhada Uhud."
        ),
        "tips": (
            "Kunjungi di pagi atau sore hari untuk menghindari panas. Ziarah "
            "ke makam syuhada Uhud termasuk Hamzah bin Abdul Muthalib (paman "
            "Nabi). Jangan memanjat gunung tanpa persiapan. Bawa air minum "
            "yang cukup. Biasanya termasuk dalam paket city tour."
        ),
        "icon": "\U0001f54c",
        "color": "#228B22",
    },
    {
        "id": "madinah_syuhada_uhud",
        "name": "Makam Syuhada Uhud",
        "name_ar": "\u0645\u0642\u0628\u0631\u0629 \u0634\u0647\u062f\u0627\u0621 \u0623\u062d\u062f",
        "category": "ibadah",
        "city": "madinah",
        "lat": 24.4989,
        "lng": 39.6095,
        "description": (
            "Makam Syuhada Uhud adalah tempat peristirahatan terakhir para "
            "sahabat Nabi yang gugur dalam Perang Uhud, termasuk Hamzah bin "
            "Abdul Muthalib, paman Nabi yang dijuluki Singa Allah."
        ),
        "tips": (
            "Baca doa untuk para syuhada saat berziarah. Jaga adab dan "
            "ketenangan di area makam. Jangan duduk atau menginjak area makam. "
            "Tersedia pedagang yang menjual suvenir di sekitar lokasi, "
            "pastikan menawar harga dengan wajar."
        ),
        "icon": "\U0001f54c",
        "color": "#228B22",
    },

    # ========== HOTEL AREA ==========
    {
        "id": "madinah_hotel_central",
        "name": "Area Hotel Central Nabawi",
        "name_ar": "\u0641\u0646\u0627\u062f\u0642 \u0627\u0644\u0645\u0646\u0637\u0642\u0629 \u0627\u0644\u0645\u0631\u0643\u0632\u064a\u0629",
        "category": "hotel_area",
        "city": "madinah",
        "lat": 24.4680,
        "lng": 39.6100,
        "description": (
            "Kawasan hotel utama di Madinah terletak di sekitar Masjid Nabawi, "
            "terutama di sisi barat dan selatan. Tersedia hotel dari kelas "
            "bintang 3 hingga 5 dengan jarak 2-10 menit berjalan kaki ke "
            "pintu masjid."
        ),
        "tips": (
            "Hotel di sisi barat (dekat Bab Salam) biasanya lebih mahal. "
            "Pilih hotel di sisi selatan untuk harga lebih terjangkau dengan "
            "jarak masih bisa dijangkau jalan kaki. Banyak restoran dan toko "
            "di sepanjang jalan menuju Masjid Nabawi. Booking jauh hari untuk "
            "harga terbaik."
        ),
        "icon": "\U0001f3e8",
        "color": "#4169E1",
    },

    # ========== KULINER ==========
    {
        "id": "madinah_albaik",
        "name": "Al Baik Madinah",
        "name_ar": "\u0627\u0644\u0628\u064a\u0643 \u0627\u0644\u0645\u062f\u064a\u0646\u0629",
        "category": "kuliner",
        "city": "madinah",
        "lat": 24.4690,
        "lng": 39.6105,
        "description": (
            "Cabang Al Baik di Madinah yang tidak kalah populer dari cabang "
            "di Makkah. Restoran cepat saji favorit jamaah Indonesia dengan "
            "ayam goreng dan udang goreng andalannya."
        ),
        "tips": (
            "Terletak tidak jauh dari Masjid Nabawi sehingga mudah dijangkau "
            "setelah shalat. Antrean tetap panjang terutama setelah shalat "
            "Maghrib dan Isya. Pesan ukuran besar untuk sharing dengan teman "
            "sekamar. Harga sama murahnya seperti di Makkah."
        ),
        "icon": "\U0001f37d\ufe0f",
        "color": "#FF6347",
    },
    {
        "id": "madinah_pasar_kurma",
        "name": "Pasar Kurma Madinah",
        "name_ar": "\u0633\u0648\u0642 \u0627\u0644\u062a\u0645\u0631",
        "category": "kuliner",
        "city": "madinah",
        "lat": 24.4700,
        "lng": 39.6090,
        "description": (
            "Pasar Kurma (Souq Al-Tamr) adalah pusat penjualan kurma terbesar "
            "di Madinah. Tersedia ratusan jenis kurma dengan berbagai kualitas "
            "dan harga, termasuk kurma Ajwa yang terkenal berkhasiat."
        ),
        "tips": (
            "Kurma Ajwa Madinah paling dicari, harganya sekitar 80-150 SAR/kg "
            "tergantung kualitas. Selalu minta mencicipi sebelum membeli. "
            "Beli dalam jumlah banyak untuk mendapat harga lebih murah. "
            "Kemas rapat untuk dibawa pulang. Tawar harga dengan sopan, "
            "biasanya bisa turun 10-20%."
        ),
        "icon": "\U0001f37d\ufe0f",
        "color": "#FF6347",
    },

    # ========== TRANSPORT ==========
    {
        "id": "madinah_haramain_station",
        "name": "Stasiun Haramain Madinah",
        "name_ar": "\u0645\u062d\u0637\u0629 \u0627\u0644\u062d\u0631\u0645\u064a\u0646 \u0627\u0644\u0645\u062f\u064a\u0646\u0629",
        "category": "transport",
        "city": "madinah",
        "lat": 24.5439,
        "lng": 39.6994,
        "description": (
            "Stasiun Kereta Cepat Haramain di Madinah menghubungkan Madinah "
            "ke Makkah via Jeddah dan Bandara King Abdulaziz. Perjalanan ke "
            "Makkah memakan waktu sekitar 2 jam. Stasiun ini modern dan "
            "dilengkapi fasilitas lengkap."
        ),
        "tips": (
            "Stasiun berjarak sekitar 15 km dari Masjid Nabawi, perlu taksi "
            "atau bus (sekitar 20-30 menit). Beli tiket melalui aplikasi SAR "
            "atau website resmi. Tiket Ekonomi Madinah-Makkah sekitar 150-250 "
            "SAR. Datang 30-45 menit sebelum keberangkatan. Bawa paspor asli "
            "untuk verifikasi tiket."
        ),
        "icon": "\U0001f684",
        "color": "#008080",
    },
]


# ---------------------------------------------------------------------------
# Gabungan Semua POI
# ---------------------------------------------------------------------------

ALL_POIS: List[Dict] = MAKKAH_POIS + MADINAH_POIS


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def get_pois_by_city(city: str) -> List[Dict]:
    """Ambil semua POI berdasarkan kota.

    Args:
        city: Nama kota ("makkah" atau "madinah").

    Returns:
        List berisi dict POI yang sesuai dengan kota.
    """
    return [poi for poi in ALL_POIS if poi["city"] == city]


def get_pois_by_category(city: str, category: str) -> List[Dict]:
    """Ambil POI berdasarkan kota dan kategori.

    Args:
        city: Nama kota ("makkah" atau "madinah").
        category: Nilai kategori dari POICategory (misalnya "ibadah", "kuliner").

    Returns:
        List berisi dict POI yang sesuai dengan kota dan kategori.
    """
    return [
        poi for poi in ALL_POIS
        if poi["city"] == city and poi["category"] == category
    ]


def get_poi_by_id(poi_id: str) -> Optional[Dict]:
    """Ambil satu POI berdasarkan ID unik.

    Args:
        poi_id: ID unik POI (misalnya "makkah_haram_main").

    Returns:
        Dict POI jika ditemukan, None jika tidak ada.
    """
    for poi in ALL_POIS:
        if poi["id"] == poi_id:
            return poi
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__ = [
    "POICategory",
    "CATEGORY_INFO",
    "MAKKAH_POIS",
    "MADINAH_POIS",
    "ALL_POIS",
    "get_pois_by_city",
    "get_pois_by_category",
    "get_poi_by_id",
]
