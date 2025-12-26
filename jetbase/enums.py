from enum import Enum


class MigrationDirectionType(Enum):
    UPGRADE = "upgrade"
    ROLLBACK = "rollback"


class MigrationType(Enum):
    VERSIONED = "VERSIONED"
    RUNS_ON_CHANGE = "RUNS_ON_CHANGE"
    RUNS_ALWAYS = "RUNS_ALWAYS"


class DatabaseType(Enum):
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"
