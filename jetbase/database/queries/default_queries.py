from sqlalchemy import TextClause, text

from jetbase.enums import MigrationType

LATEST_VERSION_QUERY: TextClause = text(f"""
    SELECT 
        version 
    FROM 
        jetbase_migrations
    WHERE
        migration_type = '{MigrationType.VERSIONED.value}'
    ORDER BY 
        applied_at DESC
    LIMIT 1
""")

CREATE_MIGRATIONS_TABLE_STMT: TextClause = text("""
CREATE TABLE IF NOT EXISTS jetbase_migrations (
    order_executed INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    version VARCHAR(255),
    description VARCHAR(500) NOT NULL,
    filename VARCHAR(512) NOT NULL,
    migration_type VARCHAR(32) NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    checksum VARCHAR(64) NOT NULL
)
""")

INSERT_VERSION_STMT: TextClause = text("""
INSERT INTO jetbase_migrations (version, description, filename, migration_type, checksum) 
VALUES (:version, :description, :filename, :migration_type, :checksum)
""")

DELETE_VERSION_STMT: TextClause = text(f"""
DELETE FROM jetbase_migrations 
WHERE version = :version
AND migration_type = '{MigrationType.VERSIONED.value}'
""")

LATEST_VERSIONS_QUERY: TextClause = text(f"""
    SELECT 
        version 
    FROM 
        jetbase_migrations
    WHERE
        migration_type = '{MigrationType.VERSIONED.value}'
    ORDER BY 
        applied_at DESC
    LIMIT :limit
""")

LATEST_VERSIONS_BY_STARTING_VERSION_QUERY: TextClause = text(f"""
    SELECT
        version
    FROM
        jetbase_migrations
    WHERE applied_at > 
        (select applied_at from jetbase_migrations 
            where version = :starting_version AND migration_type = '{MigrationType.VERSIONED.value}')
    AND migration_type = '{MigrationType.VERSIONED.value}'
    ORDER BY 
        applied_at DESC
""")

CHECK_IF_VERSION_EXISTS_QUERY: TextClause = text(f"""
    SELECT 
        COUNT(*)
    FROM 
        jetbase_migrations
    WHERE 
        version = :version
    AND
        migration_type = '{MigrationType.VERSIONED.value}'
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
    locked_at = CURRENT_TIMESTAMP,
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


GET_VERSION_CHECKSUMS_QUERY: TextClause = text(f"""
    SELECT 
        version, checksum
    FROM 
        jetbase_migrations
    WHERE
        migration_type = '{MigrationType.VERSIONED.value}'
    ORDER BY 
        order_executed ASC
""")


REPAIR_MIGRATION_CHECKSUM_STMT: TextClause = text(f"""
UPDATE jetbase_migrations
SET checksum = :checksum
WHERE version = :version
AND migration_type = '{MigrationType.VERSIONED.value}'
""")

GET_RUNS_ON_CHANGE_MIGRATIONS_QUERY: TextClause = text(f"""
    SELECT 
        filename, checksum
    FROM 
        jetbase_migrations
    WHERE
        migration_type = '{MigrationType.RUNS_ON_CHANGE.value}'
    ORDER BY 
        filename ASC
        """)


GET_RUNS_ALWAYS_MIGRATIONS_QUERY: TextClause = text(f"""
    SELECT 
        filename
    FROM 
        jetbase_migrations
    WHERE
        migration_type = '{MigrationType.RUNS_ALWAYS.value}'
    ORDER BY 
        filename ASC
        """)

GET_REPEATABLE_MIGRATIONS_QUERY: TextClause = text(f"""
    SELECT 
        filename
    FROM 
        jetbase_migrations
    WHERE
        migration_type in ('{MigrationType.RUNS_ALWAYS.value}', '{MigrationType.RUNS_ON_CHANGE.value}')
    ORDER BY 
        filename ASC
        """)

UPDATE_REPEATABLE_MIGRATION_STMT: TextClause = text("""
UPDATE jetbase_migrations
SET checksum = :checksum,
    applied_at = CURRENT_TIMESTAMP
WHERE filename = :filename
AND migration_type = :migration_type
""")


DELETE_MISSING_VERSION_STMT: TextClause = text(f"""
DELETE FROM jetbase_migrations
WHERE version = :version
AND migration_type = '{MigrationType.VERSIONED.value}'
""")

DELETE_MISSING_REPEATABLE_STMT: TextClause = text(f"""
DELETE FROM jetbase_migrations
WHERE filename = :filename
AND migration_type in ('{MigrationType.RUNS_ALWAYS.value}', '{MigrationType.RUNS_ON_CHANGE.value}')
""")
