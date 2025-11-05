from enum import Enum


class MigrationOperationType(Enum):
    UPGRADE = "upgrade"
    ROLLBACK = "rollback"
