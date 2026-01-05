-- ============================================================================
-- LABBAIK AI - Simulation Groups Schema
-- Family/Group Planning Feature for Umrah
-- ============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- SIMULATION GROUPS TABLE
-- Stores group metadata and simulation snapshot
-- ============================================================================
CREATE TABLE IF NOT EXISTS simulation_groups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    group_code VARCHAR(8) UNIQUE NOT NULL,  -- Format: "UMR" + 5 alphanumeric (e.g., "UMR1A2B3")
    name TEXT NOT NULL,                      -- Group name (e.g., "Keluarga Pak Ahmad")
    description TEXT,

    -- Target planning
    target_date DATE,                        -- Target departure date
    target_amount INTEGER,                   -- Total group target in IDR

    -- Simulation snapshot (stored as JSON)
    simulation_params JSONB,                 -- {departure_city, duration, hotel_stars, etc.}
    simulation_breakdown JSONB,              -- {flight, visa, hotel_makkah, hotel_madinah, etc.}
    cost_per_person INTEGER,                 -- Cost per person in IDR

    -- Leader/Owner info
    leader_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    leader_name TEXT,                        -- Cached for display without JOIN
    leader_phone TEXT,                       -- For WhatsApp contact

    -- Status management
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'cancelled')),
    is_public BOOLEAN DEFAULT FALSE,         -- Whether group is publicly discoverable

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_sim_groups_code ON simulation_groups(group_code);
CREATE INDEX IF NOT EXISTS idx_sim_groups_leader ON simulation_groups(leader_id);
CREATE INDEX IF NOT EXISTS idx_sim_groups_status ON simulation_groups(status);
CREATE INDEX IF NOT EXISTS idx_sim_groups_created ON simulation_groups(created_at DESC);

-- ============================================================================
-- GROUP MEMBERS TABLE
-- Tracks members and their contributions
-- ============================================================================
CREATE TABLE IF NOT EXISTS group_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    group_id UUID NOT NULL REFERENCES simulation_groups(id) ON DELETE CASCADE,

    -- Member identity (can be registered user or invited guest)
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,  -- NULL if not yet registered
    name TEXT NOT NULL,
    phone TEXT,                              -- For WhatsApp notifications
    email TEXT,

    -- Contribution tracking
    contribution_amount INTEGER DEFAULT 0,   -- Amount already saved/contributed
    contribution_target INTEGER,             -- Their personal target (defaults to cost_per_person)

    -- Role and status
    role TEXT DEFAULT 'member' CHECK (role IN ('leader', 'co_leader', 'member')),
    status TEXT DEFAULT 'invited' CHECK (status IN ('invited', 'active', 'declined', 'removed')),

    -- Timestamps
    joined_at TIMESTAMPTZ,                   -- When they accepted/activated
    invited_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),

    -- Prevent duplicate members (by phone or user_id within same group)
    CONSTRAINT unique_group_phone UNIQUE (group_id, phone),
    CONSTRAINT unique_group_user UNIQUE (group_id, user_id)
);

-- Indexes for member lookups
CREATE INDEX IF NOT EXISTS idx_group_members_group ON group_members(group_id);
CREATE INDEX IF NOT EXISTS idx_group_members_user ON group_members(user_id);
CREATE INDEX IF NOT EXISTS idx_group_members_phone ON group_members(phone);
CREATE INDEX IF NOT EXISTS idx_group_members_status ON group_members(status);

-- ============================================================================
-- HELPER FUNCTION: Update timestamp on modification
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to simulation_groups
DROP TRIGGER IF EXISTS update_simulation_groups_updated_at ON simulation_groups;
CREATE TRIGGER update_simulation_groups_updated_at
    BEFORE UPDATE ON simulation_groups
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Apply trigger to group_members
DROP TRIGGER IF EXISTS update_group_members_updated_at ON group_members;
CREATE TRIGGER update_group_members_updated_at
    BEFORE UPDATE ON group_members
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================
COMMENT ON TABLE simulation_groups IS 'Stores family/group Umrah planning sessions with shared simulation data';
COMMENT ON TABLE group_members IS 'Tracks members of simulation groups and their savings contributions';
COMMENT ON COLUMN simulation_groups.group_code IS 'Shareable code format: UMR + 5 alphanumeric chars';
COMMENT ON COLUMN simulation_groups.simulation_params IS 'JSON snapshot of simulation input parameters';
COMMENT ON COLUMN simulation_groups.simulation_breakdown IS 'JSON snapshot of cost breakdown';
COMMENT ON COLUMN group_members.contribution_amount IS 'Self-reported savings amount in IDR';
