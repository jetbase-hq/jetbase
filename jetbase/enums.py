from enum import Enum


class MigrationDirectionType(Enum):
    UPGRADE = "upgrade"
    ROLLBACK = "rollback"


class MigrationType(Enum):
    VERSIONED = "VERSIONED"
    REPEATABLE_ON_CHANGE = "REPEATABLE_ON_CHANGE"
    REPEATABLE_ALWAYS = "REPEATABLE_ALWAYS"
