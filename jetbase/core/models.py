from dataclasses import dataclass


@dataclass
class MigrationRecord:
    version: str
    order_executed: int
    description: str


# @dataclass
# class MigrationFilepath:
#     version: str
#     filepath: str


# @dataclass
# class RepeatableOnChangeMigration:
#     filename: str
#     checksum: str
