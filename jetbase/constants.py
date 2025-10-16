from typing import Final

BASE_DIR: Final[str] = "jetbase"
MIGRATIONS_DIR: Final[str] = "migrations"
CONFIG_FILE: Final[str] = "config.py"

CONFIG_FILE_CONTENT: Final[str] = """
# Jetbase Configuration
# Update the sqlalchemy_url with your database connection string.

sqlalchemy_url = "postgresql://user:password@localhost:5432/mydb"
"""
