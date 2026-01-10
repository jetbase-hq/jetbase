def test_cryptography_is_installed():
    """Test that cryptography is installed when jetbase[snowflake] is installed."""
    try:
        import cryptography  # type: ignore[missing-import] # noqa: F401

        assert True
    except ImportError:
        assert False, "cryptography should be installed with jetbase[snowflake]"


def test_snowflake_sqlalchemy_is_installed():
    """Test that snowflake-sqlalchemy is installed when jetbase[snowflake] is installed."""
    try:
        import snowflake.sqlalchemy  # type: ignore[missing-import] # noqa: F401

        assert True
    except ImportError:
        assert False, "snowflake-sqlalchemy should be installed with jetbase[snowflake]"
