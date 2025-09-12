-- Database initialization script for Pokemon Image Recognition App

-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS pokemon_db;

-- Use the database
\c pokemon_db;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Pokemon cache table for faster lookups
CREATE TABLE IF NOT EXISTS pokemon_cache (
    id SERIAL PRIMARY KEY,
    pokemon_id INTEGER UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Image processing logs
CREATE TABLE IF NOT EXISTS recognition_logs (
    id SERIAL PRIMARY KEY,
    image_hash VARCHAR(64) NOT NULL,
    predicted_pokemon_id INTEGER,
    confidence FLOAT,
    processing_time_ms INTEGER,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Model performance metrics
CREATE TABLE IF NOT EXISTS model_metrics (
    id SERIAL PRIMARY KEY,
    model_version VARCHAR(50) NOT NULL,
    accuracy FLOAT,
    avg_processing_time_ms INTEGER,
    total_predictions INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_pokemon_cache_pokemon_id ON pokemon_cache(pokemon_id);
CREATE INDEX IF NOT EXISTS idx_recognition_logs_image_hash ON recognition_logs(image_hash);
CREATE INDEX IF NOT EXISTS idx_recognition_logs_created_at ON recognition_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_model_metrics_model_version ON model_metrics(model_version);