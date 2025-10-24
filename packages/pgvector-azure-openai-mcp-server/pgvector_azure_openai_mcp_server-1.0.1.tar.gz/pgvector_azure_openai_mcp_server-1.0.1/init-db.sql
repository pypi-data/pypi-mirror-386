-- Initialize PostgreSQL database for pgvector MCP Server
-- This script runs when the Docker container is first created

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify extension installation
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';

-- Display success message
DO $$
BEGIN
    RAISE NOTICE '✅ pgvector database initialized successfully!';
    RAISE NOTICE '📊 Vector extension version: %', (SELECT extversion FROM pg_extension WHERE extname = 'vector');
    RAISE NOTICE '🚀 Ready to accept MCP server connections';
END $$;