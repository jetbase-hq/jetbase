from dataclasses import dataclass


@dataclass
class MigrationRecord:
    version: str
    order_executed: int
    description: str
