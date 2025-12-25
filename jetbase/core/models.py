import datetime as dt
from dataclasses import dataclass


@dataclass
class MigrationRecord:
    version: str
    order_executed: int
    description: str
    filename: str
    applied_at: dt.datetime
    migration_type: str


@dataclass
class LockStatus:
    is_locked: bool
    locked_at: dt.datetime | None
