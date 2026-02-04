import os
from pathlib import Path
from typing import Optional

from jetbase.constants import MIGRATIONS_DIR


def find_jetbase_directory(start: Optional[Path] = None) -> Optional[Path]:
    """
    Find the jetbase directory by searching up the directory tree.

    Searches for a directory named 'jetbase' that contains a 'migrations'
    subdirectory. Can start searching from any directory; defaults to current
    working directory.

    Args:
        start (Path | None): Starting directory for the search.
            Defaults to current working directory.

    Returns:
        Path | None: The jetbase directory path if found, otherwise None.
    """
    if start is None:
        start = Path.cwd()

    current = start.resolve()

    while current != current.parent:
        jetbase_candidate = current / "jetbase"
        migrations_dir = jetbase_candidate / MIGRATIONS_DIR

        if jetbase_candidate.is_dir() and migrations_dir.is_dir():
            return jetbase_candidate

        if current.name == "jetbase" and (current / MIGRATIONS_DIR).is_dir():
            return current

        current = current.parent

    return None


def find_jetbase_from_subdir() -> Optional[Path]:
    """
    Check if current directory is a subdirectory of jetbase and return jetbase path.

    For example, if running from project/app/ and jetbase is in project/jetbase/,
    this will find and return project/jetbase/.

    Returns:
        Path | None: The jetbase directory path if found, otherwise None.
    """
    return find_jetbase_directory()


def get_jetbase_migrations_dir() -> Optional[Path]:
    """
    Get the migrations directory from the jetbase folder.

    Searches for the jetbase directory and returns the migrations path.

    Returns:
        Path | None: The migrations directory path if jetbase is found, otherwise None.
    """
    jetbase_dir = find_jetbase_from_subdir()
    if jetbase_dir:
        return jetbase_dir / MIGRATIONS_DIR
    return None


def get_jetbase_env_path() -> Optional[Path]:
    """
    Get the env.py path from the jetbase folder.

    Returns:
        Path | None: The env.py path if jetbase is found, otherwise None.
    """
    jetbase_dir = find_jetbase_from_subdir()
    if jetbase_dir:
        return jetbase_dir / "env.py"
    return None


def is_jetbase_subdir() -> bool:
    """
    Check if the current directory is inside a jetbase project.

    Returns:
        bool: True if inside a jetbase project, False otherwise.
    """
    return find_jetbase_from_subdir() is not None
