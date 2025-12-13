-- ================================
-- NewsScope / TrueLens DB Schema
-- Author: DB Engineer (Member 3)
-- ================================

-- Drop existing tables (for reset during development)
DROP TABLE IF EXISTS analysis CASCADE;
DROP TABLE IF EXISTS summaries CASCADE;
DROP TABLE IF EXISTS articles CASCADE;

-- ================================
-- ARTICLES TABLE
-- ================================
CREATE TABLE articles (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    source_domain TEXT NOT NULL,
    published_at TIMESTAMP NOT NULL,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================
-- SUMMARIES TABLE (GPT Output)
-- ================================
CREATE TABLE summaries (
    id SERIAL PRIMARY KEY,
    article_id INTEGER UNIQUE REFERENCES articles(id) ON DELETE CASCADE,
    neutral_summary TEXT NOT NULL,
    trust_index INTEGER CHECK (trust_index BETWEEN 0 AND 100),
    reasoning TEXT
);

-- ================================
-- ANALYSIS TABLE (Bias Detection)
-- ================================
CREATE TABLE analysis (
    id SERIAL PRIMARY KEY,
    article_id INTEGER UNIQUE REFERENCES articles(id) ON DELETE CASCADE,
    bias_label VARCHAR(20),
    bias_score REAL,
    final_score REAL
);

-- ================================
-- INDEXES FOR PERFORMANCE
-- ================================
CREATE INDEX idx_articles_published_at ON articles(published_at DESC);
CREATE INDEX idx_analysis_final_score ON analysis(final_score DESC);
