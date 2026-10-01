import os
import tempfile

from jetbase.constants import MIGRATIONS_DIR
from jetbase.engine.file_parser import parse_rollback_statements
from jetbase.engine.git import get_repo_root, read_file_at_commit
from jetbase.engine.lock import migration_lock
from jetbase.engine.version import get_migration_filepaths_by_version
from jetbase.enums import MigrationDirectionType
from jetbase.logging import logger
from jetbase.models import AppliedVersionedMigration
from jetbase.repositories.migrations_repo import (
    get_versioned_migrations_desc,
    run_migration,
)


def attempt_safe_rollback() -> bool:
    """
    Roll the database back to the latest applied migration whose file exists.

    Triggered when an upgrade finds that an already-applied migration's file
    is missing locally. Rolls back the trailing applied migrations whose files
    are absent, down to the most recent applied version that still has a file
    (the new baseline). The rollback SQL for missing files is recovered
    read-only from the git commit hash recorded on the latest applied
    migration (it contained every earlier migration's file).

    Falls back gracefully (returns False) when recovery is not possible, so
    the caller can re-raise the original error and preserve old behaviour:
    no applied migrations, not inside a git repository, the latest applied
    migration has no recorded git commit hash, the missing files are not a
    contiguous trailing run, or a file cannot be recovered from git.

    Returns:
        bool: True if the database was rolled back to a usable baseline,
            False if no safe rollback could be performed.
    """
    applied: list[AppliedVersionedMigration] = get_versioned_migrations_desc()
    if not applied:
        return False

    repo_root: str | None = get_repo_root()
    latest_hash: str | None = applied[0].git_commit_hash
    if repo_root is None or not latest_hash:
        return False

    migrations_dir: str = os.path.join(os.getcwd(), MIGRATIONS_DIR)
    current_files: dict[str, str] = get_migration_filepaths_by_version(
        directory=migrations_dir
    )

    to_rollback: list[AppliedVersionedMigration] = []
    for migration in applied:
        if migration.version in current_files:
            break
        to_rollback.append(migration)

    if not to_rollback:
        return False

    logger.info(
        "Detected missing migration file(s). Attempting safe rollback of: %s",
        ", ".join(migration.version for migration in to_rollback),
    )

    with migration_lock():
        for migration in to_rollback:
            sql_statements: list[str] | None = _get_rollback_statements(
                migration=migration,
                current_files=current_files,
                migrations_dir=migrations_dir,
                repo_root=repo_root,
                commit_hash=latest_hash,
            )
            if sql_statements is None:
                logger.warning(
                    "Could not recover rollback SQL for version %s from git. "
                    "Aborting safe rollback.",
                    migration.version,
                )
                return False

            run_migration(
                sql_statements=sql_statements,
                version=migration.version,
                migration_operation=MigrationDirectionType.ROLLBACK,
                filename=migration.filename,
            )
            logger.info("Rollback applied successfully: %s", migration.filename)

    return True


def _get_rollback_statements(
    migration: AppliedVersionedMigration,
    current_files: dict[str, str],
    migrations_dir: str,
    repo_root: str,
    commit_hash: str,
) -> list[str] | None:
    """
    Get rollback SQL statements for a migration being safely rolled back.

    Uses the local file when it still exists; otherwise recovers the file
    content read-only from the given git commit and parses it.

    Args:
        migration (AppliedVersionedMigration): The migration to roll back.
        current_files (dict[str, str]): Mapping of version to file path for
            files that currently exist locally.
        migrations_dir (str): Absolute path to the migrations directory.
        repo_root (str): Absolute path to the git repository root.
        commit_hash (str): The commit hash to recover missing files from.

    Returns:
        list[str] | None: The rollback SQL statements, or None if the file
            could not be recovered from git.
    """
    local_path: str | None = current_files.get(migration.version)
    if local_path is not None:
        return parse_rollback_statements(file_path=local_path)

    file_path: str = os.path.join(migrations_dir, migration.filename)
    repo_relative_path: str = os.path.relpath(file_path, repo_root).replace(os.sep, "/")
    content: str | None = read_file_at_commit(
        commit_hash=commit_hash, repo_relative_path=repo_relative_path
    )
    if content is None:
        return None

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".sql", delete=False
    ) as temp_file:
        temp_file.write(content)
        temp_file_path: str = temp_file.name

    try:
        return parse_rollback_statements(file_path=temp_file_path)
    finally:
        os.unlink(temp_file_path)
