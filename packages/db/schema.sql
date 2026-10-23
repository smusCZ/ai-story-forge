-- AI Story Forge – Core Schema (Phase 1: Series + Character Anchors)
-- PostgreSQL + pgvector ready

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ============================================================
-- SERIES (izolace postav a příběhů)
-- ============================================================
CREATE TABLE series (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id        UUID,
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_series_owner ON series(owner_id);

-- ============================================================
-- CHARACTER ANCHORS (vázané na sérii – žádné míchání)
-- ============================================================
CREATE TABLE character_anchors (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    series_id           UUID NOT NULL REFERENCES series(id) ON DELETE CASCADE,
    name                VARCHAR(255) NOT NULL,
    role                VARCHAR(100),
    appearance_text     TEXT,
    personality         JSONB NOT NULL DEFAULT '{}',
    backstory           TEXT,
    relationships       JSONB NOT NULL DEFAULT '{}',
    current_state       TEXT,
    consistency_rules   JSONB NOT NULL DEFAULT '{}',
    reference_image_ids UUID[] DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_character_name_per_series UNIQUE (series_id, name)
);

CREATE INDEX idx_character_anchors_series ON character_anchors(series_id);

-- ============================================================
-- STORIES (vázané na sérii + žánrový profil)
-- ============================================================
CREATE TABLE stories (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    series_id       UUID NOT NULL REFERENCES series(id) ON DELETE RESTRICT,
    title           VARCHAR(500) NOT NULL,
    status          VARCHAR(50) NOT NULL DEFAULT 'draft',
    genre           JSONB NOT NULL DEFAULT '{}',
    settings        JSONB NOT NULL DEFAULT '{}',
    engagement_score FLOAT NOT NULL DEFAULT 0.0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_stories_series ON stories(series_id);
CREATE INDEX idx_stories_status ON stories(status);

-- ============================================================
-- CHAPTERS
-- ============================================================
CREATE TABLE chapters (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    story_id            UUID NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
    branch_id           UUID,
    chapter_number      INTEGER NOT NULL,
    title               VARCHAR(500),
    content             TEXT NOT NULL,
    summary             TEXT,
    status              VARCHAR(50) NOT NULL DEFAULT 'draft',
    generated_by        VARCHAR(50) NOT NULL DEFAULT 'user',
    parent_chapter_id   UUID REFERENCES chapters(id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_chapter_number_per_story UNIQUE (story_id, chapter_number, branch_id)
);

CREATE INDEX idx_chapters_story ON chapters(story_id);

-- ============================================================
-- IMAGE FOLDERS + IMAGES
-- ============================================================
CREATE TABLE image_folders (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id    UUID,
    series_id   UUID REFERENCES series(id) ON DELETE SET NULL,
    story_id    UUID REFERENCES stories(id) ON DELETE SET NULL,
    name        VARCHAR(255) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE images (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    folder_id   UUID NOT NULL REFERENCES image_folders(id) ON DELETE CASCADE,
    url         TEXT NOT NULL,
    filename    VARCHAR(500),
    tags        TEXT[] DEFAULT '{}',
    embedding   vector(768),
    uploaded_by UUID,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_images_folder ON images(folder_id);

-- ============================================================
-- FEEDBACK
-- ============================================================
CREATE TABLE feedback (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chapter_id      UUID NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    user_id         UUID,
    type            VARCHAR(50) NOT NULL,
    content         TEXT,
    sentiment_score FLOAT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_feedback_chapter ON feedback(chapter_id);

-- ============================================================
-- AGENT RUNS
-- ============================================================
CREATE TABLE agent_runs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    story_id        UUID NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
    action_taken    VARCHAR(100),
    reasoning       TEXT,
    input_state     JSONB,
    output          JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_agent_runs_story ON agent_runs(story_id);

-- ============================================================
-- UPDATED_AT trigger
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_series_updated_at BEFORE UPDATE ON series
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_character_anchors_updated_at BEFORE UPDATE ON character_anchors
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_stories_updated_at BEFORE UPDATE ON stories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chapters_updated_at BEFORE UPDATE ON chapters
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
