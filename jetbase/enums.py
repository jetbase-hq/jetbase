from enum import Enum


class MigrationDirectionType(Enum):
    "Enum representing the direction of a migration operation."

    UPGRADE = "upgrade"
    ROLLBACK = "rollback"


class MigrationType(Enum):
    "Enum representing the type of migration."

    VERSIONED = "VERSIONED"
    RUNS_ON_CHANGE = "RUNS_ON_CHANGE"
    RUNS_ALWAYS = "RUNS_ALWAYS"


class DatabaseType(Enum):
    "Enum representing supported database types."

    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"
    SNOWFLAKE = "snowflake"
    MYSQL = "mysql"
    DATABRICKS = "databricks"
