from pathlib import Path

from jetbase.constants import BASE_DIR, ENV_FILE, ENV_FILE_CONTENT, MIGRATIONS_DIR


def initialize_cmd() -> None:
    """
    Create the directory structure for a new Jetbase project.

    Creates a 'jetbase' directory containing a 'migrations' subdirectory
    and an 'env.py' configuration file with a template database URL.

    Returns:
        None: Prints a confirmation message with the project location.
    """
    migrations_dir: Path = Path(BASE_DIR) / MIGRATIONS_DIR
    migrations_dir.mkdir(parents=True, exist_ok=True)

    config_path: Path = Path(BASE_DIR) / ENV_FILE
    with open(config_path, "w") as f:
        f.write(ENV_FILE_CONTENT)

    print(
        f"Initialized Jetbase project in {Path(BASE_DIR).absolute()}\n"
        "Run 'cd jetbase' to get started!"
    )
