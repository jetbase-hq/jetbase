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
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    checksum VARCHAR(64)
)
""")

INSERT_VERSION_STMT: TextClause = text("""
INSERT INTO jetbase_migrations (version, description, filename, checksum) 
VALUES (:version, :description, :filename, :checksum)
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

CHECK_IF_LOCK_TABLE_EXISTS_QUERY: TextClause = text("""
SELECT EXISTS (
    SELECT 1
    FROM information_schema.tables
    WHERE table_schema = 'public'
      AND table_name = 'jetbase_lock'
)
""")


MIGRATION_RECORDS_QUERY: TextClause = text("""
    SELECT
        version, 
        order_executed, 
        description  
    FROM
        jetbase_migrations
    ORDER BY
        applied_at ASC
""")


CREATE_LOCK_TABLE_STMT: TextClause = text("""
CREATE TABLE IF NOT EXISTS jetbase_lock (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    is_locked BOOLEAN NOT NULL DEFAULT FALSE,
    locked_at TIMESTAMP,
    process_id VARCHAR(36)
)
""")

INITIALIZE_LOCK_RECORD_STMT: TextClause = text("""
INSERT INTO jetbase_lock (id, is_locked)
SELECT 1, FALSE
WHERE NOT EXISTS (SELECT 1 FROM jetbase_lock WHERE id = 1)
""")


CHECK_LOCK_STATUS_STMT: TextClause = text("""
SELECT is_locked, locked_at
FROM jetbase_lock
WHERE id = 1
""")

ACQUIRE_LOCK_STMT: TextClause = text("""
UPDATE jetbase_lock
SET is_locked = TRUE,
    locked_at = :locked_at,
    process_id = :process_id
WHERE id = 1 AND is_locked = FALSE
""")

RELEASE_LOCK_STMT: TextClause = text("""
UPDATE jetbase_lock
SET is_locked = FALSE,
    locked_at = NULL,
    process_id = NULL
WHERE id = 1 AND process_id = :process_id
""")

FORCE_UNLOCK_STMT: TextClause = text("""
UPDATE jetbase_lock
SET is_locked = FALSE,
    locked_at = NULL,
    process_id = NULL
WHERE id = 1
""")


GET_VERSION_CHECKSUMS_QUERY: TextClause = text("""
    SELECT 
        version, checksum
    FROM 
        jetbase_migrations
    ORDER BY 
        order_executed ASC
""")


REPAIR_MIGRATION_CHECKSUM_STMT: TextClause = text("""
UPDATE jetbase_migrations
SET checksum = :checksum
WHERE version = :version
""")
