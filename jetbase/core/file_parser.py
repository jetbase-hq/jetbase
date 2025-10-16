def parse_sql_file(file_path: str) -> list[str]:
    """
    Parse a SQL file and return a list of SQL statements.

    Args:
        file_path (str): Path to the SQL file

    Returns:
        list[str]: List of SQL statements
    """
    statements = []
    current_statement = []

    with open(file_path, "r") as file:
        for line in file:
            line = line.strip()

            if not line or line.startswith("--"):
                continue
            current_statement.append(line)

            if line.endswith(";"):
                statement = " ".join(current_statement)
                statement = statement.rstrip(";").strip()
                if statement:
                    statements.append(statement)
                current_statement = []

    return statements
