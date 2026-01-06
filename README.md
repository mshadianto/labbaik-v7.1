# LABBAIK Smart Planner v7.6

### Satu-satunya AI Companion untuk Umrah Anda

**Enterprise Edition** - *Platform AI Perencanaan Umrah #1 di Indonesia*

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://postgresql.org)
[![Railway](https://img.shields.io/badge/Railway-Deployed-blueviolet.svg)](https://railway.app)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Live Demo:** [app.labbaik.io](https://app.labbaik.io)

---

## Daftar Isi

1. [Tentang Project](#tentang-project)
2. [Smart Pillars](#smart-pillars)
3. [Fitur Unggulan](#fitur-unggulan)
4. [Tech Stack](#tech-stack)
5. [Struktur Project](#struktur-project)
6. [Instalasi](#instalasi)
7. [Deployment](#deployment)
8. [Konfigurasi](#konfigurasi)
9. [User Roles & Access Control](#user-roles--access-control)
10. [API Documentation](#api-documentation)
11. [Roadmap](#roadmap)

---

## Tentang Project

**LABBAIK Smart Planner** adalah platform inovatif berbasis Kecerdasan Buatan (AI) yang dirancang untuk mendampingi umat Muslim Indonesia dalam merencanakan perjalanan Umrah. Dengan semangat **DYOR (Do Your Own Research)**, kami menyediakan ekosistem digital yang transparan, informatif, dan aman.

### Visi & Misi

* **Visi:** Menjadi kompas digital utama bagi jamaah Umrah di seluruh Indonesia
* **Misi:** Digitalisasi manasik, transparansi biaya, dan peningkatan keamanan jamaah melalui teknologi AI

### Keunggulan Utama

* **AI Assistant** - Konsultasi ibadah & logistik 24/7 dengan RAG
* **Smart Pricing** - Perbandingan harga real-time multi-platform
* **Knowledge Base** - Panduan lengkap umrah, tips hemat, hidden gems
* **Partner API** - REST API untuk integrasi travel agent
* **Analytics Dashboard** - Real-time user engagement metrics

---

## Smart Pillars

LABBAIK Smart Planner dibangun di atas 3 pilar utama:

### Smart Prep
Persiapan cerdas sebelum berangkat:
- AI Chat Assistant untuk konsultasi
- Panduan manasik lengkap
- Checklist persiapan dokumen
- Tips packing & kesehatan

### Smart Savings
Hemat hingga 30% biaya umrah:
- Cost Simulator dengan breakdown lengkap
- **Pusat Harga** - Bandingkan hotel (200+ OTA), penerbangan & paket umrah
- Smart Nudge untuk penghematan grup
- Umrah Bareng matching system

### Smart Journey
Perjalanan yang aman & nyaman:
- 3D Manasik visualization
- Crowd Prediction Masjidil Haram
- SOS Emergency dengan GPS
- Real-time tracking (Premium)

---

## Fitur Unggulan

### Core Features

| Fitur | Deskripsi |
|-------|-----------|
| **AI Chat Assistant** | Tanya jawab seputar umrah dengan AI berbasis RAG (Groq/OpenAI) |
| **Cost Simulator** | Kalkulasi budget dengan breakdown lengkap & smart nudge |
| **Pusat Harga** | Bandingkan harga hotel (200+ OTA), penerbangan & paket umrah |
| **Umrah Bareng** | Social matching untuk umrah berkelompok |
| **Crowd Prediction** | Prediksi kepadatan Masjidil Haram & Nabawi |
| **3D Manasik** | Visualisasi tawaf dan sa'i interaktif |

### Premium Features

| Fitur | Deskripsi |
|-------|-----------|
| **Real-time Tracking** | Pantau posisi jamaah rombongan |
| **SOS Emergency** | Tombol darurat dengan lokasi GPS |
| **Unlimited Chat** | Tanpa batas konsultasi AI |
| **Priority Support** | Dukungan prioritas |

### Admin Features

| Fitur | Deskripsi |
|-------|-----------|
| **Analytics Dashboard** | User engagement, pillar usage, conversions |
| **User Management** | Kelola user dan roles |
| **System Monitoring** | Health checks dan logs |

### Partner Features

| Fitur | Deskripsi |
|-------|-----------|
| **Partner Dashboard** | Kelola paket dan booking |
| **Package Builder** | Rancang paket umrah dengan kalkulasi margin |
| **Travel CRM** | Kelola lead, booking, pembayaran, jamaah |
| **REST API** | Integrasi sistem booking |

### Intelligence Services

| Service | Deskripsi |
|---------|-----------|
| **Name Normalization** | Arabic/Latin transliteration untuk matching |
| **Currency Conversion** | Multi-currency (SAR, IDR, USD, dll) |
| **Risk Score** | Prediksi sold-out hotel (0-100) |
| **Peak Season Detection** | Deteksi musim ramai otomatis |

---

## Tech Stack

### Core Technology

| Component | Technology |
|-----------|------------|
| Language | Python 3.10+ |
| Framework | Streamlit 1.28+ |
| Database | PostgreSQL (Supabase/Neon) |
| Hosting | Railway |
| Domain | labbaik.io |

### AI & Services

| Component | Technology |
|-----------|------------|
| LLM Engine | Groq (Llama 3.3 70B) / OpenAI (GPT-4o) |
| Vector DB | ChromaDB |
| Orchestration | LangChain |
| Analytics | Custom PostgreSQL tracking |

---

## Struktur Project

```
labbaik-v7/
├── app.py                      # Entry point & routing
├── requirements.txt            # Dependencies
├── railway.toml                # Railway deployment config
├── Procfile                    # Process configuration
│
├── ui/                         # User Interface
│   ├── pages/                  # Page components
│   │   ├── home.py             # Landing page
│   │   ├── chat.py             # AI Chat
│   │   ├── simulator.py        # Cost Simulator
│   │   ├── price_hub.py        # Unified price comparison (hotel/flight/package)
│   │   ├── umrah_bareng.py     # Social matching
│   │   ├── analytics_dashboard.py  # Admin analytics
│   │   └── ...
│   └── components/             # Reusable components
│
├── services/                   # Business Logic
│   ├── ai/                     # AI & RAG services
│   │   ├── chat_service.py     # Groq/OpenAI chat
│   │   └── base.py             # Base service class
│   ├── analytics/              # Analytics tracking
│   │   └── tracker.py          # Event & page tracking
│   ├── database/               # Database layer
│   │   └── repository.py       # PostgreSQL connection
│   ├── hotel/                  # Hotel price comparison (Makcorps API)
│   ├── price_aggregation/      # Multi-source price aggregation
│   ├── intelligence/           # Intelligence services
│   ├── user/                   # User management
│   └── subscription/           # Premium subscriptions
│
├── features/                   # Feature modules
│   ├── crowd_prediction.py
│   ├── manasik_3d.py
│   └── sos_emergency.py
│
├── config/                     # Configuration files
│   └── settings.yaml
│
├── sql/                        # Database schemas
│   ├── analytics_schema.sql    # Analytics tables
│   └── travel_crm_schema.sql   # CRM tables
│
├── scripts/                    # Utility scripts
│   ├── init_admin.py           # Admin initialization
│   └── run_analytics_migration.py  # Analytics schema setup
│
└── data/                       # Data & Knowledge
    └── knowledge/
```

---

## Instalasi

### 1. Clone Repository

```bash
git clone https://github.com/mshadianto/labbaik-v7.1.git
cd labbaik-v7.1
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup Database

```bash
# Run analytics migration
python scripts/run_analytics_migration.py

# Initialize admin user
python scripts/init_admin.py
```

### 5. Run Application

```bash
streamlit run app.py
```

---

## Deployment

### Railway (Production)

Project ini di-deploy di Railway dengan konfigurasi:

**railway.toml:**
```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "streamlit run app.py --server.port $PORT --server.address 0.0.0.0"
healthcheckPath = "/"
healthcheckTimeout = 300
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3
```

**Environment Variables di Railway:**
- `DATABASE_URL` - PostgreSQL connection string
- `GROQ_API_KEY` - Groq API key
- `OPENAI_API_KEY` - OpenAI key (optional)
- `ADMIN_EMAIL` - Admin email
- `ADMIN_PASSWORD` - Admin password

### Domain Setup

Domain `labbaik.io` dikonfigurasi dengan:
- `app.labbaik.io` → Railway deployment
- SSL/TLS otomatis via Railway

---

## Konfigurasi

### Environment Variables

Buat file `.streamlit/secrets.toml`:

```toml
# Database (Supabase/Neon PostgreSQL)
DATABASE_URL = "postgresql://user:pass@host:5432/dbname"

# AI Services
GROQ_API_KEY = "gsk_your_key"
OPENAI_API_KEY = "sk_your_key"  # Optional fallback

# Admin
ADMIN_EMAIL = "admin@labbaik.io"
ADMIN_PASSWORD = "secure_password"

# WhatsApp (WAHA) - Optional
WAHA_API_URL = "http://localhost:3000"
WAHA_SESSION = "Labbaik"

# Price Comparison APIs - Optional
MAKCORPS_API_KEY = "your_makcorps_key"  # Hotel price comparison
AMADEUS_API_KEY = "your_amadeus_key"
AMADEUS_API_SECRET = "your_amadeus_secret"
```

### Admin Setup

```bash
python scripts/init_admin.py
```

> **Security Note:** Jangan commit credentials ke repository!

---

## User Roles & Access Control

### Role Hierarchy

| Role | Level | Description |
|------|-------|-------------|
| GUEST | 0 | Visitor tanpa login |
| FREE | 1 | User terdaftar gratis |
| PREMIUM | 2 | Subscriber berbayar |
| PARTNER | 3 | Travel agent partner |
| ADMIN | 4 | Full access |

### Feature Access Matrix

| Feature | Guest | Free | Premium | Partner | Admin |
|---------|-------|------|---------|---------|-------|
| Home & Landing | Y | Y | Y | Y | Y |
| AI Chat | - | 10/day | Unlimited | Unlimited | Unlimited |
| Cost Simulator | Y | Y | Y | Y | Y |
| Pusat Harga | Y | Y | Full OTA | Full OTA | Full OTA |
| Umrah Bareng | - | Y | Y | Y | Y |
| Analytics Dashboard | - | - | - | - | Y |
| Partner Dashboard | - | - | - | Y | Y |

### Subscription Plans

| Plan | Price | Duration |
|------|-------|----------|
| Monthly | Rp 99,000 | 30 days |
| Quarterly | Rp 249,000 | 90 days |
| Yearly | Rp 799,000 | 365 days |

---

## API Documentation

### Base URL

```
https://api.labbaik.io/api/v1
```

### Authentication

```http
Authorization: Bearer lbk_live_xxxxxxxxxxxx
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/packages` | List all packages |
| GET | `/packages/{id}` | Get package detail |
| POST | `/bookings` | Create booking |
| GET | `/bookings/{code}` | Get booking status |
| GET | `/analytics/overview` | Partner analytics |

---

## Analytics

### Tracked Events

| Event Type | Category | Description |
|------------|----------|-------------|
| page_view | navigation | Page visits |
| pillar_view | navigation | Smart Pillar access |
| nudge_shown | smart_savings | Smart nudge displayed |
| nudge_clicked | smart_savings | Smart nudge click-through |
| conversion | conversions | Premium upgrade, UB match |
| feature_usage | features | Feature interactions |

### Excluded from Tracking

Internal team emails are excluded from analytics:
- admin@labbaik.io
- founder@labbaik.io
- salam@labbaik.io

---

## Roadmap

### Completed

- [x] v7.0 - Core platform & AI Chat
- [x] v7.1 - Brand refresh "LABBAIK Smart Planner"
- [x] v7.1.1 - Analytics Dashboard & Smart Nudge
- [x] v7.5 - Makcorps Hotel API integration
- [x] v7.6 - Unified Price Hub (hotel, flight, package comparison)

### Upcoming

- [ ] v7.7 - Enhanced Umrah Bareng matching algorithm
- [ ] v8.0 - Mobile app (React Native)

---

## Contributing

Kami mengundang developer untuk berkontribusi:

1. Fork repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

### Commit Convention

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `refactor:` - Code refactoring

---

## Team

**Lead Developer:** MS Hadianto

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

<div align="center">

### Doa Penutup

*"Ya Allah, mudahkanlah perjalanan umrah bagi siapa saja yang menggunakan platform ini. Jadikanlah ibadah mereka mabrur dan diterima di sisi-Mu. Aamiin."*

**Star repo ini jika bermanfaat!**

Made with love in Indonesia

</div>
