import hashlib


def calculate_checksum(sql_statements: list[str]) -> str:
    """
    Calculate a checksum for a list of SQL statements.

    Args:
        sql_statements (list[str]): The list of SQL statements to calculate the checksum for

    Returns:
        str: The hexadecimal checksum string

    Example:
        >>> calculate_checksum(["SELECT * FROM users", "INSERT INTO logs VALUES (1)"])
        'a1b2c3d4e5f6...'
    """
    formatted_sql_statements: str = "\n".join(sql_statements)

    checksum: str = hashlib.sha256(formatted_sql_statements.encode("utf-8")).hexdigest()

    return checksum
