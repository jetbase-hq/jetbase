import os

from jetbase.core.checksum import calculate_checksum
from jetbase.core.file_parser import parse_upgrade_statements
from jetbase.core.lock import migration_lock
from jetbase.core.repository import (
    get_checksums_by_version,
    update_migration_checksums,
)
from jetbase.core.upgrade import run_upgrade_validations
from jetbase.core.version import get_migration_filepaths_by_version
from jetbase.exceptions import (
    MigrationVersionMismatchError,
)


def repair_checksums_cmd() -> None:
    migrated_versions_and_checksums: list[tuple[str, str]] = get_checksums_by_version()
    if not migrated_versions_and_checksums:
        print("No migrations have been applied; nothing to repair.")
        return

    latest_migrated_version: str = migrated_versions_and_checksums[-1][0]

    run_upgrade_validations(
        latest_migrated_version=latest_migrated_version,
        skip_checksum_validation=True,
    )

    versions_and_checksums_to_repair: list[tuple[str, str]] = []

    migration_filepaths_by_version: dict[str, str] = get_migration_filepaths_by_version(
        directory=os.path.join(os.getcwd(), "migrations"),
        end_version=latest_migrated_version,
    )

    for index, (file_version, filepath) in enumerate(
        migration_filepaths_by_version.items()
    ):
        sql_statements: list[str] = parse_upgrade_statements(file_path=filepath)
        checksum: str = calculate_checksum(sql_statements=sql_statements)

        # this should never be hit because of the validation check above
        if file_version != migrated_versions_and_checksums[index][0]:
            raise MigrationVersionMismatchError(
                f"Version mismatch: expected {migrated_versions_and_checksums[index][0]}, found {file_version}."
            )

        if checksum != migrated_versions_and_checksums[index][1]:
            versions_and_checksums_to_repair.append(
                (
                    file_version,
                    checksum,
                )
            )

    if not versions_and_checksums_to_repair:
        print("All migration checksums are already valid; nothing to repair.")
        return

    with migration_lock():
        update_migration_checksums(
            versions_and_checksums=versions_and_checksums_to_repair
        )
        for version, _ in versions_and_checksums_to_repair:
            print(f"Repaired checksum for version: {version}")
            print("Successfully repaired checksums")
