from enum import Enum


class MigrationDirectionType(Enum):
    """
    Enum representing the direction of a migration operation.

    Attributes:
        UPGRADE: Apply migrations forward (run upgrade SQL).
        ROLLBACK: Revert migrations backward (run rollback SQL).
    """

    UPGRADE = "upgrade"
    ROLLBACK = "rollback"


class MigrationType(Enum):
    """
    Enum representing the type of migration.

    Attributes:
        VERSIONED: Standard migration with a version number, runs once.
        RUNS_ON_CHANGE: Repeatable migration that runs when its checksum changes.
        RUNS_ALWAYS: Repeatable migration that runs on every upgrade.
    """

    VERSIONED = "VERSIONED"
    RUNS_ON_CHANGE = "RUNS_ON_CHANGE"
    RUNS_ALWAYS = "RUNS_ALWAYS"


class DatabaseType(Enum):
    """
    Enum representing supported database types.

    Attributes:
        POSTGRESQL: PostgreSQL database.
        SQLITE: SQLite database.
        SNOWFLAKE: Snowflake database.
    """

    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"
    SNOWFLAKE = "snowflake"
