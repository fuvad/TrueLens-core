-- ================================
-- NewsScope / TrueLens DB Schema
-- Author: DB Engineer 
-- ================================

-- ================================
-- SOURCES TABLE
-- ================================

CREATE TABLE IF NOT EXISTS sources (
  id SERIAL PRIMARY KEY,
  domain TEXT UNIQUE NOT NULL,
  name TEXT,
  reliability_tag TEXT CHECK (reliability_tag IN ('trusted','unverified','bad')) DEFAULT 'unverified',
  last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ================================
-- ARTICLES TABLE
-- ================================
CREATE TABLE IF NOT EXISTS articles (
  id BIGSERIAL PRIMARY KEY,
  title TEXT,
  url TEXT UNIQUE NOT NULL,
  source_domain TEXT NOT NULL REFERENCES sources(domain) ON UPDATE CASCADE,
  summary TEXT,
  content TEXT,
  published_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  is_verified BOOLEAN
);

-- ================================
-- SUMMARIES TABLE (GPT Output)
-- ================================
CREATE TABLE IF NOT EXISTS summaries (
  id BIGSERIAL PRIMARY KEY,
  article_id BIGINT REFERENCES articles(id) ON DELETE CASCADE,
  neutral_summary TEXT,
  trust_index INT CHECK (trust_index BETWEEN 0 AND 100),
  reasoning TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ================================
-- ANALYSIS TABLE (Bias Detection)
-- ================================
CREATE TABLE IF NOT EXISTS analysis (
  id BIGSERIAL PRIMARY KEY,
  article_id BIGINT REFERENCES articles(id) ON DELETE CASCADE,
  bias_label TEXT,
  bias_score DOUBLE PRECISION,
  final_score DOUBLE PRECISION,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);


-- ================================
-- INDEXES FOR PERFORMANCE
-- ================================
CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source_domain);
CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_at);