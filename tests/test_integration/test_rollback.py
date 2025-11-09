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

    assert len(users) == 6, f"Expected 6 users, but got {len(users)}"


@pytest.mark.count
def test_rollback_count(db_session):
    """Test that queries all users and asserts count."""
    result = db_session.execute(text("SELECT * FROM users"))
    users = result.fetchall()

    assert len(users) == 7, f"Expected 7 users, but got {len(users)}"


@pytest.mark.to_version
def test_rollback_to_version(db_session):
    """Test that queries all users and asserts count."""
    result = db_session.execute(text("SELECT * FROM users"))
    users = result.fetchall()

    assert len(users) == 3, f"Expected 3 users, but got {len(users)}"
