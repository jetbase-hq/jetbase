import datetime as dt
from dataclasses import dataclass


@dataclass
class MigrationRecord:
    order_executed: int
    version: str
    description: str
    filename: str
    migration_type: str
    applied_at: dt.datetime
    checksum: str


@dataclass
class LockStatus:
    is_locked: bool
    locked_at: dt.datetime | None
