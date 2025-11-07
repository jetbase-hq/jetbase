from pathlib import Path

from jetbase.constants import BASE_DIR, CONFIG_FILE, CONFIG_FILE_CONTENT, MIGRATIONS_DIR


def create_directory_structure(base_path: str) -> None:
    """
    Create the basic directory structure for a new Jetbase project.

    This function creates:
    - A migrations directory
    - A config file with default content

    After creating the structure, it prints a confirmation message.

    Args:
        base_path (str): The base path where the Jetbase project structure will be created

    Returns:
        None
    """
    migrations_dir: Path = Path(base_path) / MIGRATIONS_DIR
    migrations_dir.mkdir(parents=True, exist_ok=True)

    config_path: Path = Path(base_path) / CONFIG_FILE
    with open(config_path, "w") as f:
        f.write(CONFIG_FILE_CONTENT)

    print(f"Initialized Jetbase project in {Path(base_path).absolute()}")


def initialize_cmd() -> None:
    create_directory_structure(base_path=BASE_DIR)
