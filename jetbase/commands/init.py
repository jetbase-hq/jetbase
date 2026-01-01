from pathlib import Path

from jetbase.constants import BASE_DIR, ENV_FILE, ENV_FILE_CONTENT, MIGRATIONS_DIR

# def initialize_cmd() -> None:
#     create_directory_structure(base_path=BASE_DIR)


def initialize_cmd() -> None:
    """
    Create the basic directory structure for a new Jetbase project.

    This function creates:
    - A migrations directory
    - An env.py file with default content

    After creating the structure, it prints a confirmation message.

    Args:
        base_path (str): The base path where the Jetbase project structure will be created

    Returns:
        None
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
