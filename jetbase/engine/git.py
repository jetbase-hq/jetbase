import os
import subprocess


def _run_git(*args: str) -> str | None:
    """
    Run a git command in the current working directory.

    Args:
        *args: Arguments to pass to the git executable (excluding 'git').

    Returns:
        str | None: The stripped stdout of the command, or None if git is
            unavailable or the command fails (e.g. not inside a git repo).
    """
    try:
        result: subprocess.CompletedProcess[str] = subprocess.run(
            ["git", *args],
            cwd=os.getcwd(),
            capture_output=True,
            text=True,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None

    return result.stdout.strip()


def get_current_commit_hash() -> str | None:
    """
    Get the git commit hash currently checked out.

    Returns:
        str | None: The full commit hash of HEAD, or None if git is not
            available or the current directory is not inside a git repository.
    """
    return _run_git("rev-parse", "HEAD")


def get_repo_root() -> str | None:
    """
    Get the absolute path to the root of the current git repository.

    Returns:
        str | None: The repository root path, or None if git is not available
            or the current directory is not inside a git repository.
    """
    return _run_git("rev-parse", "--show-toplevel")


def read_file_at_commit(commit_hash: str, repo_relative_path: str) -> str | None:
    """
    Read the contents of a file as it existed at a specific commit.

    Uses ``git show <commit_hash>:<path>`` to retrieve the file content
    without modifying the working tree or HEAD.

    Args:
        commit_hash (str): The commit hash to read the file from.
        repo_relative_path (str): Path to the file relative to the repository
            root, using forward slashes.

    Returns:
        str | None: The file content, or None if the file does not exist at
            that commit or git is unavailable.
    """
    return _run_git("show", f"{commit_hash}:{repo_relative_path}")
