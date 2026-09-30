-- Initialize spatial and utility extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- Note: vector extension enabled if pgvector is installed in image
DO $$
BEGIN
    CREATE EXTENSION IF NOT EXISTS "vector";
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'pgvector extension not pre-bundled in image, using fallback array representation';
END
$$;
