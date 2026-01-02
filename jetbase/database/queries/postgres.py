from jetbase.database.queries.base import BaseQueries


class PostgresQueries(BaseQueries):
    """
    PostgreSQL-specific SQL queries.

    This class inherits all methods from BaseQueries without modification
    because the default queries in BaseQueries are already PostgreSQL-compatible.
    It exists to maintain consistency in the query loading pattern and to allow
    future PostgreSQL-specific optimizations.
    """

    pass
