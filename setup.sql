-- Create a new database (if you don't want to use the default 'postgres' one)
CREATE DATABASE personal_assistance;

-- Switch to the new database
\c personal_assistance;

-- 1. Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE if NOT EXISTS notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    content TEXT NOT NULL, 
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    mood TEXT,
    tags TEXT[], 
    topic TEXT NOT NULL, 
    embedding VECTOR(3072) NOT NULL
);

CREATE INDEX idx_created_at ON notes(created_at);
CREATE INDEX idx_tags ON notes USING GIN(tags);

CREATE TABLE if not exists raw_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    note TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);