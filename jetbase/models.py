import datetime as dt
from dataclasses import dataclass


@dataclass
class MigrationRecord:
    """
    Represents a single migration record from the jetbase_migrations table.

    Attributes:
        order_executed (int): The sequential order in which this migration
            was executed.
        version (str): The version string for versioned migrations, or
            None for repeatable migrations.
        description (str): Human-readable description extracted from
            the migration filename.
        filename (str): The original filename of the migration file.
        migration_type (str): The type of migration ('VERSIONED',
            'RUNS_ALWAYS', or 'RUNS_ON_CHANGE').
        applied_at (dt.datetime): Timestamp when the migration was applied.
        checksum (str): SHA256 checksum of the migration's SQL statements.
    """

    order_executed: int
    version: str
    description: str
    filename: str
    migration_type: str
    applied_at: dt.datetime
    checksum: str


@dataclass
class LockStatus:
    """
    Represents the current state of the migration lock.

    Attributes:
        is_locked (bool): True if migrations are currently locked.
        locked_at (dt.datetime | None): Timestamp when the lock was acquired,
            or None if not locked.
    """

    is_locked: bool
    locked_at: dt.datetime | None
