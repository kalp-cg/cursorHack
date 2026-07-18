-- VedyaAI PostgreSQL Schema
-- Run once on a fresh database (included in docker-entrypoint-initdb.d)

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================
-- CORE ONTOLOGY
-- ============================================================

CREATE TABLE IF NOT EXISTS concepts (
    concept_id      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type            TEXT NOT NULL CHECK (type IN ('roga','lakshana','dravya','yoga','kalpana','karma','property')),
    canonical_name  TEXT NOT NULL UNIQUE,
    status          TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','deprecated','candidate')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Surface-form terms → concept mapping (synonym/alias table)
CREATE TABLE IF NOT EXISTS terms (
    term_id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    surface_form    TEXT NOT NULL,
    language        TEXT NOT NULL DEFAULT 'en',   -- 'en','sa','hi','transliterated'
    concept_id      UUID NOT NULL REFERENCES concepts(concept_id) ON DELETE CASCADE,
    source          TEXT,                          -- 'synonyms.yaml','herbs_amidha','manual'
    UNIQUE(surface_form, language)
);
CREATE INDEX IF NOT EXISTS idx_terms_surface ON terms (lower(surface_form));
CREATE INDEX IF NOT EXISTS idx_terms_concept  ON terms (concept_id);

-- ============================================================
-- DRAVYA — Single herbs / minerals / animal products
-- ============================================================

CREATE TABLE IF NOT EXISTS dravyas (
    dravya_id       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    concept_id      UUID NOT NULL REFERENCES concepts(concept_id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    botanical_name  TEXT,
    family          TEXT,
    english_name    TEXT,
    part_used       TEXT[],
    image_url       TEXT,
    external_link   TEXT,
    preview_text    TEXT,
    source          TEXT NOT NULL DEFAULT 'herbs_amidha',
    corpus_version  TEXT NOT NULL DEFAULT '1.0.0'
);
CREATE INDEX IF NOT EXISTS idx_dravyas_concept ON dravyas(concept_id);
CREATE INDEX IF NOT EXISTS idx_dravyas_name    ON dravyas(lower(name));

CREATE TABLE IF NOT EXISTS property_sets (
    dravya_id       UUID PRIMARY KEY REFERENCES dravyas(dravya_id) ON DELETE CASCADE,
    rasa            TEXT[],    -- Taste(s): Madhura, Amla, Lavana, Katu, Tikta, Kashaya
    guna            TEXT[],    -- Quality(ies): Laghu, Guru, Ruksha, Snigdha, etc.
    virya           TEXT,      -- Potency: Ushna or Sheeta
    vipaka          TEXT,      -- Post-digestive taste: Madhura, Amla, Katu
    prabhav         TEXT[],    -- Special action(s)
    pacify          TEXT[],    -- Doshas pacified: Vata, Pitta, Kapha
    aggravate       TEXT[],    -- Doshas aggravated
    tridosha        BOOLEAN DEFAULT FALSE
);

-- ============================================================
-- KALPANA — Pharmaceutical form / medium class
-- ============================================================

CREATE TABLE IF NOT EXISTS kalpanas (
    kalpana_id      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT NOT NULL UNIQUE,   -- e.g. 'Kwatha/Kashayam'
    medium_class    TEXT NOT NULL,          -- 'aqueous','fermented','lipid','powder','tablet','leha','mineral'
    description     TEXT
);

-- Seed kalpana medium classes on schema creation
INSERT INTO kalpanas (name, medium_class, description) VALUES
  ('Kwatha/Kashayam',    'aqueous',    'Aqueous decoction'),
  ('Asava/Arishta',      'fermented',  'Fermented preparation (contains natural alcohol)'),
  ('Ghrita',             'lipid',      'Medicated ghee / clarified butter'),
  ('Taila',              'lipid',      'Medicated oil'),
  ('Churna',             'powder',     'Fine powder'),
  ('Vati/Gutika',        'tablet',     'Tablet or pill'),
  ('Avaleha/Leha',       'leha',       'Jam-like / electuary preparation'),
  ('Bhasma/Pishti',      'mineral',    'Calcined mineral / gem powder')
ON CONFLICT (name) DO NOTHING;

-- ============================================================
-- YOGA — Compound formulations
-- ============================================================

CREATE TABLE IF NOT EXISTS yogas (
    yoga_id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT NOT NULL,
    kalpana_id      UUID REFERENCES kalpanas(kalpana_id),
    category        TEXT,                  -- Original category from source
    dosage          TEXT,
    anupana         TEXT,                  -- Vehicle / adjuvant
    source          TEXT NOT NULL DEFAULT 'formulations_bhaishajya',
    reference_text  TEXT,                  -- Raw reference string (e.g. 'Ashtanga Hrudayam...')
    corpus_version  TEXT NOT NULL DEFAULT '1.0.0',
    external_only   BOOLEAN DEFAULT FALSE, -- TRUE for Taila/Ghrita wound applications
    differentiation_note TEXT,
    ambiguity_notes JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(name, kalpana_id)
);
CREATE INDEX IF NOT EXISTS idx_yogas_name ON yogas(lower(name));
CREATE INDEX IF NOT EXISTS idx_yogas_kalpana ON yogas(kalpana_id);

-- Yoga ↔ Indication (primary/secondary with source ref)
CREATE TABLE IF NOT EXISTS yoga_indications (
    yoga_id         UUID NOT NULL REFERENCES yogas(yoga_id) ON DELETE CASCADE,
    concept_id      UUID NOT NULL REFERENCES concepts(concept_id) ON DELETE CASCADE,
    weight          TEXT NOT NULL DEFAULT 'primary' CHECK (weight IN ('primary','secondary')),
    source_ref_id   UUID,                  -- References reference table (nullable FK added later)
    PRIMARY KEY (yoga_id, concept_id, weight)
);
CREATE INDEX IF NOT EXISTS idx_yoga_ind_concept ON yoga_indications(concept_id);
CREATE INDEX IF NOT EXISTS idx_yoga_ind_yoga    ON yoga_indications(yoga_id);

-- Yoga ↔ Ingredient (dravya), with optional sense override
CREATE TABLE IF NOT EXISTS yoga_ingredients (
    yoga_id         UUID NOT NULL REFERENCES yogas(yoga_id) ON DELETE CASCADE,
    dravya_id       UUID REFERENCES dravyas(dravya_id) ON DELETE SET NULL,
    ingredient_name TEXT NOT NULL,         -- Raw string from source (always present)
    quantity_note   TEXT,
    sense_override  TEXT,                  -- e.g. 'Vetiveria zizanioides' for Abhaya in Jatyadi
    PRIMARY KEY (yoga_id, ingredient_name)
);
CREATE INDEX IF NOT EXISTS idx_yoga_ing_dravya ON yoga_ingredients(dravya_id);

-- ============================================================
-- REFERENCES — Classical citation metadata
-- ============================================================

CREATE TABLE IF NOT EXISTS "references" (
    ref_id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    work            TEXT NOT NULL,         -- e.g. 'Charaka Samhita'
    sthana          TEXT,                  -- e.g. 'Cikitsasthana'
    chapter         TEXT,
    verse_id        TEXT,
    excerpt_text    TEXT,                  -- Short excerpt / verse translation
    source_file     TEXT,                  -- Original JSON file path
    corpus_version  TEXT NOT NULL DEFAULT '1.0.0',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_refs_work    ON "references"(work);
CREATE INDEX IF NOT EXISTS idx_refs_sthana  ON "references"(sthana);

-- Full-text search for RAG (Ask the Texts)
ALTER TABLE "references" ADD COLUMN IF NOT EXISTS fts tsvector
    GENERATED ALWAYS AS (to_tsvector('english', coalesce(excerpt_text, ''))) STORED;
CREATE INDEX IF NOT EXISTS idx_refs_fts ON "references" USING GIN (fts);

-- Prevent duplicate Charaka verse loads
CREATE UNIQUE INDEX IF NOT EXISTS uq_refs_charaka_verse
  ON "references" (sthana, chapter, verse_id)
  WHERE work = 'Charaka Samhita';

-- Yoga ↔ Reference (many-to-many)
CREATE TABLE IF NOT EXISTS yoga_references (
    yoga_id         UUID NOT NULL REFERENCES yogas(yoga_id) ON DELETE CASCADE,
    ref_id          UUID NOT NULL REFERENCES "references"(ref_id) ON DELETE CASCADE,
    PRIMARY KEY (yoga_id, ref_id)
);

-- Add FK from yoga_indications to references (after references table exists)
ALTER TABLE yoga_indications
    ADD CONSTRAINT fk_yoga_ind_ref
    FOREIGN KEY (source_ref_id) REFERENCES "references"(ref_id) ON DELETE SET NULL
    DEFERRABLE INITIALLY DEFERRED;

-- ============================================================
-- VECTOR EMBEDDINGS (pgvector)
-- ============================================================

CREATE TABLE IF NOT EXISTS verse_embeddings (
    ref_id          UUID PRIMARY KEY REFERENCES "references"(ref_id) ON DELETE CASCADE,
    embedding       vector(1536),          -- OpenAI text-embedding-3-small dimension
    model_name      TEXT NOT NULL DEFAULT 'text-embedding-3-small',
    corpus_version  TEXT NOT NULL DEFAULT '1.0.0',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_verse_emb_vector
    ON verse_embeddings USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- ============================================================
-- SAFETY — Constraint Rules
-- ============================================================

CREATE TABLE IF NOT EXISTS constraint_rules (
    rule_id             TEXT PRIMARY KEY,
    condition_concept   TEXT NOT NULL,     -- Canonical comorbidity name, e.g. 'Prameha'
    condition_aliases   TEXT[],            -- Synonyms for the condition
    target_type         TEXT NOT NULL,     -- 'kalpana_class','ingredient_keyword','ingredient_name','category_flag'
    target_value        JSONB NOT NULL,    -- String or array of strings
    severity            TEXT NOT NULL CHECK (severity IN ('HARD_EXCLUDE','WARN')),
    message             TEXT NOT NULL,
    classical_basis     TEXT,
    applies_to_yoga_names TEXT[],          -- If set, only applies to these specific yogas
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- SENSE RULES — Homonym disambiguation
-- ============================================================

CREATE TABLE IF NOT EXISTS sense_rules (
    rule_id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    term                TEXT NOT NULL,             -- e.g. 'Abhaya'
    default_dravya_name TEXT,                      -- e.g. 'Terminalia chebula'
    context_yoga_id     UUID REFERENCES yogas(yoga_id) ON DELETE SET NULL,
    context_yoga_name   TEXT,                      -- denormalised for readability
    context_dravya_name TEXT,                      -- e.g. 'Vetiveria zizanioides'
    explanation         TEXT NOT NULL,
    source              TEXT
);
CREATE INDEX IF NOT EXISTS idx_sense_term ON sense_rules(lower(term));

-- ============================================================
-- AUDIT / TRACE
-- ============================================================

CREATE TABLE IF NOT EXISTS recommendation_traces (
    trace_id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vignette_hash   TEXT,                  -- SHA256 of vignette JSON (anonymous)
    corpus_version  TEXT NOT NULL,
    llm_used        BOOLEAN NOT NULL DEFAULT FALSE,
    top_yoga_id     UUID REFERENCES yogas(yoga_id) ON DELETE SET NULL,
    feature_vector  JSONB,                 -- Scores for top yoga
    safety_hits     JSONB,                 -- Rule IDs fired
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- HELPFUL VIEWS
-- ============================================================

CREATE OR REPLACE VIEW yoga_detail AS
SELECT
    y.yoga_id,
    y.name AS yoga_name,
    k.name AS kalpana_name,
    k.medium_class,
    y.category,
    y.dosage,
    y.anupana,
    y.reference_text,
    y.differentiation_note,
    y.ambiguity_notes,
    y.external_only,
    ARRAY_AGG(DISTINCT CASE WHEN yi.weight = 'primary' THEN c.canonical_name END) FILTER (WHERE yi.weight = 'primary') AS primary_indications,
    ARRAY_AGG(DISTINCT CASE WHEN yi.weight = 'secondary' THEN c.canonical_name END) FILTER (WHERE yi.weight = 'secondary') AS secondary_indications,
    ARRAY_AGG(DISTINCT ing.ingredient_name) AS ingredients
FROM yogas y
LEFT JOIN kalpanas k ON y.kalpana_id = k.kalpana_id
LEFT JOIN yoga_indications yi ON y.yoga_id = yi.yoga_id
LEFT JOIN concepts c ON yi.concept_id = c.concept_id
LEFT JOIN yoga_ingredients ing ON y.yoga_id = ing.yoga_id
GROUP BY y.yoga_id, k.name, k.medium_class;
