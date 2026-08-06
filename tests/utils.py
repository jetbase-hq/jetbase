import os


def is_clickhouse() -> bool:
    url: str = os.environ.get("JETBASE_SQLALCHEMY_URL", "")
    return "clickhouse" in url.lower()


def is_postgres() -> bool:
    url: str = os.environ.get("JETBASE_SQLALCHEMY_URL", "")
    return "postgres" in url.lower()
