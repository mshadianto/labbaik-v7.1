-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- === MASTER ===
CREATE TABLE IF NOT EXISTS hotels_master (
  hotel_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  city TEXT NOT NULL CHECK (city IN ('MAKKAH','MADINAH')),
  address_raw TEXT,
  lat DOUBLE PRECISION,
  lon DOUBLE PRECISION,
  star_rating NUMERIC(2,1),
  chain TEXT,
  amenities_json JSONB DEFAULT '{}'::jsonb,
  distance_to_haram_m INTEGER,
  distance_to_nabawi_m INTEGER,
  walk_time_to_haram_min INTEGER,
  walk_time_to_nabawi_min INTEGER,
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_hotels_city_name ON hotels_master(city, name);

CREATE TABLE IF NOT EXISTS provider_hotel_map (
  hotel_id UUID REFERENCES hotels_master(hotel_id) ON DELETE CASCADE,
  provider TEXT NOT NULL,
  provider_hotel_id TEXT NOT NULL,
  confidence_score NUMERIC(5,2) DEFAULT 0,
  last_seen TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY (provider, provider_hotel_id)
);

CREATE INDEX IF NOT EXISTS idx_provider_map_hotel ON provider_hotel_map(hotel_id);

-- === QUERIES ===
CREATE TABLE IF NOT EXISTS search_queries (
  query_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  city TEXT NOT NULL CHECK (city IN ('MAKKAH','MADINAH')),
  checkin DATE NOT NULL,
  checkout DATE NOT NULL,
  adults INTEGER NOT NULL DEFAULT 2,
  children INTEGER NOT NULL DEFAULT 0,
  currency TEXT NOT NULL DEFAULT 'SAR',
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_queries_city_dates ON search_queries(city, checkin, checkout);

-- === OFFERS ===
CREATE TABLE IF NOT EXISTS offers (
  offer_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  hotel_id UUID REFERENCES hotels_master(hotel_id) ON DELETE CASCADE,
  provider TEXT NOT NULL,
  query_id UUID REFERENCES search_queries(query_id) ON DELETE CASCADE,
  room_name TEXT,
  board_type TEXT,
  refundability TEXT,
  price_total NUMERIC(14,2),
  price_per_night NUMERIC(14,2),
  taxes_fees NUMERIC(14,2),
  availability_status TEXT,
  fetched_at TIMESTAMPTZ DEFAULT now(),
  raw_payload JSONB
);

CREATE INDEX IF NOT EXISTS idx_offers_hotel_time ON offers(hotel_id, fetched_at DESC);
CREATE INDEX IF NOT EXISTS idx_offers_query ON offers(query_id);

-- Optional daily cache
CREATE TABLE IF NOT EXISTS availability_calendar (
  hotel_id UUID REFERENCES hotels_master(hotel_id) ON DELETE CASCADE,
  provider TEXT NOT NULL,
  date DATE NOT NULL,
  min_price NUMERIC(14,2),
  status TEXT,
  fetched_at TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY (hotel_id, provider, date)
);

-- === TRANSPORT (aligned with schema_v1_3.sql) ===
CREATE TABLE IF NOT EXISTS transport_schedule (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  operator TEXT NOT NULL,
  mode TEXT NOT NULL CHECK (mode IN ('TRAIN','BUS')),
  route TEXT NOT NULL,
  depart_time_local TIMESTAMPTZ,
  arrive_time_local TIMESTAMPTZ,
  duration_min INTEGER,
  price_sar NUMERIC(10, 2),
  class TEXT,
  availability TEXT,
  source_url TEXT,
  source_method TEXT,
  payload JSONB,
  fetched_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_transport_schedule_route ON transport_schedule(operator, route, fetched_at DESC);
CREATE INDEX IF NOT EXISTS idx_transport_schedule_depart ON transport_schedule(depart_time_local);

-- === OPS ===
CREATE TABLE IF NOT EXISTS crawl_jobs (
  job_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  type TEXT NOT NULL,
  payload JSONB NOT NULL,
  status TEXT NOT NULL DEFAULT 'queued',
  run_at TIMESTAMPTZ DEFAULT now(),
  created_at TIMESTAMPTZ DEFAULT now(),
  last_error TEXT
);

CREATE INDEX IF NOT EXISTS idx_jobs_status_run ON crawl_jobs(status, run_at);

CREATE TABLE IF NOT EXISTS crawl_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  job_id UUID REFERENCES crawl_jobs(job_id) ON DELETE CASCADE,
  provider TEXT,
  ok BOOLEAN DEFAULT false,
  http_code INTEGER,
  latency_ms INTEGER,
  error TEXT,
  ts TIMESTAMPTZ DEFAULT now()
);
