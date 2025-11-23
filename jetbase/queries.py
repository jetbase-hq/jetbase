from sqlalchemy import TextClause, text

LATEST_VERSION_QUERY: TextClause = text("""
    SELECT 
        version 
    FROM 
        jetbase_migrations
    ORDER BY 
        applied_at DESC
    LIMIT 1
""")

CREATE_MIGRATIONS_TABLE_STMT: TextClause = text("""
CREATE TABLE IF NOT EXISTS jetbase_migrations (
    version VARCHAR(255) PRIMARY KEY,
    description VARCHAR(500),
    filename VARCHAR(512),
    order_executed INT GENERATED ALWAYS AS IDENTITY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

INSERT_VERSION_STMT: TextClause = text("""
INSERT INTO jetbase_migrations (version, description, filename) 
VALUES (:version, :description, :filename)
""")

DELETE_VERSION_STMT: TextClause = text("""
DELETE FROM jetbase_migrations 
WHERE version = :version
""")

LATEST_VERSIONS_QUERY: TextClause = text("""
    SELECT 
        version 
    FROM 
        jetbase_migrations
    ORDER BY 
        applied_at DESC
    LIMIT :limit
""")

LATEST_VERSIONS_BY_STARTING_VERSION_QUERY: TextClause = text("""
    SELECT
        version
    FROM
        jetbase_migrations
    WHERE applied_at > 
        (select applied_at from jetbase_migrations 
            where version = :starting_version)
    ORDER BY 
        applied_at DESC
""")

CHECK_IF_VERSION_EXISTS_QUERY: TextClause = text("""
    SELECT 
        COUNT(*)
    FROM 
        jetbase_migrations
    WHERE 
        version = :version
""")


CHECK_IF_MIGRATIONS_TABLE_EXISTS_QUERY: TextClause = text("""
SELECT EXISTS (
    SELECT 1
    FROM information_schema.tables
    WHERE table_schema = 'public'
      AND table_name = 'jetbase_migrations'
)
""")
