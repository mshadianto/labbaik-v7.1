# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LABBAIK Smart Planner is a Streamlit-based AI platform for Umrah (Islamic pilgrimage) planning. It helps Indonesian Muslims plan their Umrah journey with features like AI chat, cost simulation, hotel/flight price comparison, group matching, Travel CRM, gamification, guided onboarding, and emergency SOS.

**Tech Stack:** Python 3.9+, Streamlit, PostgreSQL (Supabase/Neon), Groq/GLM-4/OpenAI LLM, ChromaDB for RAG, hijri-converter

**Domains:** `labbaik.io` (Hostinger/WordPress landing page), `app.labbaik.io` (Railway/Streamlit app)

**Team emails (excluded from analytics):** `admin@labbaik.io`, `founder@labbaik.io`, `salam@labbaik.io`

## Common Commands

```bash
# Run the application
streamlit run app.py

# Install dependencies
pip install -r requirements.txt

# Run with virtual environment (Windows)
venv\Scripts\activate
streamlit run app.py

# Initialize admin user
python scripts/init_admin.py

# Initialize CRM database schema
python scripts/init_crm_schema.py

# Database migrations
python scripts/run_analytics_migration.py  # Analytics schema
python scripts/run_groups_migration.py     # Simulation groups

# Database maintenance
python scripts/run_optimize_indexes.py
python scripts/run_cleanup_data.py
```

### Database Setup (Supabase)

Run migrations in Supabase SQL Editor (in order):
```sql
sql/supabase_migration.sql        -- Core tables (users, sessions, visitors)
sql/analytics_schema.sql          -- Analytics and tracking
sql/travel_crm_schema.sql         -- CRM (leads, bookings, jamaah, invoices)
sql/schema_partners.sql           -- Partner system
sql/schema_v1_3.sql               -- v1.3 schema updates
sql/price_aggregation_schema.sql  -- Price aggregation
sql/simulation_groups_schema.sql  -- Group simulation/planning
sql/optimize_indexes.sql          -- Performance indexes
```

### Testing

No automated test suite exists. Manual testing via `streamlit run app.py`.

### Umrah Crawler (Separate FastAPI Backend)

```bash
cd umrah-crawler
uvicorn app.main:app --reload      # Run API server (port 8000)
python -m app.jobs                  # Background job scheduler
python -m app.jobs_v13              # v1.3 jobs (Haramain train, SAPTCO bus)
```

**Data Providers:** Amadeus (hotels/flights), Xotelo (hotel prices), Makcorps (hotel comparison), Agoda, Haramain (train), SAPTCO (bus), ECB (forex)

## Architecture

### Entry Point
- `app.py` - Main Streamlit application with lazy imports and feature flags. Handles routing, session state, and sidebar navigation.
- `core/version.py` - Version management (`APP_VERSION`, `get_display_version()`)

### Directory Structure

```
core/                   # Configuration, constants, exceptions, logging
services/               # Backend services
  ai/                   # LLM services (Groq, GLM-4, OpenAI) with provider abstraction
  analytics/            # Event/page tracking, visitor analytics, dashboard
  auth/                 # Authentication (auth_service.py)
  cost/                 # Cost calculator
  crm/                  # Travel CRM (leads, bookings, jamaah, invoices)
  database/             # PostgreSQL connection pool and repository pattern
  hotel/                # Hotel price comparison (Makcorps API)
  intelligence/         # Name normalization, pricing, risk scores, geo clustering
  notification/         # Notification service
  partner_api/          # REST API for travel agent partners
  price/                # Live prices, monitoring, price repository
  price_aggregation/    # Multi-source price aggregation, caching, scheduling
  referral/             # Referral/rewards system
  scrapers/             # Web scrapers (Traveloka, Tiket.com) with rate limiting
  subscription/         # Premium subscription handling
  umrah/                # Hotel/transport data fetching from multiple APIs
  user/                 # User management and access control
  audio/                # TTS service (edge-tts, gTTS) shared by doa_player & umrah_complete
  whatsapp/             # WAHA WhatsApp client
features/               # Standalone feature modules (SOS, crowd prediction, etc.)
ui/pages/               # Streamlit page renderers (40+ pages)
ui/components/          # Reusable UI components (shared_styles, price_widgets, crm_helpers)
data/                   # Static data and knowledge bases
config/                 # YAML configuration files
sql/                    # Database schemas and migrations
scripts/                # Utility and initialization scripts
umrah-crawler/          # Separate FastAPI backend for data crawling
  app/amadeus/          # Amadeus API client (auth, hotels, flights, transfers)
  app/providers/        # Data providers (Agoda, Xotelo, Makcorps, Haramain, SAPTCO, ECB forex)
  app/services/         # Healthcheck, itinerary generation
  app/utils/            # HTTP helpers, normalization, rate limiting
```

### Key Patterns

**Feature Flags:** Features are lazy-imported with try/except and `HAS_*` boolean flags in `app.py`. Check these flags before using features. Full list:
`HAS_ITINERARY`, `HAS_HOTEL_COMPARE`, `HAS_PRICE_HUB`, `HAS_CHECKLIST`, `HAS_READINESS`, `HAS_COST_TRACKER`, `HAS_TANYA_USTADZ`, `HAS_DOC_CHECKER`, `HAS_PETA`, `HAS_KURS`, `HAS_CROWD_PREDICTION`, `HAS_SOS`, `HAS_TRACKING`, `HAS_MANASIK`, `HAS_COMPARISON`, `HAS_ANALYTICS`, `HAS_USER_MANAGEMENT`, `HAS_SUBSCRIPTION`, `HAS_PARTNER_SYSTEM`, `HAS_CRM`, `HAS_PRICE_AGGREGATION`, `HAS_WHATSAPP`, `HAS_DOA_PLAYER`, `HAS_PWA`, `HAS_TRACKING_SERVICE`, `HAS_SETTINGS`

**Per-page feature flags** (used within individual pages via try/except imports):
`HAS_SEASON_CALENDAR`, `HAS_CROWD_PREDICTION`, `HAS_RISK_SCORE`, `HAS_GEO_CLUSTER`, `HAS_LIVE_PRICES`, `HAS_PRICE_MONITOR`, `HAS_PARTNER_API`, `HAS_HIJRI`, `HAS_ARABIC`, `HAS_PLOTLY`, `HAS_PANDAS`, `HAS_QRCODE`, `HAS_KURS_SERVICE`, `HAS_DB`

**Session State:** All state is managed via `st.session_state`. See `init_session_state()` in `app.py` for all keys including navigation, auth, chat, gamification (XP, level, badges, streak, weekly challenges), onboarding (guided tour), page feedback, notification preferences, and more.

**Singletons:** Both `DatabaseConnection` (`services/database/repository.py`) and `ConfigManager` (`core/config.py`) use the singleton pattern via `__new__`. Access via `get_db()` and `get_settings()` respectively.

**Service Layer:**
- `services/ai/chat_service.py` - Multi-provider chat (Groq, GLM-4, OpenAI) with rate limiting
- `services/ai/helpers.py` - `ai_complete()` auto-fallback, `add_xp_safe()` gamification helper
- `services/database/repository.py` - Database singleton with connection pooling (`get_db()`)
- `services/user/user_repository.py` - User CRUD with PostgreSQL/SQLite fallback
- `services/intelligence/` - Name normalization, currency conversion, risk scoring, geo clustering, season calendar
- `services/intelligence/season_calendar.py` - `SeasonCalendar` with `get_season()`, `get_weight()`, `get_booking_recommendation()`, `get_low_season_dates()` — wired to booking, simulator, home
- `services/intelligence/geo_cluster.py` - `deduplicate_hotels()`, `merge_hotel_data()` — wired to price_hub
- `services/intelligence/risk_score.py` - `get_risk_calculator()`, `RiskLevel` — wired to price_hub
- `services/hotel/makcorps.py` - Hotel price comparison across 200+ OTAs
- `services/price/monitoring.py` - `PriceMonitor`, `get_cached_health_status()` — wired to home
- `services/price/live_prices.py` - `LivePriceService.get_cheapest_packages()` — wired to chat, home
- `services/price_aggregation/` - Multi-source price scraping, normalization, caching, n8n adapter
- `services/notification/notification_service.py` - 10 notification templates (WhatsApp, email, in-app), `render_template()`, `WhatsAppTemplates`, `InAppTemplates`
- `services/analytics/tracker.py` - Event and page tracking (`track_page()`)

**Configuration:**
- Primary: Streamlit secrets (`.streamlit/secrets.toml`) and environment variables
- Secondary: `config/settings.yaml` (env vars override YAML values)
- Use `get_settings()` from `core/config.py` — returns a `Settings` dataclass with typed sub-configs: `DatabaseConfig`, `AIConfig`, `AuthConfig`, `UIConfig`, `UmrahDataConfig`, `PluginConfig`, `LoggingConfig`
- Environment: Set `LABBAIK_ENV` to `development`/`staging`/`production`/`testing`

### AI Services

The AI layer uses a provider abstraction via `AIServiceFactory`:

| Provider | Model | Package |
|----------|-------|---------|
| `GroqChatService` | llama-3.3-70b-versatile | `groq` |
| `GLMChatService` | glm-4, glm-4-plus, glm-4-flash | `zhipuai` |
| `OpenAIChatService` | gpt-4o-mini | `openai` |

All extend `BaseChatService` from `services/ai/base.py`. `AIServiceFactory` creates and caches service instances — use `create_chat_service(provider, api_key)`. Provider selection is available in the chat page sidebar. Additional services: `rag_service.py` (ChromaDB vector search with `all-MiniLM-L6-v2` embeddings), `speech_service.py` (text-to-speech via gTTS/edge-tts).

### Travel CRM System

CRM modules for travel agent partners in `services/crm/`:
- Lead Management - Pipeline, follow-up tracking, activity log
- Booking Tracker - Status, payments, installments
- Jamaah Database - Pilgrim data, documents, history
- Quote/Invoice Generator - Automated pricing and billing

UI pages: `ui/pages/crm_*.py` (leads with pagination, pipeline view, partner lead import)

### User Roles & Access Control

Role hierarchy (see `services/user/access_control.py`):
- GUEST (0) → FREE (1) → PREMIUM (2) → PARTNER (3) → ADMIN (4)

Use `check_page_access(page)` to verify permissions before rendering premium features. The `Feature` enum in `access_control.py` maps individual capabilities (e.g., `UNLIMITED_CHAT`, `GROUP_TRACKING`) to minimum required roles via the `FEATURE_ROLES` dict.

### Database

PostgreSQL (Supabase or Neon) with connection pooling via psycopg2. `DatabaseConnection` is a singleton — use `get_db()` from `services/database/repository.py`. Resolves the connection string from `DATABASE_URL` env var first, then falls back to Streamlit secrets.

Supabase pooler URL format (port 6543):
```
postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
```

## Environment Variables

**Required:**
- `DATABASE_URL` - PostgreSQL connection string (Supabase pooler URL, port 6543)

**AI Providers (at least one required):**
- `GROQ_API_KEY` - Groq API key
- `GLM_API_KEY` - Zhipu AI (GLM-4) key
- `OPENAI_API_KEY` - OpenAI key

**Admin:**
- `ADMIN_EMAIL` - Admin email (default: admin@labbaik.io)
- `ADMIN_PASSWORD` - Admin password

**Optional:**
- `WAHA_API_URL`, `WAHA_SESSION` - WhatsApp integration (WAHA self-hosted)
- `AMADEUS_API_KEY`, `AMADEUS_API_SECRET` - Amadeus hotel/flight API
- `RAPIDAPI_KEY` - RapidAPI key for Xotelo
- `MAKCORPS_API_KEY` - Makcorps hotel price comparison API

## Deployment

### Railway (Application)

App deployed at: `https://app.labbaik.io`

```bash
# Link project (if Railway CLI installed)
railway link
railway variables set KEY=value
railway logs
```

Environment variables are set in Railway dashboard. Local `secrets.toml` changes don't affect production.

### Hostinger (Landing Page)

WordPress landing page at: `https://labbaik.io`

DNS setup for subdomain:
```
CNAME  app  labbaik-v7-production.up.railway.app
```

## Conventions

- All UI text is in Indonesian (Bahasa Indonesia)
- Pages follow the pattern: `render_*_page()` functions in `ui/pages/`
- Feature modules export `render_*_page()` and `render_*_widget()` for sidebar
- Use `track_page(page_name)` for analytics
- Gamification: Use `add_xp(amount, reason)` to award points. `add_xp()` auto-checks achievement badges and logs to `xp_log`. Use `add_xp_safe()` from `services/ai/helpers.py` for safe non-throwing variant
- AI service pattern for new pages: use `ai_complete()` from `services/ai/helpers.py` (auto-handles provider fallback). Always wrap AI calls with skeleton loaders (`SKELETON_CSS` + `render_skeleton()`) and include graceful fallback when AI unavailable
- New features: Add `HAS_*` flag in `app.py`, lazy-import with try/except
- Cross-page navigation: Use `st.session_state.nav = "target_page"` + `st.rerun()` for page-to-page redirects
- WhatsApp sharing: Use `_build_wa_share_url(text)` helper → `https://wa.me/?text=ENCODED`
- Hijri dates: Import `hijri_converter.Gregorian` with `HAS_HIJRI` flag, use `_get_hijri_date_str(date)` helper
- Demo fallbacks: When API/service unavailable, show realistic demo data with "DATA DEMO" badge

## UX & Accessibility

The app follows WCAG AA guidelines and mobile-first responsive design:

**CSS Architecture (`ui/components/shared_styles.py`):**
- `inject_css()` auto-includes `RESPONSIVE_CSS` + `ACCESSIBILITY_CSS` on every page
- Available CSS blocks: `HERO_CSS`, `CARD_CSS`, `AI_CARD_CSS`, `PROGRESS_CSS`, `EMPTY_STATE_CSS`, `SKELETON_CSS`, `BADGE_CSS`, `RESPONSIVE_CSS`, `ACCESSIBILITY_CSS`
- `SKELETON_CSS` + `render_skeleton()` are opt-in — used on AI pages (readiness, doc_checker, tanya_ustadz) before `ai_complete()` calls

**Responsive Design:**
- 3 `@media` breakpoints: 768px (tablet), 480px (phone), `prefers-reduced-motion`
- Streamlit columns auto-wrap via `flex-wrap` on `[data-testid="column"]`
- Touch targets: min-height 44px (tablet), 48px (phone) for buttons/inputs

**Accessibility:**
- All AI response cards use `role="status" aria-live="polite"` (46 instances across 29 files)
- Decorative emoji in page heroes wrapped with `<span aria-hidden="true">`
- `focus-visible` outlines (2px solid #d4af37) on interactive elements
- Skip-to-content link (hidden until `:focus`)
- `prefers-reduced-motion` disables animations

**Contrast:**
- Never use `#888` on dark backgrounds — minimum `#b0b0b0` for WCAG AA (7:1 ratio)
- Secondary text: `#b0b0b0`, muted text: `#8e9fb3` or `#b8c5d4`

**Onboarding:**
- First-visit welcome banner with CTA buttons in `app.py`
- 5-step guided tour (session state key: `onboarding_step`, 0=not started, 1-5=active, 6=done)
- XP rewards: 10 XP for skipping tour, 25 XP for completing

**Form Validation (`ui/pages/auth_page.py`):**
- `validate_email()` — regex validation with Indonesian error messages
- `get_password_strength()` — 0-4 score with visual indicator
- Real-time feedback on form submission

## Gamification System

XP-based engagement system with levels, badges, and challenges:

**XP & Levels:**
- `add_xp(amount, reason)` in `app.py` — awards XP, logs to `xp_log`, tracks daily streak, auto-checks achievements
- Levels: XP // 100 → 0="Pemula", 1="Penjelajah", 2="Perencana", 3="Ahli", 4="Master", 5+="Legend"
- Sidebar shows: XP total, level badge, progress bar, streak counter, recent activities

**Achievement Badges (8):**
- Penjelajah Pertama (5 pages), Perencana Handal (readiness), Ahli Budget (cost tracker), Penghafal Doa (10 phrases), Pembanding Cerdas (3 hotels), Jamaah Sosial (WhatsApp share), Streak Master (3-day streak), Guru Manasik (manasik guide)
- Auto-checked on every `add_xp()` call via `check_achievements()`

**Weekly Challenges (5 rotating):**
- One challenge per week based on ISO week number
- Target pages: readiness, hotel_compare, simulator, chat, itinerary

**Page Feedback Widget:**
- `render_page_feedback()` in `app.py` — 5-star rating + optional comment on every page
- Shown once per page per session, stored in `st.session_state.page_feedback`

## Key Page Features

Summary of major features per page (post v7.8 enhancements):

| Page | Key Features |
|------|-------------|
| `home.py` | Hijri date, season countdown, featured deals, testimonials, live prices, data freshness, monitoring widget |
| `chat.py` | Multi-provider AI, Arabic flashcards (43 phrases), package recommendations, WhatsApp share, transcript export/search |
| `booking.py` | 7-step flow, season intelligence, Hijri display, AI tips, cost tracker sync, cross-page nav, WhatsApp share |
| `simulator.py` | Cost simulation, season price impact, save/compare 5 scenarios, PDF report, budget templates |
| `cost_tracker.py` | Budget setup, expense tracking, budget alerts (80%/100%), category donut chart, daily bars, budget vs actual, savings tracker, CSV export |
| `hotel_compare.py` | Amenity filtering, favorites/bookmarks (max 10), side-by-side comparison, demo fallback |
| `price_hub.py` | Risk scores, geo-cluster dedup, 30-day price history chart, live prices |
| `price_comparison.py` | Composite scoring (price/rating/reliability/value), source badges |
| `readiness_checker.py` | 4-dimension scoring, coaching plan with timeline, doc completion card, cross-page nav |
| `doc_checker.py` | 11 documents, departure-date timeline warnings, urgency grouping, AI tips with skeleton loader |
| `tanya_ustadz.py` | AI Q&A (Syafi'i), 18-entry fiqih database, search, history, helpful voting |
| `itinerary_builder.py` | AI itinerary, crowd warnings per activity, ICS/TXT/WA/JSON/PDF export, WhatsApp share |
| `smart_checklist.py` | AI item suggestions, 18 Tokopedia shopping links, priority badges |
| `peta_interaktif.py` | Interactive map, crowd prediction overlay (6 locations), time slider |
| `referral_page.py` | Milestones (4 tiers), leaderboard, QR code generator, friend tracking |
| `subscription_page.py` | Plan comparison (Free/Premium/VIP), billing history, upgrade/cancel flow |
| `group_matching.py` | Group discovery, 5-dimension compatibility scoring, in-app group chat |
| `partnership.py` | DB-wired registration, partner list, stats banner, pricing cards |
| `analytics_dashboard.py` | KPI overview, cohort retention matrix, activity heatmap, CSV/HTML export |
| `crm_leads.py` | Lead management with pagination, partner lead import, AI analysis |
| `settings_page.py` | Notification prefs, display mode, data management |
| `kurs_calculator.py` | Live exchange rates (open.er-api.com), 30-min cache, fallback to hardcoded |

## Notification Templates

`services/notification/notification_service.py` provides 10 ready-to-use templates:
`welcome`, `booking_confirmation`, `payment_reminder`, `doc_deadline`, `departure_reminder`, `group_invite`, `referral_reward`, `readiness_update`, `price_alert`, `manasik_reminder`

Use `render_template(template_id, context_dict)` to populate and get a `NotificationMessage`. `WhatsAppTemplates` and `InAppTemplates` classes provide channel-specific formatting.

## Commit Message Format

Follow conventional commits:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks
