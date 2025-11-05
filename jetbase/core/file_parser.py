from jetbase.enums import MigrationOperationType


def parse_upgrade_statements(file_path: str) -> list[str]:
    statements = []
    current_statement = []

    with open(file_path, "r") as file:
        for line in file:
            line = line.strip()

            if (
                line.startswith("--")
                and line[2:].strip().lower() == MigrationOperationType.ROLLBACK.value
            ):
                break

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


def parse_rollback_statements(file_path: str) -> list[str]:
    statements = []
    current_statement = []
    in_rollback_section = False

    with open(file_path, "r") as file:
        for line in file:
            line = line.strip()

            if not in_rollback_section:
                if (
                    line.startswith("--")
                    and line[2:].strip().lower()
                    == MigrationOperationType.ROLLBACK.value
                ):
                    in_rollback_section = True
                else:
                    continue

            if in_rollback_section:
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
