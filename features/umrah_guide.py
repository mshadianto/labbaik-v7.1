"""
LABBAIK AI v7.0 - Complete Umrah Guide
=======================================
Super enhanced Umrah guide based on Ministry of Hajj and Umrah official document.

Features:
- Complete step-by-step Umrah procedures
- Comprehensive doa collection with audio
- Pillars, duties, and Sunnahs
- Miqat locations and information
- Historical sites in Makkah and Madinah
- Interactive guide mode
"""

import streamlit as st
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json

# =============================================================================
# DATA STRUCTURES
# =============================================================================

class UmrahStep(str, Enum):
    PREPARATION = "preparation"
    IHRAM = "ihram"
    TAWAF = "tawaf"
    SAI = "sai"
    TAHALLUL = "tahallul"
    ZIARAH = "ziarah"


class DoaCategory(str, Enum):
    PERJALANAN = "perjalanan"
    IHRAM = "ihram"
    TAWAF = "tawaf"
    SAI = "sai"
    MASJID = "masjid"
    HARIAN = "harian"
    ZIARAH = "ziarah"
    RAWDAH = "rawdah"


@dataclass
class Doa:
    """Enhanced Doa structure."""
    id: str
    name: str
    arabic: str
    latin: str
    translation_id: str  # Indonesian
    translation_en: str  # English
    category: DoaCategory
    when_to_read: str
    location: str = ""
    is_wajib: bool = False
    is_sunnah: bool = True
    audio_url: str = ""
    source: str = ""  # Hadith reference


@dataclass
class UmrahProcedure:
    """Umrah procedure step."""
    step: int
    name: str
    name_ar: str
    description: str
    location: str
    is_pillar: bool  # Rukun
    is_obligatory: bool  # Wajib
    tips: List[str] = field(default_factory=list)
    doas: List[str] = field(default_factory=list)  # Doa IDs
    sunnahs: List[str] = field(default_factory=list)


@dataclass
class Miqat:
    """Miqat location."""
    name: str
    name_ar: str
    location: str
    for_travelers_from: str
    distance_to_makkah: str
    coordinates: tuple = (0, 0)


@dataclass
class HistoricalSite:
    """Historical site in Makkah/Madinah."""
    name: str
    name_ar: str
    city: str  # MAKKAH or MADINAH
    description: str
    significance: str
    visiting_tips: str
    coordinates: tuple = (0, 0)


# =============================================================================
# UMRAH DEFINITION & VIRTUES
# =============================================================================

UMRAH_DEFINITION = {
    "en": "Umrah is worshipping Allah through Ihram, Tawaf, Sa'i between Safa and Marwa, and a partial or complete shortening of the hair.",
    "id": "Umrah adalah ibadah kepada Allah melalui Ihram, Tawaf, Sa'i antara Safa dan Marwa, dan mencukur atau memotong rambut."
}

UMRAH_VIRTUES = [
    {
        "text_en": "Purification of sins",
        "text_id": "Penghapusan dosa-dosa",
        "hadith": "Alternate between Hajj and Umrah; for doing that will eliminate poverty and sin as the bellows eliminate dross. [An-Nasa'i: 2629]"
    },
    {
        "text_en": "Removing poverty",
        "text_id": "Menghilangkan kemiskinan",
        "hadith": "Alternate between Hajj and Umrah; for doing that will eliminate poverty and sin. [An-Nasa'i: 2629]"
    },
    {
        "text_en": "Equal to Jihad for women and elderly",
        "text_id": "Setara dengan jihad bagi wanita dan lansia",
        "hadith": "Jihad of the elderly, the young, the weak and women is Hajj and Umrah. [An-Nasa'i]"
    },
    {
        "text_en": "Guests of Allah",
        "text_id": "Tamu-tamu Allah",
        "hadith": "Those performing Hajj and Umrah are the guests of Allah. [Ibn Majah]"
    }
]

# =============================================================================
# PILLARS, DUTIES & SUNNAHS OF UMRAH
# =============================================================================

UMRAH_PILLARS = [
    {
        "name_en": "Ihram",
        "name_id": "Ihram",
        "name_ar": "الإحرام",
        "description_en": "Entering the state of Ihram with the intention of Umrah",
        "description_id": "Memasuki keadaan Ihram dengan niat Umrah"
    },
    {
        "name_en": "Tawaf",
        "name_id": "Tawaf",
        "name_ar": "الطواف",
        "description_en": "Circling around the Ka'ba seven times",
        "description_id": "Mengelilingi Ka'bah tujuh kali"
    },
    {
        "name_en": "Sa'i",
        "name_id": "Sa'i",
        "name_ar": "السعي",
        "description_en": "Walking between Safa and Marwa seven times",
        "description_id": "Berjalan antara Safa dan Marwa tujuh kali"
    },
    {
        "name_en": "Shaving/Cutting Hair",
        "name_id": "Tahallul (Cukur/Potong Rambut)",
        "name_ar": "الحلق أو التقصير",
        "description_en": "Shaving or cutting the hair to exit Ihram",
        "description_id": "Mencukur atau memotong rambut untuk keluar dari Ihram"
    }
]

UMRAH_SUNNAHS = [
    {"name": "Mandi sebelum Ihram", "name_en": "Taking bath before Ihram"},
    {"name": "Memakai wewangian sebelum Ihram", "name_en": "Applying perfume before Ihram"},
    {"name": "Membaca Talbiyah dengan suara keras (pria)", "name_en": "Reciting Talbiyah loudly (men)"},
    {"name": "Idhtiba' (membuka bahu kanan) saat Tawaf", "name_en": "Idhtiba' (uncovering right shoulder) during Tawaf"},
    {"name": "Ramal (jalan cepat) di 3 putaran pertama Tawaf", "name_en": "Ramal (walking briskly) in first 3 rounds of Tawaf"},
    {"name": "Mencium atau menyentuh Hajar Aswad", "name_en": "Kissing or touching the Black Stone"},
    {"name": "Berdoa di Multazam", "name_en": "Supplicating at Multazam"},
    {"name": "Minum air Zamzam", "name_en": "Drinking Zamzam water"},
    {"name": "Sholat 2 rakaat di belakang Maqam Ibrahim", "name_en": "Praying 2 Rak'ahs behind Maqam Ibrahim"},
    {"name": "Berlari kecil di antara tanda hijau saat Sa'i (pria)", "name_en": "Jogging between green markers during Sa'i (men)"},
]

# =============================================================================
# MIQAT LOCATIONS
# =============================================================================

MIQAT_LOCATIONS: List[Miqat] = [
    Miqat(
        name="Dhul Hulayfah (Abyar Ali)",
        name_ar="ذو الحليفة (أبيار علي)",
        location="Near Madinah",
        for_travelers_from="Madinah and those passing through",
        distance_to_makkah="450 km",
        coordinates=(24.4167, 39.5431)
    ),
    Miqat(
        name="Al-Juhfah (Rabigh)",
        name_ar="الجحفة (رابغ)",
        location="Near Rabigh",
        for_travelers_from="Egypt, Syria, Morocco, and West Africa",
        distance_to_makkah="186 km",
        coordinates=(22.7167, 39.0333)
    ),
    Miqat(
        name="Qarn al-Manazil (As-Sayl)",
        name_ar="قرن المنازل (السيل)",
        location="Near Taif",
        for_travelers_from="Najd and those from the East",
        distance_to_makkah="75 km",
        coordinates=(21.6333, 40.4333)
    ),
    Miqat(
        name="Yalamlam (As-Sadiah)",
        name_ar="يلملم (السعدية)",
        location="South of Makkah",
        for_travelers_from="Yemen and those from the South",
        distance_to_makkah="92 km",
        coordinates=(20.5500, 39.8500)
    ),
    Miqat(
        name="Dhat Irq",
        name_ar="ذات عرق",
        location="Northeast of Makkah",
        for_travelers_from="Iraq and those from the Northeast",
        distance_to_makkah="94 km",
        coordinates=(21.9333, 40.4167)
    ),
    Miqat(
        name="Jeddah (for air travelers)",
        name_ar="جدة (للقادمين جواً)",
        location="Jeddah Airport",
        for_travelers_from="Air travelers who didn't pass another Miqat",
        distance_to_makkah="86 km",
        coordinates=(21.6794, 39.1567)
    ),
]

# =============================================================================
# COMPREHENSIVE DOA DATABASE
# =============================================================================

UMRAH_DOAS: List[Doa] = [
    # === PERJALANAN ===
    Doa(
        id="doa_001",
        name="Doa Keluar Rumah",
        arabic="بِسْمِ اللهِ تَوَكَّلْتُ عَلَى اللهِ وَلاَ حَوْلَ وَلاَ قُوَّةَ إِلاَّ بِاللهِ",
        latin="Bismillahi tawakkaltu 'alallah, wa laa hawla wa laa quwwata illa billah",
        translation_id="Dengan nama Allah, aku bertawakal kepada Allah. Tidak ada daya dan kekuatan kecuali dengan pertolongan Allah.",
        translation_en="In the name of Allah, I place my trust in Allah. There is no power or strength except with Allah.",
        category=DoaCategory.PERJALANAN,
        when_to_read="Saat keluar rumah menuju bandara",
        location="Rumah",
        source="Abu Dawud, Tirmidhi"
    ),
    Doa(
        id="doa_002",
        name="Doa Naik Kendaraan",
        arabic="سُبْحَانَ الَّذِي سَخَّرَ لَنَا هَذَا وَمَا كُنَّا لَهُ مُقْرِنِينَ وَإِنَّا إِلَى رَبِّنَا لَمُنْقَلِبُونَ",
        latin="Subhanalladzi sakhkhara lana hadza wa ma kunna lahu muqrinin, wa inna ila rabbina lamunqalibun",
        translation_id="Maha Suci Allah yang telah menundukkan ini untuk kami, padahal kami tidak mampu menguasainya. Dan sesungguhnya kami akan kembali kepada Tuhan kami.",
        translation_en="Glory be to Him who has subjected this to us, and we could never have it by our efforts. And to our Lord we shall return.",
        category=DoaCategory.PERJALANAN,
        when_to_read="Saat naik pesawat/kendaraan",
        location="Kendaraan",
        source="Az-Zukhruf: 13-14"
    ),
    Doa(
        id="doa_003",
        name="Doa Safar (Perjalanan)",
        arabic="اللَّهُمَّ إِنَّا نَسْأَلُكَ فِي سَفَرِنَا هَذَا الْبِرَّ وَالتَّقْوَى وَمِنَ الْعَمَلِ مَا تَرْضَى",
        latin="Allahumma inna nas'aluka fi safarina hadzal birra wat-taqwa, wa minal 'amali ma tardha",
        translation_id="Ya Allah, kami memohon kepada-Mu dalam perjalanan kami ini kebaikan dan takwa, serta amal yang Engkau ridhai.",
        translation_en="O Allah, we ask You in this journey of ours for righteousness, piety, and deeds that please You.",
        category=DoaCategory.PERJALANAN,
        when_to_read="Saat memulai perjalanan",
        location="Kendaraan",
        source="Muslim"
    ),

    # === IHRAM ===
    Doa(
        id="doa_010",
        name="Niat Ihram Umrah",
        arabic="لَبَّيْكَ اللَّهُمَّ عُمْرَةً",
        latin="Labbaika Allahumma 'Umratan",
        translation_id="Aku penuhi panggilan-Mu ya Allah untuk melaksanakan umrah.",
        translation_en="Here I am O Allah, answering Your call to perform Umrah.",
        category=DoaCategory.IHRAM,
        when_to_read="Saat niat ihram di miqat",
        location="Miqat",
        is_wajib=True,
        source="Bukhari, Muslim"
    ),
    Doa(
        id="doa_011",
        name="Talbiyah",
        arabic="لَبَّيْكَ اللَّهُمَّ لَبَّيْكَ، لَبَّيْكَ لَا شَرِيكَ لَكَ لَبَّيْكَ، إِنَّ الْحَمْدَ وَالنِّعْمَةَ لَكَ وَالْمُلْكَ، لَا شَرِيكَ لَكَ",
        latin="Labbaik Allahumma labbaik, labbaika laa syariika laka labbaik. Innal hamda wan ni'mata laka wal mulk, laa syariika lak",
        translation_id="Aku memenuhi panggilan-Mu ya Allah, aku memenuhi panggilan-Mu. Aku memenuhi panggilan-Mu, tidak ada sekutu bagi-Mu, aku memenuhi panggilan-Mu. Sesungguhnya segala puji, nikmat, dan kerajaan adalah milik-Mu. Tidak ada sekutu bagi-Mu.",
        translation_en="Here I am O Allah, here I am. Here I am, You have no partner, here I am. Verily all praise, grace, and sovereignty belong to You. You have no partner.",
        category=DoaCategory.IHRAM,
        when_to_read="Sepanjang perjalanan menuju Makkah",
        location="Dari Miqat sampai Masjidil Haram",
        is_wajib=True,
        source="Bukhari, Muslim"
    ),

    # === TAWAF ===
    Doa(
        id="doa_020",
        name="Doa Melihat Ka'bah Pertama Kali",
        arabic="اللَّهُمَّ زِدْ هَذَا الْبَيْتَ تَشْرِيفًا وَتَعْظِيمًا وَتَكْرِيمًا وَمَهَابَةً، وَزِدْ مَنْ شَرَّفَهُ وَكَرَّمَهُ مِمَّنْ حَجَّهُ أَوِ اعْتَمَرَهُ تَشْرِيفًا وَتَكْرِيمًا وَتَعْظِيمًا وَبِرًّا",
        latin="Allahumma zid hadzal baita tasyrifan wa ta'zhiman wa takriman wa mahabah, wa zid man syarrafahu wa karramahu mimman hajjahu awi'tamarahu tasyrifan wa takriman wa ta'zhiman wa birra",
        translation_id="Ya Allah, tambahkanlah kemuliaan, keagungan, kehormatan, dan kewibawaan rumah ini. Dan tambahkanlah kemuliaan, kehormatan, keagungan, dan kebaikan kepada orang yang memuliakannya dari mereka yang berhaji atau berumrah kepadanya.",
        translation_en="O Allah, increase this House in honor, reverence, respect, and awe. And increase in honor, respect, reverence, and righteousness those who honor it among those who perform Hajj or Umrah to it.",
        category=DoaCategory.TAWAF,
        when_to_read="Pertama kali melihat Ka'bah",
        location="Masjidil Haram"
    ),
    Doa(
        id="doa_021",
        name="Doa di Hajar Aswad (Istilam)",
        arabic="بِسْمِ اللهِ وَاللهُ أَكْبَرُ",
        latin="Bismillahi wallahu akbar",
        translation_id="Dengan nama Allah, Allah Maha Besar.",
        translation_en="In the name of Allah, Allah is the Greatest.",
        category=DoaCategory.TAWAF,
        when_to_read="Saat menghadap/menyentuh Hajar Aswad di setiap putaran",
        location="Hajar Aswad",
        is_wajib=True
    ),
    Doa(
        id="doa_022",
        name="Doa Antara Rukun Yamani dan Hajar Aswad",
        arabic="رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الْآخِرَةِ حَسَنَةً وَقِنَا عَذَابَ النَّارِ",
        latin="Rabbana atina fid-dunya hasanah, wa fil akhirati hasanah, wa qina 'adzaban-nar",
        translation_id="Ya Tuhan kami, berilah kami kebaikan di dunia dan kebaikan di akhirat, dan lindungilah kami dari siksa api neraka.",
        translation_en="Our Lord, give us good in this world and good in the Hereafter, and save us from the torment of the Fire.",
        category=DoaCategory.TAWAF,
        when_to_read="Antara Rukun Yamani dan Hajar Aswad (setiap putaran)",
        location="Antara Rukun Yamani dan Hajar Aswad",
        is_wajib=True,
        source="Al-Baqarah: 201"
    ),
    Doa(
        id="doa_023",
        name="Doa Setelah Tawaf (Minum Zamzam)",
        arabic="اللَّهُمَّ إِنِّي أَسْأَلُكَ عِلْمًا نَافِعًا وَرِزْقًا طَيِّبًا وَعَمَلًا مُتَقَبَّلًا",
        latin="Allahumma inni as'aluka 'ilman nafi'an, wa rizqan thayyiban, wa 'amalan mutaqabbalan",
        translation_id="Ya Allah, aku memohon kepada-Mu ilmu yang bermanfaat, rizki yang halal, dan amal yang diterima.",
        translation_en="O Allah, I ask You for beneficial knowledge, good provision, and accepted deeds.",
        category=DoaCategory.TAWAF,
        when_to_read="Setelah selesai tawaf, saat minum air zamzam",
        location="Zamzam",
        source="Ibn Majah"
    ),
    Doa(
        id="doa_024",
        name="Doa di Multazam",
        arabic="اللَّهُمَّ يَا رَبَّ الْبَيْتِ الْعَتِيقِ، أَعْتِقْ رِقَابَنَا وَرِقَابَ آبَائِنَا وَأُمَّهَاتِنَا وَإِخْوَانِنَا وَأَوْلَادِنَا مِنَ النَّارِ",
        latin="Allahumma ya rabbal baytil 'atiq, a'tiq riqabana wa riqaba aba'ina wa ummahatina wa ikhwanina wa awladina minan-nar",
        translation_id="Ya Allah, wahai Tuhan pemilik Baitullah, bebaskanlah kami, orang tua kami, saudara-saudara kami, dan anak-anak kami dari api neraka.",
        translation_en="O Allah, Lord of the Ancient House, free us, our parents, our siblings, and our children from the Fire.",
        category=DoaCategory.TAWAF,
        when_to_read="Di Multazam (antara pintu Ka'bah dan Hajar Aswad)",
        location="Multazam",
        is_sunnah=True
    ),

    # === SAI ===
    Doa(
        id="doa_030",
        name="Doa di Bukit Shafa (Awal Sa'i)",
        arabic="إِنَّ الصَّفَا وَالْمَرْوَةَ مِنْ شَعَائِرِ اللهِ، أَبْدَأُ بِمَا بَدَأَ اللهُ بِهِ",
        latin="Innas-shafa wal marwata min sya'a'irillah, abda'u bima bada'allahu bih",
        translation_id="Sesungguhnya Shafa dan Marwah adalah sebagian dari syiar-syiar Allah. Aku mulai dengan apa yang Allah mulai.",
        translation_en="Indeed, Safa and Marwa are among the symbols of Allah. I begin with what Allah began with.",
        category=DoaCategory.SAI,
        when_to_read="Saat naik ke bukit Shafa (pertama kali saja)",
        location="Bukit Shafa",
        is_wajib=True,
        source="Al-Baqarah: 158"
    ),
    Doa(
        id="doa_031",
        name="Doa di Shafa dan Marwah",
        arabic="اللهُ أَكْبَرُ اللهُ أَكْبَرُ اللهُ أَكْبَرُ وَلِلَّهِ الْحَمْدُ، لَا إِلَهَ إِلَّا اللهُ وَحْدَهُ لَا شَرِيكَ لَهُ، لَهُ الْمُلْكُ وَلَهُ الْحَمْدُ يُحْيِي وَيُمِيتُ وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ، لَا إِلَهَ إِلَّا اللهُ وَحْدَهُ أَنْجَزَ وَعْدَهُ وَنَصَرَ عَبْدَهُ وَهَزَمَ الْأَحْزَابَ وَحْدَهُ",
        latin="Allahu akbar, Allahu akbar, Allahu akbar wa lillahil hamd. Laa ilaha illallahu wahdahu laa syarika lah, lahul mulku wa lahul hamdu yuhyi wa yumitu wa huwa 'ala kulli syai'in qadir. Laa ilaha illallahu wahdahu anjaza wa'dahu wa nashara 'abdahu wa hazamal ahzaba wahdah",
        translation_id="Allah Maha Besar (3x) dan segala puji bagi Allah. Tidak ada Tuhan selain Allah Yang Maha Esa, tidak ada sekutu bagi-Nya. Milik-Nya kerajaan dan pujian, Dia menghidupkan dan mematikan, dan Dia Maha Kuasa atas segala sesuatu. Tidak ada Tuhan selain Allah Yang Maha Esa, Dia telah menepati janji-Nya, menolong hamba-Nya, dan mengalahkan golongan-golongan musuh sendirian.",
        translation_en="Allah is the Greatest (3x) and all praise is for Allah. There is no god but Allah alone, without partner. To Him belongs dominion and praise, He gives life and death, and He is Powerful over all things. There is no god but Allah alone, He fulfilled His promise, supported His servant, and defeated the confederates alone.",
        category=DoaCategory.SAI,
        when_to_read="Di atas bukit Shafa dan Marwah (diulang 3x)",
        location="Bukit Shafa dan Marwah",
        source="Muslim"
    ),

    # === MASJID ===
    Doa(
        id="doa_040",
        name="Doa Masuk Masjid",
        arabic="اللَّهُمَّ افْتَحْ لِي أَبْوَابَ رَحْمَتِكَ",
        latin="Allahummaf-tah li abwaba rahmatik",
        translation_id="Ya Allah, bukakanlah untukku pintu-pintu rahmat-Mu.",
        translation_en="O Allah, open for me the doors of Your mercy.",
        category=DoaCategory.MASJID,
        when_to_read="Saat masuk Masjidil Haram/Nabawi",
        location="Pintu Masjid",
        source="Muslim"
    ),
    Doa(
        id="doa_041",
        name="Doa Keluar Masjid",
        arabic="اللَّهُمَّ إِنِّي أَسْأَلُكَ مِنْ فَضْلِكَ",
        latin="Allahumma inni as'aluka min fadlik",
        translation_id="Ya Allah, aku memohon karunia-Mu.",
        translation_en="O Allah, I ask You for Your bounty.",
        category=DoaCategory.MASJID,
        when_to_read="Saat keluar dari masjid",
        location="Pintu Masjid",
        source="Muslim"
    ),

    # === HARIAN ===
    Doa(
        id="doa_050",
        name="Doa Sebelum Makan",
        arabic="بِسْمِ اللهِ وَعَلَى بَرَكَةِ اللهِ",
        latin="Bismillahi wa 'ala barakatillah",
        translation_id="Dengan nama Allah dan dengan berkah Allah.",
        translation_en="In the name of Allah and with the blessing of Allah.",
        category=DoaCategory.HARIAN,
        when_to_read="Sebelum makan",
        location="Mana saja"
    ),
    Doa(
        id="doa_051",
        name="Doa Setelah Makan",
        arabic="الْحَمْدُ لِلهِ الَّذِي أَطْعَمَنَا وَسَقَانَا وَجَعَلَنَا مُسْلِمِينَ",
        latin="Alhamdulillahilladzi ath'amana wa saqana wa ja'alana muslimin",
        translation_id="Segala puji bagi Allah yang telah memberi kami makan dan minum, serta menjadikan kami orang-orang muslim.",
        translation_en="All praise is for Allah who fed us and gave us drink and made us Muslims.",
        category=DoaCategory.HARIAN,
        when_to_read="Setelah makan",
        location="Mana saja"
    ),
    Doa(
        id="doa_052",
        name="Doa Sebelum Tidur",
        arabic="بِاسْمِكَ اللَّهُمَّ أَمُوتُ وَأَحْيَا",
        latin="Bismika Allahumma amutu wa ahya",
        translation_id="Dengan nama-Mu ya Allah, aku mati dan aku hidup.",
        translation_en="In Your name O Allah, I die and I live.",
        category=DoaCategory.HARIAN,
        when_to_read="Sebelum tidur",
        location="Kamar hotel"
    ),
    Doa(
        id="doa_053",
        name="Doa Bangun Tidur",
        arabic="الْحَمْدُ لِلهِ الَّذِي أَحْيَانَا بَعْدَ مَا أَمَاتَنَا وَإِلَيْهِ النُّشُورُ",
        latin="Alhamdulillahilladzi ahyana ba'da ma amatana wa ilaihin-nusyur",
        translation_id="Segala puji bagi Allah yang telah menghidupkan kami setelah mematikan kami, dan kepada-Nya kami dibangkitkan.",
        translation_en="All praise is for Allah who gave us life after death, and to Him is the resurrection.",
        category=DoaCategory.HARIAN,
        when_to_read="Setelah bangun tidur",
        location="Kamar hotel"
    ),

    # === ZIARAH ===
    Doa(
        id="doa_060",
        name="Salam di Makam Rasulullah",
        arabic="السَّلَامُ عَلَيْكَ يَا رَسُولَ اللهِ، السَّلَامُ عَلَيْكَ يَا نَبِيَّ اللهِ، السَّلَامُ عَلَيْكَ يَا خَيْرَ خَلْقِ اللهِ، أَشْهَدُ أَنَّكَ قَدْ بَلَّغْتَ الرِّسَالَةَ وَأَدَّيْتَ الْأَمَانَةَ وَنَصَحْتَ الْأُمَّةَ",
        latin="Assalamu 'alaika ya Rasulallah, assalamu 'alaika ya Nabiyyallah, assalamu 'alaika ya khaira khalqillah. Asyhadu annaka qad ballaghtar-risalah wa addaital-amanah wa nasahtal-ummah",
        translation_id="Salam sejahtera atasmu wahai Rasulullah, salam sejahtera atasmu wahai Nabi Allah, salam sejahtera atasmu wahai sebaik-baik makhluk Allah. Aku bersaksi bahwa engkau telah menyampaikan risalah, menunaikan amanah, dan menasehati umat.",
        translation_en="Peace be upon you O Messenger of Allah, peace be upon you O Prophet of Allah, peace be upon you O best of Allah's creation. I bear witness that you have conveyed the message, fulfilled the trust, and advised the nation.",
        category=DoaCategory.ZIARAH,
        when_to_read="Di depan makam Rasulullah SAW",
        location="Masjid Nabawi - Makam Rasulullah"
    ),
    Doa(
        id="doa_061",
        name="Doa Setelah Umrah (Tahallul)",
        arabic="الْحَمْدُ لِلَّهِ الَّذِي بِنِعْمَتِهِ تَتِمُّ الصَّالِحَاتُ",
        latin="Alhamdulillahilladzi bini'matihi tatimmus-shalihat",
        translation_id="Segala puji bagi Allah yang dengan nikmat-Nya sempurnalah segala amal shalih.",
        translation_en="All praise is for Allah, by whose grace good deeds are completed.",
        category=DoaCategory.ZIARAH,
        when_to_read="Setelah selesai umrah (tahallul)",
        location="Setelah potong rambut"
    ),

    # === RAWDAH ===
    Doa(
        id="doa_070",
        name="Doa di Raudhah",
        arabic="اللَّهُمَّ إِنِّي أَسْأَلُكَ الْجَنَّةَ وَأَعُوذُ بِكَ مِنَ النَّارِ",
        latin="Allahumma inni as'alukal jannah wa a'udzu bika minan-nar",
        translation_id="Ya Allah, aku memohon surga kepada-Mu dan aku berlindung kepada-Mu dari api neraka.",
        translation_en="O Allah, I ask You for Paradise and seek refuge in You from the Fire.",
        category=DoaCategory.RAWDAH,
        when_to_read="Saat berada di Raudhah",
        location="Raudhah - Masjid Nabawi",
        source="Abu Dawud"
    ),
]

# =============================================================================
# HISTORICAL SITES
# =============================================================================

HISTORICAL_SITES: List[HistoricalSite] = [
    # Makkah Sites
    HistoricalSite(
        name="Jabal Rahmah (Mount of Mercy)",
        name_ar="جبل الرحمة",
        city="MAKKAH",
        description="The mountain in Arafah where Prophet Adam and Hawa met after descending from Paradise.",
        significance="Site of Prophet Muhammad's Farewell Sermon",
        visiting_tips="Best visited during Hajj season or when visiting Arafah"
    ),
    HistoricalSite(
        name="Jabal Nur (Cave of Hira)",
        name_ar="جبل النور (غار حراء)",
        city="MAKKAH",
        description="The mountain containing Cave Hira where Prophet Muhammad received the first revelation.",
        significance="Site of the first Quranic revelation",
        visiting_tips="Climbing takes about 1-2 hours. Best visited early morning"
    ),
    HistoricalSite(
        name="Jabal Tsur (Cave of Thawr)",
        name_ar="جبل ثور",
        city="MAKKAH",
        description="The cave where Prophet Muhammad and Abu Bakr hid during the Hijrah to Madinah.",
        significance="Mentioned in Quran: 'The second of two when they were in the cave'",
        visiting_tips="Located south of Makkah, climbing is difficult"
    ),
    HistoricalSite(
        name="Mina",
        name_ar="منى",
        city="MAKKAH",
        description="Valley where pilgrims stay during Hajj and perform the stoning ritual.",
        significance="Site of the stoning of the Jamarat",
        visiting_tips="Visited during Hajj days (8-13 Dhul Hijjah)"
    ),
    HistoricalSite(
        name="Muzdalifah",
        name_ar="مزدلفة",
        city="MAKKAH",
        description="Open area between Arafah and Mina where pilgrims spend the night during Hajj.",
        significance="Site for collecting pebbles and night prayer",
        visiting_tips="Visited on the night of 9th Dhul Hijjah"
    ),
    HistoricalSite(
        name="Zamzam Well",
        name_ar="بئر زمزم",
        city="MAKKAH",
        description="The miraculous well that sprang for Hajar and Ismail in the desert.",
        significance="Blessed water mentioned by Prophet Muhammad",
        visiting_tips="Zamzam water is available throughout the Grand Mosque"
    ),

    # Madinah Sites
    HistoricalSite(
        name="Masjid Quba",
        name_ar="مسجد قباء",
        city="MADINAH",
        description="The first mosque built in Islam, constructed by Prophet Muhammad upon arriving in Madinah.",
        significance="Prayer here equals reward of Umrah (Ibn Majah: 1181)",
        visiting_tips="Best visited on Saturday following the Sunnah. Open 24 hours."
    ),
    HistoricalSite(
        name="Masjid Qiblatain",
        name_ar="مسجد القبلتين",
        city="MADINAH",
        description="The mosque where the Qibla was changed from Jerusalem to Makkah during prayer.",
        significance="Site of the change of Qibla direction",
        visiting_tips="Historical mosque, regular prayers held"
    ),
    HistoricalSite(
        name="Uhud Mountain",
        name_ar="جبل أحد",
        city="MADINAH",
        description="Site of the Battle of Uhud where many companions were martyred.",
        significance="Prophet said: 'Uhud is a mountain that loves us and we love it'",
        visiting_tips="Visit the martyrs' cemetery (Shuhada Uhud)"
    ),
    HistoricalSite(
        name="Al-Baqi Cemetery",
        name_ar="البقيع",
        city="MADINAH",
        description="The main cemetery of Madinah where many companions and family of Prophet are buried.",
        significance="Burial place of Prophet's family and companions",
        visiting_tips="Open after Fajr and Asr prayers for men. Located next to Masjid Nabawi."
    ),
    HistoricalSite(
        name="Masjid Al-Ghamama",
        name_ar="مسجد الغمامة",
        city="MADINAH",
        description="Mosque where Prophet Muhammad prayed Eid prayer, and a cloud shaded him.",
        significance="Site of Prophet's Eid prayers",
        visiting_tips="Located near Masjid Nabawi"
    ),
]

# =============================================================================
# UMRAH PROCEDURES
# =============================================================================

UMRAH_PROCEDURES: List[UmrahProcedure] = [
    UmrahProcedure(
        step=1,
        name="Persiapan & Niat",
        name_ar="التحضير والنية",
        description="Persiapan sebelum berangkat termasuk mendapatkan visa, tiket, dan niat yang ikhlas.",
        location="Negara asal",
        is_pillar=False,
        is_obligatory=False,
        tips=[
            "Pastikan paspor masih berlaku minimal 6 bulan",
            "Daftar melalui platform Nusuk atau agen resmi",
            "Siapkan pakaian ihram (untuk pria)",
            "Pelajari bacaan-bacaan wajib"
        ]
    ),
    UmrahProcedure(
        step=2,
        name="Ihram di Miqat",
        name_ar="الإحرام من الميقات",
        description="Masuk ke keadaan ihram dengan mandi, memakai pakaian ihram (pria), dan mengucapkan niat.",
        location="Miqat sesuai arah kedatangan",
        is_pillar=True,
        is_obligatory=True,
        tips=[
            "Mandi sunnah sebelum ihram",
            "Pakai wewangian sebelum ihram (tidak setelahnya)",
            "Niat dengan mengucapkan: Labbaika Allahumma 'Umratan",
            "Mulai membaca talbiyah dengan suara keras (pria)"
        ],
        doas=["doa_010", "doa_011"],
        sunnahs=["Mandi", "Memakai wewangian", "Shalat 2 rakaat"]
    ),
    UmrahProcedure(
        step=3,
        name="Tawaf (7 Putaran)",
        name_ar="الطواف",
        description="Mengelilingi Ka'bah sebanyak 7 kali dimulai dari Hajar Aswad, berlawanan arah jarum jam.",
        location="Masjidil Haram - Ka'bah",
        is_pillar=True,
        is_obligatory=True,
        tips=[
            "Mulai dari garis coklat sejajar Hajar Aswad",
            "Berjalan berlawanan arah jarum jam",
            "Ka'bah harus selalu di sebelah kiri",
            "Idhtiba' (buka bahu kanan) untuk pria",
            "Ramal (jalan cepat) di 3 putaran pertama untuk pria"
        ],
        doas=["doa_020", "doa_021", "doa_022", "doa_024"],
        sunnahs=["Idhtiba'", "Ramal", "Mencium Hajar Aswad", "Doa di Multazam"]
    ),
    UmrahProcedure(
        step=4,
        name="Shalat 2 Rakaat di Maqam Ibrahim",
        name_ar="صلاة ركعتين خلف المقام",
        description="Shalat 2 rakaat sunnah di belakang Maqam Ibrahim setelah selesai tawaf.",
        location="Belakang Maqam Ibrahim",
        is_pillar=False,
        is_obligatory=True,
        tips=[
            "Baca Al-Kafirun di rakaat pertama",
            "Baca Al-Ikhlas di rakaat kedua",
            "Jika tidak bisa di Maqam, boleh di mana saja dalam masjid",
            "Setelah shalat, minum air Zamzam"
        ],
        doas=["doa_023"]
    ),
    UmrahProcedure(
        step=5,
        name="Sa'i (7 Kali Safa-Marwah)",
        name_ar="السعي",
        description="Berjalan dari Safa ke Marwah dan sebaliknya sebanyak 7 kali (berakhir di Marwah).",
        location="Mas'a (antara Safa dan Marwah)",
        is_pillar=True,
        is_obligatory=True,
        tips=[
            "Mulai dari Safa, berakhir di Marwah",
            "Safa ke Marwah = 1 kali, Marwah ke Safa = 1 kali",
            "Total 7 kali (4 di Marwah, 3 di Safa)",
            "Pria berlari kecil di antara tanda hijau"
        ],
        doas=["doa_030", "doa_031"],
        sunnahs=["Naik ke Safa/Marwah", "Berdoa menghadap Ka'bah", "Berlari kecil di tanda hijau (pria)"]
    ),
    UmrahProcedure(
        step=6,
        name="Tahallul (Potong/Cukur Rambut)",
        name_ar="التحلل",
        description="Mencukur atau memotong rambut untuk keluar dari ihram.",
        location="Barbershop di sekitar Masjidil Haram",
        is_pillar=True,
        is_obligatory=True,
        tips=[
            "Pria: cukur habis (lebih utama) atau potong pendek",
            "Wanita: potong ujung rambut sepanjang 1 ruas jari",
            "Setelah tahallul, semua larangan ihram sudah halal",
            "Bisa dilakukan sendiri atau di barbershop"
        ],
        doas=["doa_061"]
    ),
]

# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    # Enums
    "UmrahStep",
    "DoaCategory",
    # Data Classes
    "Doa",
    "UmrahProcedure",
    "Miqat",
    "HistoricalSite",
    # Data
    "UMRAH_DEFINITION",
    "UMRAH_VIRTUES",
    "UMRAH_PILLARS",
    "UMRAH_SUNNAHS",
    "MIQAT_LOCATIONS",
    "UMRAH_DOAS",
    "HISTORICAL_SITES",
    "UMRAH_PROCEDURES",
]
