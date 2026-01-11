class DuplicateMigrationVersionError(Exception):
    """
    Raised when multiple migration files share the same version number.

    This typically occurs when two files have the same version prefix
    (e.g., V1.0 and V1_0) which normalize to the same version.
    """

    pass


class InvalidMigrationFilenameError(Exception):
    """
    Raised when a migration filename doesn't match the required format.

    Valid formats are:
    - V{version}__{description}.sql for versioned migrations
    - RA__{description}.sql for runs-always migrations
    - ROC__{description}.sql for runs-on-change migrations
    """

    pass


class MigrationFilenameTooLongError(Exception):
    """
    Raised when a migration filename exceeds the maximum length of 512 characters.

    Long filenames can cause issues with some filesystems and databases.
    """

    pass


class OutOfOrderMigrationError(Exception):
    """
    Raised when a new migration file has a version lower than the latest applied.

    New migrations must have version numbers higher than all previously
    applied migrations to maintain a consistent migration order.
    """

    pass


class ChecksumMismatchError(Exception):
    """
    Raised when a migration file's current checksum differs from the stored checksum.

    This indicates that the migration file was modified after being applied
    to the database, which can cause inconsistencies between environments.
    """

    pass


class MigrationVersionMismatchError(Exception):
    """
    Raised when migration file versions don't match the expected sequence.

    This occurs during checksum repair when the order of migration files
    doesn't match the order of applied migrations.
    """

    pass


class VersionNotFoundError(Exception):
    """
    Raised when a specified version doesn't exist or hasn't been applied.

    This can occur when attempting to rollback to a version that is not
    in the migration history.
    """

    pass


class DirectoryNotFoundError(Exception):
    """
    Raised when the required Jetbase directories do not exist.

    This occurs when commands are run outside of a Jetbase project
    or when the migrations directory is missing.
    """

    pass


class InvalidVersionError(Exception):
    """
    Raised when a version is not valid.
    """

    pass
