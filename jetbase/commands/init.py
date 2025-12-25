from jetbase.constants import BASE_DIR
from jetbase.core.initialize import create_directory_structure


def initialize_cmd() -> None:
    create_directory_structure(base_path=BASE_DIR)
