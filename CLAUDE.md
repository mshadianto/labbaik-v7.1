# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LABBAIK AI is a Streamlit-based AI platform for Umrah (Islamic pilgrimage) planning. It helps Indonesian Muslims plan their Umrah journey with features like AI chat, cost simulation, group matching, Travel CRM, and emergency SOS.

**Tech Stack:** Python 3.9+, Streamlit, PostgreSQL (Supabase), Groq/GLM-4/OpenAI LLM, ChromaDB for RAG

## Domain Structure

| URL | Platform | Purpose |
|-----|----------|---------|
| `https://labbaik.io` | Hostinger (WordPress) | Landing page, marketing, SEO |
| `https://app.labbaik.io` | Railway (Streamlit) | Main AI application |

**Email Addresses:**
- `admin@labbaik.io` - Admin login
- `founder@labbaik.io` - Business contact
- `salam@labbaik.io` - Customer support

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
core/           # Configuration, constants, exceptions, logging
services/       # Backend services (AI, database, analytics, WhatsApp)
  ai/           # LLM services (Groq, GLM-4, OpenAI) with provider abstraction
  database/     # PostgreSQL connection pool and repository pattern
  intelligence/ # Name normalization, pricing, risk scores
  umrah/        # Hotel/transport data fetching from multiple APIs
  user/         # User management and access control
  crm/          # Travel CRM (leads, bookings, jamaah, invoices)
  subscription/ # Premium subscription handling
  partner_api/  # REST API for travel agent partners
  hotel/        # Hotel price comparison (Makcorps API)
  scrapers/     # Web scrapers (Traveloka, Tiket.com)
features/       # Standalone feature modules (SOS, crowd prediction, etc.)
ui/pages/       # Streamlit page renderers
ui/components/  # Reusable UI components
data/           # Static data and knowledge bases
config/         # YAML configuration files
sql/            # Database schemas and migrations
scripts/        # Utility and initialization scripts
umrah-crawler/  # Separate FastAPI backend for data crawling
```

### Key Patterns

**Feature Flags:** Features are lazy-imported with try/except and `HAS_*` boolean flags (e.g., `HAS_CROWD_PREDICTION`). Check these flags before using features. See the imports section in `app.py` for the full list.

**Session State:** All state is managed via `st.session_state`. See `init_session_state()` in `app.py` for all keys including navigation, auth, chat, gamification, SOS, tracking, and more.

**Service Layer:**
- `services/ai/chat_service.py` - Multi-provider chat (Groq, GLM-4, OpenAI) with rate limiting
- `services/database/repository.py` - Database singleton with connection pooling
- `services/user/user_repository.py` - User CRUD with PostgreSQL/SQLite fallback
- `services/intelligence/` - Name normalization, currency conversion, risk scoring
- `services/hotel/makcorps.py` - Hotel price comparison across 200+ OTAs
- `services/price_aggregation/` - Price scraping and normalization

**Configuration:**
- Primary: Streamlit secrets (`.streamlit/secrets.toml`) and environment variables
- Secondary: `config/settings.yaml` (env vars override YAML values)
- Use `get_settings()` from `core/config.py` to access configuration

### AI Services

The AI layer uses a provider abstraction via `AIServiceFactory`:

| Provider | Model | Package |
|----------|-------|---------|
| `GroqChatService` | llama-3.3-70b-versatile | `groq` |
| `GLMChatService` | glm-4, glm-4-plus, glm-4-flash | `zhipuai` |
| `OpenAIChatService` | gpt-4o-mini | `openai` |

All extend `BaseChatService` from `services/ai/base.py`. Provider selection is available in the chat page sidebar - users can switch between providers in real-time. Additional services: `rag_service.py` (ChromaDB vector search), `speech_service.py` (text-to-speech).

### Travel CRM System

CRM modules for travel agent partners in `services/crm/`:
- Lead Management - Pipeline, follow-up tracking, activity log
- Booking Tracker - Status, payments, installments
- Jamaah Database - Pilgrim data, documents, history
- Quote/Invoice Generator - Automated pricing and billing

UI pages: `ui/pages/crm_*.py`

### User Roles & Access Control

Role hierarchy (see `services/user/access_control.py`):
- GUEST (0) → FREE (1) → PREMIUM (2) → PARTNER (3) → ADMIN (4)

Use `check_page_access(page)` to verify permissions before rendering premium features.

### Database

PostgreSQL (Supabase) with connection pooling. Uses pooler URL (port 6543) for serverless compatibility.

Connection string format:
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
- Gamification: Use `add_xp(amount, reason)` to award points
- New features: Add `HAS_*` flag in `app.py`, lazy-import with try/except

## Commit Message Format

Follow conventional commits:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks
