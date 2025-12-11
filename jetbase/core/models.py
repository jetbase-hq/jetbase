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
