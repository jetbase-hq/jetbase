import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def db_session():
    """Create a database session for testing."""
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/test_db"
    )

    engine = create_engine(url=DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()


@pytest.mark.basic
def test_rollback(db_session):
    """Test that queries all users and asserts count."""
    result = db_session.execute(text("SELECT * FROM users"))
    users = result.fetchall()

    assert len(users) == 3, f"Expected 3 users, but got {len(users)}"


@pytest.mark.count
def test_rollback_multiple_migrations(db_session):
    """Test that queries all users and asserts count."""
    result = db_session.execute(text("SELECT * FROM users"))
    users = result.fetchall()

    assert len(users) == 4, f"Expected 4 users, but got {len(users)}"
