import os

from jetbase.cli.main import app


def test_init_jetbase_dir(tmp_path, runner) -> None:
    """Test the 'init' command initializes the migrations directory."""
    os.chdir(tmp_path)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0

    assert (tmp_path / "jetbase").exists()
    assert (tmp_path / "jetbase").is_dir()
    assert (tmp_path / "jetbase" / "migrations").exists()
    assert (tmp_path / "jetbase" / "migrations").is_dir()


def test_init_migrations_dir(tmp_path, runner) -> None:
    os.chdir(tmp_path)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0

    assert (tmp_path / "jetbase" / "migrations").exists()
    assert (tmp_path / "jetbase" / "migrations").is_dir()


def test_init_env_py(tmp_path, runner) -> None:
    os.chdir(tmp_path)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0

    assert (tmp_path / "jetbase" / "env.py").exists()
    assert (tmp_path / "jetbase" / "env.py").is_file()
