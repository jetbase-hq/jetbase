class DuplicateMigrationVersionError(Exception):
    """Raised when multiple migration files share the same version."""

    pass


class InvalidMigrationFilenameError(Exception):
    """Raised when migration filename doesn't match required format."""

    pass


class MigrationFilenameTooLongError(Exception):
    """Raised when migration filename exceeds maximum length."""

    pass


class OutOfOrderMigrationError(Exception):
    """Raised when a new migration file has a version lower than the latest migrated version."""

    pass


class MigrationChecksumMismatchError(Exception):
    """Raised when a migration file's checksum doesn't match the stored checksum."""

    pass


class MigrationVersionMismatchError(Exception):
    """Raised when migration file versions don't match expected sequence."""

    pass


class VersionNotFoundError(Exception):
    """Raised when attempting to rollback to a version that doesn't exist or hasn't been applied."""

    pass
