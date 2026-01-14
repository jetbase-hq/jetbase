from typing import Final

BASE_DIR: Final[str] = "jetbase"
MIGRATIONS_DIR: Final[str] = "migrations"
ENV_FILE: Final[str] = "env.py"
RUNS_ALWAYS_FILE_PREFIX: Final[str] = "RA__"
RUNS_ON_CHANGE_FILE_PREFIX: Final[str] = "ROC__"
VERSION_FILE_PREFIX: Final[str] = "V"
DEFAULT_DELIMITER: Final[str] = ";"


ENV_FILE_CONTENT: Final[str] = """# Jetbase Configuration
# Update the sqlalchemy_url with your database connection string.

sqlalchemy_url = "postgresql://user:password@localhost:5432/mydb"
"""

NEW_MIGRATION_FILE_CONTENT: Final[str] = """-- upgrade

-- rollback
"""
