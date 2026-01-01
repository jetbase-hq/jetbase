import hashlib


def calculate_checksum(sql_statements: list[str]) -> str:
    """
    Calculate SHA256 checksum for a list of SQL statements.

    Joins all statements with newlines and computes a SHA256 hash to create
    a unique fingerprint of the migration content.

    Args:
        sql_statements (list[str]): List of SQL statements to hash.

    Returns:
        str: 64-character hexadecimal SHA256 checksum string.

    Example:
        >>> calculate_checksum(["SELECT 1", "SELECT 2"])
        'a1b2c3d4e5f6...'
    """
    formatted_sql_statements: str = "\n".join(sql_statements)

    checksum: str = hashlib.sha256(formatted_sql_statements.encode("utf-8")).hexdigest()

    return checksum
