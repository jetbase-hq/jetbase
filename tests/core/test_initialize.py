from jetbase.constants import BASE_DIR, CONFIG_FILE, CONFIG_FILE_CONTENT, MIGRATIONS_DIR
from jetbase.core.initialize import create_directory_structure


def test_create_directory_structure(tmp_path, capsys) -> None:
    base_path = tmp_path / BASE_DIR
    create_directory_structure(str(base_path))

    # Check if migrations directory is created
    migrations_dir = base_path / MIGRATIONS_DIR
    assert migrations_dir.exists() and migrations_dir.is_dir()

    # Check if config file is created
    config_path = base_path / CONFIG_FILE
    assert config_path.exists() and config_path.is_file()

    # Check the content of the config file
    with open(config_path, "r") as f:
        content = f.read()
    assert content == CONFIG_FILE_CONTENT

    assert (
        capsys.readouterr().out.strip()
        == f"Initialized Jetbase project in {base_path.absolute()}"
    )
