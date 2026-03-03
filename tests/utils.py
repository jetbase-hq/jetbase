import os


def is_clickhouse():
    url = os.environ.get("JETBASE_SQLALCHEMY_URL", "")
    return "clickhouse" in url.lower()
