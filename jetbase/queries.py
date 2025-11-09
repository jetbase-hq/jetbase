from sqlalchemy import TextClause, text

LATEST_VERSION_QUERY: TextClause = text("""
    SELECT 
        version 
    FROM 
        jetbase_migrations
    ORDER BY 
        created_at DESC
    LIMIT 1
""")

CREATE_MIGRATIONS_TABLE_STMT: TextClause = text("""
CREATE TABLE IF NOT EXISTS jetbase_migrations (
    version VARCHAR(255) PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

INSERT_VERSION_STMT: TextClause = text("""
INSERT INTO jetbase_migrations (version) 
VALUES (:version)
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
        created_at DESC
    LIMIT :limit
""")

LATEST_VERSIONS_BY_STARTING_VERSION_QUERY: TextClause = text("""
    SELECT
        version
    FROM
        jetbase_migrations
    WHERE created_at > 
        (select created_at from jetbase_migrations 
            where version = :starting_version)
    ORDER BY 
        created_at DESC
""")

CHECK_IF_VERSION_EXISTS_QUERY: TextClause = text("""
    SELECT 
        COUNT(*)
    FROM 
        jetbase_migrations
    WHERE 
        version = :version
""")
