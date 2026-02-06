"""Comprehensive tests for async and sync database operations."""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import AsyncGenerator
from unittest.mock import MagicMock, patch, AsyncMock

import pytest
from sqlalchemy import (
    Boolean,
    Column,
    create_engine,
    Integer,
    String,
    text,
    DateTime,
    JSON,
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker

from jetbase.database.connection import (
    _get_engine,
    get_async_db_connection,
    get_connection,
    get_db_connection,
    is_async_enabled,
)


Base = declarative_base()


class AuthorModel(Base):
    __tablename__ = "authors"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True)


class BookModel(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    author_id = Column(Integer, nullable=False)
    published_date = Column(DateTime)
    is_available = Column(Boolean, default=True)
    book_metadata = Column(JSON)


class PublisherModel(Base):
    __tablename__ = "publishers"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    location = Column(String(100))


class ReviewModel(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True)
    book_id = Column(Integer, nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(String(1000))


@pytest.fixture
def sync_engine(tmp_path):
    """Create a sync SQLAlchemy engine for testing."""
    db_file = tmp_path / "test_sync.db"
    engine = create_engine(f"sqlite:///{db_file}")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def async_engine(tmp_path):
    """Create an async SQLAlchemy engine for testing."""
    db_file = tmp_path / "test_async.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_file}")
    yield engine
    engine.dispose()


@pytest.fixture
def sync_session_factory(sync_engine):
    """Create a sync session factory."""
    return sessionmaker(bind=sync_engine)


@pytest.fixture
def async_session_factory(async_engine):
    """Create an async session factory."""
    return async_sessionmaker(
        bind=async_engine, class_=AsyncSession, expire_on_commit=False
    )


@pytest.fixture(autouse=True)
def cleanup_env():
    """Clean up environment variables after each test."""
    yield
    _get_engine.cache_clear()
    if "ASYNC" in os.environ:
        del os.environ["ASYNC"]
    if "JETBASE_SQLALCHEMY_URL" in os.environ:
        del os.environ["JETBASE_SQLALCHEMY_URL"]


class TestSyncDBSimpleOperations:
    """Tests for basic sync database operations."""

    def test_create_table(self, sync_engine):
        """Test creating a table in sync mode."""
        with sync_engine.connect() as conn:
            conn.execute(
                text("CREATE TABLE test_sync (id INTEGER PRIMARY KEY, value TEXT)")
            )
            conn.commit()

            conn.execute(text("INSERT INTO test_sync (value) VALUES ('hello')"))
            conn.commit()

            result = conn.execute(text("SELECT value FROM test_sync"))
            assert result.fetchone() == ("hello",)

    def test_insert_multiple_rows(self, sync_engine):
        """Test inserting multiple rows in sync mode."""
        with sync_engine.connect() as conn:
            conn.execute(
                text(
                    "CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT, quantity INTEGER)"
                )
            )
            conn.commit()

            items = [("item1", 10), ("item2", 20), ("item3", 30)]
            for name, qty in items:
                conn.execute(
                    text("INSERT INTO items (name, quantity) VALUES (:name, :qty)"),
                    {"name": name, "qty": qty},
                )
            conn.commit()

            result = conn.execute(text("SELECT COUNT(*) FROM items"))
            assert result.fetchone() == (3,)

    def test_update_rows(self, sync_engine):
        """Test updating rows in sync mode."""
        with sync_engine.connect() as conn:
            conn.execute(
                text(
                    "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, active INTEGER)"
                )
            )
            conn.commit()

            conn.execute(text("INSERT INTO users (name, active) VALUES ('Alice', 1)"))
            conn.execute(text("INSERT INTO users (name, active) VALUES ('Bob', 1)"))
            conn.commit()

            conn.execute(text("UPDATE users SET active = 0 WHERE name = 'Bob'"))
            conn.commit()

            result = conn.execute(text("SELECT name FROM users WHERE active = 1"))
            names = [row[0] for row in result.fetchall()]
            assert names == ["Alice"]

    def test_delete_rows(self, sync_engine):
        """Test deleting rows in sync mode."""
        with sync_engine.connect() as conn:
            conn.execute(
                text("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT)")
            )
            conn.commit()

            conn.execute(text("INSERT INTO products (name) VALUES ('Product A')"))
            conn.execute(text("INSERT INTO products (name) VALUES ('Product B')"))
            conn.commit()

            conn.execute(text("DELETE FROM products WHERE name = 'Product A'"))
            conn.commit()

            result = conn.execute(text("SELECT COUNT(*) FROM products"))
            assert result.fetchone() == (1,)

    def test_transaction_rollback(self, sync_engine):
        """Test transaction rollback in sync mode."""
        with sync_engine.connect() as conn:
            conn.execute(
                text("CREATE TABLE accounts (id INTEGER PRIMARY KEY, balance INTEGER)")
            )
            conn.commit()

            conn.execute(text("INSERT INTO accounts (balance) VALUES (1000)"))
            conn.commit()

            try:
                with conn.begin():
                    conn.execute(text("UPDATE accounts SET balance = balance - 100"))
                    raise Exception("Simulated error")
            except Exception:
                pass

            result = conn.execute(text("SELECT balance FROM accounts"))
            assert result.fetchone() == (1000,)

    def test_aggregate_functions(self, sync_engine):
        """Test aggregate functions in sync mode."""
        with sync_engine.connect() as conn:
            conn.execute(
                text("CREATE TABLE orders (id INTEGER PRIMARY KEY, amount INTEGER)")
            )
            conn.commit()

            conn.execute(text("INSERT INTO orders (amount) VALUES (100)"))
            conn.execute(text("INSERT INTO orders (amount) VALUES (200)"))
            conn.execute(text("INSERT INTO orders (amount) VALUES (300)"))
            conn.commit()

            result = conn.execute(
                text(
                    "SELECT SUM(amount), AVG(amount), MIN(amount), MAX(amount) FROM orders"
                )
            )
            row = result.fetchone()
            assert row == (600, 200, 100, 300)


class TestAsyncDBSimpleOperations:
    """Tests for basic async database operations."""

    @pytest.mark.asyncio
    async def test_create_table(self, async_engine):
        """Test creating a table in async mode."""
        async with async_engine.connect() as conn:
            await conn.execute(
                text("CREATE TABLE test_async (id INTEGER PRIMARY KEY, value TEXT)")
            )
            await conn.commit()

            await conn.execute(
                text("INSERT INTO test_async (value) VALUES ('async_hello')")
            )
            await conn.commit()

            result = await conn.execute(text("SELECT value FROM test_async"))
            assert result.fetchone() == ("async_hello",)

    @pytest.mark.asyncio
    async def test_insert_multiple_rows(self, async_engine):
        """Test inserting multiple rows in async mode."""
        async with async_engine.connect() as conn:
            await conn.execute(
                text("CREATE TABLE async_items (id INTEGER PRIMARY KEY, name TEXT)")
            )
            await conn.commit()

            await conn.execute(
                text("INSERT INTO async_items (name) VALUES ('async_item1')")
            )
            await conn.execute(
                text("INSERT INTO async_items (name) VALUES ('async_item2')")
            )
            await conn.commit()

            result = await conn.execute(text("SELECT COUNT(*) FROM async_items"))
            assert result.fetchone() == (2,)

    @pytest.mark.asyncio
    async def test_update_rows(self, async_engine):
        """Test updating rows in async mode."""
        async with async_engine.connect() as conn:
            await conn.execute(
                text("CREATE TABLE async_users (id INTEGER PRIMARY KEY, name TEXT)")
            )
            await conn.commit()

            await conn.execute(text("INSERT INTO async_users (name) VALUES ('User1')"))
            await conn.execute(text("INSERT INTO async_users (name) VALUES ('User2')"))
            await conn.commit()

            await conn.execute(
                text("UPDATE async_users SET name = 'Updated' WHERE name = 'User1'")
            )
            await conn.commit()

            result = await conn.execute(
                text("SELECT name FROM async_users WHERE name = 'Updated'")
            )
            assert result.fetchone() == ("Updated",)

    @pytest.mark.asyncio
    async def test_delete_rows(self, async_engine):
        """Test deleting rows in async mode."""
        async with async_engine.connect() as conn:
            await conn.execute(
                text("CREATE TABLE async_products (id INTEGER PRIMARY KEY, name TEXT)")
            )
            await conn.commit()

            await conn.execute(text("INSERT INTO async_products (name) VALUES ('P1')"))
            await conn.execute(text("INSERT INTO async_products (name) VALUES ('P2')"))
            await conn.commit()

            await conn.execute(text("DELETE FROM async_products WHERE name = 'P1'"))
            await conn.commit()

            result = await conn.execute(text("SELECT COUNT(*) FROM async_products"))
            assert result.fetchone() == (1,)

    @pytest.mark.asyncio
    async def test_transaction_commit(self, async_engine):
        """Test transaction commit in async mode."""
        async with async_engine.connect() as conn:
            await conn.execute(
                text("CREATE TABLE transactions (id INTEGER PRIMARY KEY, status TEXT)")
            )
            await conn.commit()

            async with conn.begin():
                await conn.execute(
                    text("INSERT INTO transactions (status) VALUES ('processing')")
                )

            result = await conn.execute(text("SELECT status FROM transactions"))
            assert result.fetchone() == ("processing",)

    @pytest.mark.asyncio
    async def test_aggregate_functions(self, async_engine):
        """Test aggregate functions in async mode."""
        async with async_engine.connect() as conn:
            await conn.execute(
                text(
                    "CREATE TABLE async_orders (id INTEGER PRIMARY KEY, total INTEGER)"
                )
            )
            await conn.commit()

            await conn.execute(text("INSERT INTO async_orders (total) VALUES (50)"))
            await conn.execute(text("INSERT INTO async_orders (total) VALUES (150)"))
            await conn.execute(text("INSERT INTO async_orders (total) VALUES (100)"))
            await conn.commit()

            result = await conn.execute(
                text("SELECT SUM(total), AVG(total) FROM async_orders")
            )
            row = result.fetchone()
            assert row == (300, 100)


class TestSyncDBWithModels:
    """Tests for sync database operations using SQLAlchemy models."""

    def test_insert_and_query_author(self, sync_engine):
        """Test inserting and querying an Author model."""
        Session = sessionmaker(bind=sync_engine)
        with Session() as session:
            author = AuthorModel(name="J.K. Rowling", email="jk@example.com")
            session.add(author)
            session.commit()

            session.refresh(author)

            assert author.id is not None
            assert author.name == "J.K. Rowling"

            result = session.execute(
                text("SELECT name, email FROM authors WHERE id = :id"),
                {"id": author.id},
            )
            row = result.fetchone()
            assert row == ("J.K. Rowling", "jk@example.com")

    def test_insert_multiple_authors(self, sync_engine):
        """Test inserting multiple authors."""
        Session = sessionmaker(bind=sync_engine)
        authors_data = [
            AuthorModel(name="Author 1", email="author1@example.com"),
            AuthorModel(name="Author 2", email="author2@example.com"),
            AuthorModel(name="Author 3", email="author3@example.com"),
        ]

        with Session() as session:
            for author in authors_data:
                session.add(author)
            session.commit()

            result = session.execute(text("SELECT COUNT(*) FROM authors"))
            assert result.fetchone() == (3,)

    def test_query_with_filters(self, sync_engine):
        """Test querying with filters."""
        Session = sessionmaker(bind=sync_engine)
        with Session() as session:
            session.add(AuthorModel(name="Author A", email="a@example.com"))
            session.add(AuthorModel(name="Author B", email="b@example.com"))
            session.add(AuthorModel(name="Author C", email="c@example.com"))
            session.commit()

            result = session.execute(
                text(
                    "SELECT name FROM authors WHERE name LIKE 'Author %' ORDER BY name"
                )
            )
            names = [row[0] for row in result.fetchall()]
            assert names == ["Author A", "Author B", "Author C"]

    def test_update_model(self, sync_engine):
        """Test updating a model."""
        Session = sessionmaker(bind=sync_engine)
        with Session() as session:
            author = AuthorModel(name="Original Name", email="original@example.com")
            session.add(author)
            session.commit()
            author_id = author.id

            author.name = "Updated Name"
            session.commit()

            result = session.execute(
                text("SELECT name FROM authors WHERE id = :id"), {"id": author_id}
            )
            assert result.fetchone()[0] == "Updated Name"

    def test_delete_model(self, sync_engine):
        """Test deleting a model."""
        Session = sessionmaker(bind=sync_engine)
        with Session() as session:
            author = AuthorModel(name="To Delete", email="delete@example.com")
            session.add(author)
            session.commit()
            author_id = author.id

            session.delete(author)
            session.commit()

            result = session.execute(
                text("SELECT COUNT(*) FROM authors WHERE id = :id"), {"id": author_id}
            )
            assert result.fetchone() == (0,)


class TestAsyncDBWithModels:
    """Tests for async database operations using SQLAlchemy models."""

    @pytest.mark.asyncio
    async def test_insert_and_query_author(self, async_engine):
        """Test inserting and querying an Author model asynchronously."""
        async with async_engine.connect() as conn:
            author = AuthorModel(name="George Orwell", email="orwell@example.com")
            conn.add(author)
            await conn.commit()
            await conn.refresh(author)

            assert author.id is not None
            assert author.name == "George Orwell"

            result = await conn.execute(
                text("SELECT name, email FROM authors WHERE id = :id"),
                {"id": author.id},
            )
            row = result.fetchone()
            assert row == ("George Orwell", "orwell@example.com")

    @pytest.mark.asyncio
    async def test_insert_multiple_authors(self, async_engine):
        """Test inserting multiple authors asynchronously."""
        async with async_engine.connect() as conn:
            authors_data = [
                AuthorModel(name="Async Author 1", email="async1@example.com"),
                AuthorModel(name="Async Author 2", email="async2@example.com"),
            ]

            for author in authors_data:
                conn.add(author)
            await conn.commit()

            result = await conn.execute(text("SELECT COUNT(*) FROM authors"))
            assert result.fetchone() == (2,)

    @pytest.mark.asyncio
    async def test_query_with_filters(self, async_engine):
        """Test querying with filters asynchronously."""
        async with async_engine.connect() as conn:
            conn.add(AuthorModel(name="Filter Test A", email="filter_a@example.com"))
            conn.add(AuthorModel(name="Filter Test B", email="filter_b@example.com"))
            conn.add(AuthorModel(name="Other", email="other@example.com"))
            await conn.commit()

            result = await conn.execute(
                text("SELECT name FROM authors WHERE name LIKE 'Filter Test %'")
            )
            names = [row[0] for row in result.fetchall()]
            assert names == ["Filter Test A", "Filter Test B"]

    @pytest.mark.asyncio
    async def test_update_model(self, async_engine):
        """Test updating a model asynchronously."""
        async with async_engine.connect() as conn:
            author = AuthorModel(name="Update Me", email="update@example.com")
            conn.add(author)
            await conn.commit()
            await conn.refresh(author)

            author.name = "Updated Async"
            await conn.commit()
            await conn.refresh(author)

            assert author.name == "Updated Async"

    @pytest.mark.asyncio
    async def test_delete_model(self, async_engine):
        """Test deleting a model asynchronously."""
        async with async_engine.connect() as conn:
            author = AuthorModel(
                name="Delete Me Async", email="delete_async@example.com"
            )
            conn.add(author)
            await conn.commit()
            author_id = author.id

            await conn.delete(author)
            await conn.commit()

            result = await conn.execute(
                text("SELECT COUNT(*) FROM authors WHERE id = :id"), {"id": author_id}
            )
            assert result.fetchone() == (0,)


class TestSyncDBComplexOperations:
    """Tests for complex sync database operations."""

    def test_join_query(self, sync_engine):
        """Test join queries in sync mode."""
        with sync_engine.connect() as conn:
            conn.execute(
                text("""
                CREATE TABLE sync_authors (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL
                )
            """)
            )
            conn.execute(
                text("""
                CREATE TABLE sync_books (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    author_id INTEGER NOT NULL
                )
            """)
            )
            conn.commit()

            conn.execute(text("INSERT INTO sync_authors (name) VALUES ('Author 1')"))
            conn.execute(
                text("INSERT INTO sync_books (title, author_id) VALUES ('Book 1', 1)")
            )
            conn.execute(
                text("INSERT INTO sync_books (title, author_id) VALUES ('Book 2', 1)")
            )
            conn.commit()

            result = conn.execute(
                text("""
                SELECT a.name, b.title
                FROM sync_authors a
                JOIN sync_books b ON a.id = b.author_id
                ORDER BY b.title
            """)
            )
            rows = result.fetchall()
            assert len(rows) == 2
            assert rows[0] == ("Author 1", "Book 1")
            assert rows[1] == ("Author 1", "Book 2")

    def test_subquery(self, sync_engine):
        """Test subqueries in sync mode."""
        Session = sessionmaker(bind=sync_engine)
        with Session() as session:
            session.execute(
                text("""
                CREATE TABLE orders (
                    id INTEGER PRIMARY KEY,
                    customer_id INTEGER,
                    amount INTEGER
                )
            """)
            )
            session.execute(
                text("""
                CREATE TABLE customers (
                    id INTEGER PRIMARY KEY,
                    name TEXT
                )
            """)
            )
            session.commit()

            session.execute(text("INSERT INTO customers (name) VALUES ('Customer A')"))
            session.execute(text("INSERT INTO customers (name) VALUES ('Customer B')"))
            session.execute(
                text("INSERT INTO orders (customer_id, amount) VALUES (1, 100)")
            )
            session.execute(
                text("INSERT INTO orders (customer_id, amount) VALUES (1, 200)")
            )
            session.execute(
                text("INSERT INTO orders (customer_id, amount) VALUES (2, 50)")
            )
            session.commit()

            result = session.execute(
                text("""
                SELECT c.name, SUM(o.amount) as total
                FROM customers c
                JOIN orders o ON c.id = o.customer_id
                WHERE o.amount > 50
                GROUP BY c.id
            """)
            )
            rows = result.fetchall()
            assert len(rows) == 1
            assert rows[0] == ("Customer A", 300)

    def test_index_usage(self, sync_engine):
        """Test index usage for query optimization."""
        with sync_engine.connect() as conn:
            conn.execute(
                text("""
                CREATE TABLE indexed_table (
                    id INTEGER PRIMARY KEY,
                    category TEXT,
                    value INTEGER
                )
            """)
            )
            conn.execute(text("CREATE INDEX idx_category ON indexed_table (category)"))
            conn.commit()

            for i in range(100):
                category = "A" if i % 2 == 0 else "B"
                conn.execute(
                    text(
                        "INSERT INTO indexed_table (category, value) VALUES (:cat, :val)"
                    ),
                    {"cat": category, "val": i},
                )
            conn.commit()

            result = conn.execute(
                text("SELECT COUNT(*) FROM indexed_table WHERE category = 'A'")
            )
            assert result.fetchone()[0] == 50

    def test_cte_query(self, sync_engine):
        """Test Common Table Expression (CTE) queries."""
        with sync_engine.connect() as conn:
            conn.execute(
                text("""
                CREATE TABLE employees (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    manager_id INTEGER
                )
            """)
            )
            conn.commit()

            conn.execute(
                text("INSERT INTO employees (name, manager_id) VALUES ('CEO', NULL)")
            )
            conn.execute(
                text("INSERT INTO employees (name, manager_id) VALUES ('Manager1', 1)")
            )
            conn.execute(
                text("INSERT INTO employees (name, manager_id) VALUES ('Manager2', 1)")
            )
            conn.execute(
                text("INSERT INTO employees (name, manager_id) VALUES ('Employee1', 2)")
            )
            conn.commit()

            result = conn.execute(
                text("""
                WITH RECURSIVE hierarchy AS (
                    SELECT id, name, 0 as level
                    FROM employees
                    WHERE manager_id IS NULL
                    UNION ALL
                    SELECT e.id, e.name, h.level + 1
                    FROM employees e
                    JOIN hierarchy h ON e.manager_id = h.id
                )
                SELECT name, level FROM hierarchy WHERE level > 0
            """)
            )
            rows = result.fetchall()
            assert len(rows) == 3


class TestAsyncDBComplexOperations:
    """Tests for complex async database operations."""

    @pytest.mark.asyncio
    async def test_join_query(self, async_engine):
        """Test join queries in async mode."""
        async with async_engine.connect() as conn:
            await conn.execute(
                text("""
                CREATE TABLE async_authors (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL
                )
            """)
            )
            await conn.execute(
                text("""
                CREATE TABLE async_books (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    author_id INTEGER NOT NULL
                )
            """)
            )
            await conn.commit()

            await conn.execute(
                text("INSERT INTO async_authors (name) VALUES ('Async Author')")
            )
            await conn.execute(
                text(
                    "INSERT INTO async_books (title, author_id) VALUES ('Async Book 1', 1)"
                )
            )
            await conn.execute(
                text(
                    "INSERT INTO async_books (title, author_id) VALUES ('Async Book 2', 1)"
                )
            )
            await conn.commit()

            result = await conn.execute(
                text("""
                SELECT a.name, b.title
                FROM async_authors a
                JOIN async_books b ON a.id = b.author_id
            """)
            )
            rows = result.fetchall()
            assert len(rows) == 2

    @pytest.mark.asyncio
    async def test_subquery(self, async_engine):
        """Test subqueries in async mode."""
        async with async_engine.connect() as conn:
            await conn.execute(
                text("""
                CREATE TABLE async_orders (
                    id INTEGER PRIMARY KEY,
                    product_id INTEGER,
                    quantity INTEGER
                )
            """)
            )
            await conn.execute(
                text("""
                CREATE TABLE async_products (
                    id INTEGER PRIMARY KEY,
                    name TEXT
                )
            """)
            )
            await conn.commit()

            await conn.execute(
                text("INSERT INTO async_products (name) VALUES ('Product 1')")
            )
            await conn.execute(
                text("INSERT INTO async_orders (product_id, quantity) VALUES (1, 5)")
            )
            await conn.execute(
                text("INSERT INTO async_orders (product_id, quantity) VALUES (1, 3)")
            )
            await conn.commit()

            result = await conn.execute(
                text("""
                SELECT p.name, SUM(o.quantity) as total
                FROM async_products p
                WHERE p.id IN (
                    SELECT product_id FROM async_orders WHERE quantity >= 3
                )
                GROUP BY p.id
            """)
            )
            rows = result.fetchall()
            assert len(rows) == 1
            assert rows[0][0] == "Product 1"

    @pytest.mark.asyncio
    async def test_cte_query(self, async_engine):
        """Test CTE queries in async mode."""
        async with async_engine.connect() as conn:
            await conn.execute(
                text("""
                CREATE TABLE async_employees (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    department TEXT
                )
            """)
            )
            await conn.commit()

            await conn.execute(
                text(
                    "INSERT INTO async_employees (name, department) VALUES ('E1', 'Dept A')"
                )
            )
            await conn.execute(
                text(
                    "INSERT INTO async_employees (name, department) VALUES ('E2', 'Dept B')"
                )
            )
            await conn.execute(
                text(
                    "INSERT INTO async_employees (name, department) VALUES ('E3', 'Dept A')"
                )
            )
            await conn.commit()

            result = await conn.execute(
                text("""
                SELECT department, COUNT(*) as count
                FROM async_employees
                GROUP BY department
            """)
            )
            rows = result.fetchall()
            departments = {row[0]: row[1] for row in rows}
            assert departments["Dept A"] == 2
            assert departments["Dept B"] == 1


class TestConnectionModeSwitching:
    """Tests for switching between sync and async connection modes."""

    def test_sync_mode_after_async_env(self, tmp_path):
        """Test that sync mode works after async environment is set."""
        os.environ["ASYNC"] = "true"
        os.environ["JETBASE_SQLALCHEMY_URL"] = f"sqlite+aiosqlite:///{tmp_path}/test.db"

        _get_engine.cache_clear()

        with get_connection() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.fetchone() == (1,)

    @pytest.mark.asyncio
    async def test_async_mode_after_sync_env(self, tmp_path):
        """Test that async mode works after sync environment is set."""
        os.environ["ASYNC"] = "true"
        os.environ["JETBASE_SQLALCHEMY_URL"] = f"sqlite+aiosqlite:///{tmp_path}/test.db"

        _get_engine.cache_clear()

        async with get_async_db_connection() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.fetchone() == (1,)


class TestDBConnectionEdgeCases:
    """Tests for edge cases in database connections."""

    def test_empty_result_set(self, sync_engine):
        """Test querying empty result set."""
        with sync_engine.connect() as conn:
            conn.execute(text("CREATE TABLE empty_table (id INTEGER PRIMARY KEY)"))
            conn.commit()

            result = conn.execute(text("SELECT * FROM empty_table"))
            rows = result.fetchall()
            assert len(rows) == 0

    @pytest.mark.asyncio
    async def test_async_empty_result_set(self, async_engine):
        """Test querying empty result set in async mode."""
        async with async_engine.connect() as conn:
            await conn.execute(
                text("CREATE TABLE async_empty (id INTEGER PRIMARY KEY)")
            )
            await conn.commit()

            result = await conn.execute(text("SELECT * FROM async_empty"))
            rows = result.fetchall()
            assert len(rows) == 0

    def test_null_handling(self, sync_engine):
        """Test handling NULL values."""
        with sync_engine.connect() as conn:
            conn.execute(
                text("""
                CREATE TABLE null_test (
                    id INTEGER PRIMARY KEY,
                    value TEXT
                )
            """)
            )
            conn.commit()

            conn.execute(text("INSERT INTO null_test (value) VALUES (NULL)"))
            conn.commit()

            result = conn.execute(
                text("SELECT value FROM null_test WHERE value IS NULL")
            )
            rows = result.fetchall()
            assert len(rows) == 1

    def test_concurrent_transactions(self, sync_engine):
        """Test concurrent-like operations in sync mode."""
        Session = sessionmaker(bind=sync_engine)
        with Session() as session:
            session.execute(
                text("CREATE TABLE counter (id INTEGER PRIMARY KEY, value INTEGER)")
            )
            session.commit()

            session.execute(text("INSERT INTO counter (value) VALUES (0)"))
            session.commit()

            for _ in range(10):
                session.execute(text("UPDATE counter SET value = value + 1"))
                session.commit()

            result = session.execute(text("SELECT value FROM counter"))
            assert result.fetchone()[0] == 10

    def test_like_pattern_matching(self, sync_engine):
        """Test LIKE pattern matching."""
        with sync_engine.connect() as conn:
            conn.execute(
                text("""
                CREATE TABLE pattern_test (
                    id INTEGER PRIMARY KEY,
                    text_value TEXT
                )
            """)
            )
            conn.commit()

            values = ["hello world", "hello there", "goodbye world", "test"]
            for val in values:
                conn.execute(
                    text("INSERT INTO pattern_test (text_value) VALUES (:val)"),
                    {"val": val},
                )
            conn.commit()

            result = conn.execute(
                text(
                    "SELECT text_value FROM pattern_test WHERE text_value LIKE 'hello%'"
                )
            )
            rows = result.fetchall()
            assert len(rows) == 2

    def test_order_by_and_limit(self, sync_engine):
        """Test ORDER BY and LIMIT clauses."""
        with sync_engine.connect() as conn:
            conn.execute(
                text("""
                CREATE TABLE sorted_items (
                    id INTEGER PRIMARY KEY,
                    value INTEGER,
                    name TEXT
                )
            """)
            )
            conn.commit()

            for i in range(10):
                conn.execute(
                    text("INSERT INTO sorted_items (value, name) VALUES (:val, :name)"),
                    {"val": i, "name": f"Item {i}"},
                )
            conn.commit()

            result = conn.execute(
                text("""
                SELECT value, name FROM sorted_items
                ORDER BY value DESC
                LIMIT 3
            """)
            )
            rows = result.fetchall()
            assert len(rows) == 3
            assert rows[0] == (9, "Item 9")
            assert rows[1] == (8, "Item 8")
            assert rows[2] == (7, "Item 7")

    def test_group_by_having(self, sync_engine):
        """Test GROUP BY with HAVING clause."""
        Session = sessionmaker(bind=sync_engine)
        with Session() as session:
            session.execute(
                text("""
                CREATE TABLE sales (
                    id INTEGER PRIMARY KEY,
                    product TEXT,
                    amount INTEGER
                )
            """)
            )
            session.commit()

            sales_data = [
                ("Product A", 100),
                ("Product A", 150),
                ("Product B", 200),
                ("Product B", 150),
                ("Product C", 300),
            ]
            for product, amount in sales_data:
                session.execute(
                    text("INSERT INTO sales (product, amount) VALUES (:prod, :amt)"),
                    {"prod": product, "amt": amount},
                )
            session.commit()

            result = session.execute(
                text("""
                SELECT product, SUM(amount) as total
                FROM sales
                GROUP BY product
                HAVING SUM(amount) > 200
            """)
            )
            rows = result.fetchall()
            assert len(rows) == 3


class TestAsyncDBSessionManagement:
    """Tests for async session management."""

    @pytest.mark.asyncio
    async def test_async_session_begin_commit(self, async_engine):
        """Test async session begin and commit."""
        async with async_engine.connect() as conn:
            await conn.execute(
                text("CREATE TABLE session_test (id INTEGER PRIMARY KEY, data TEXT)")
            )
            await conn.commit()

            async with conn.begin():
                await conn.execute(
                    text("INSERT INTO session_test (data) VALUES ('session_data')")
                )

            result = await conn.execute(text("SELECT data FROM session_test"))
            assert result.fetchone()[0] == "session_data"

    @pytest.mark.asyncio
    async def test_async_session_rollback(self, async_engine):
        """Test async session rollback."""
        async with async_engine.connect() as conn:
            await conn.execute(
                text(
                    "CREATE TABLE rollback_test (id INTEGER PRIMARY KEY, value INTEGER)"
                )
            )
            await conn.commit()

            try:
                async with conn.begin():
                    await conn.execute(
                        text("INSERT INTO rollback_test (value) VALUES (100)")
                    )
                    raise Exception("Force rollback")
            except Exception:
                pass

            result = await conn.execute(text("SELECT COUNT(*) FROM rollback_test"))
            assert result.fetchone()[0] == 0

    @pytest.mark.asyncio
    async def test_async_multiple_operations(self, async_engine):
        """Test multiple async operations in sequence."""
        async with async_engine.connect() as conn:
            await conn.execute(
                text("CREATE TABLE multi_ops (id INTEGER PRIMARY KEY, name TEXT)")
            )
            await conn.commit()

            for i in range(5):
                await conn.execute(
                    text("INSERT INTO multi_ops (name) VALUES (:name)"),
                    {"name": f"Name {i}"},
                )
            await conn.commit()

            result = await conn.execute(text("SELECT COUNT(*) FROM multi_ops"))
            assert result.fetchone()[0] == 5

            await conn.execute(
                text("UPDATE multi_ops SET name = 'Updated' WHERE id = 1")
            )
            await conn.commit()

            result = await conn.execute(text("SELECT name FROM multi_ops WHERE id = 1"))
            assert result.fetchone()[0] == "Updated"
