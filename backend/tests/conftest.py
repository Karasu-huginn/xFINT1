import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app


@pytest.fixture(scope="session")
def test_engine():
    """Create the dedicated test database and return an engine bound to it."""
    database_name = settings.test_database_url.rsplit("/", 1)[1]
    admin_url = settings.test_database_url.rsplit("/", 1)[0] + "/postgres"
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as connection:
        is_present = connection.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": database_name},
        ).scalar()
        if not is_present:
            connection.execute(text(f'CREATE DATABASE "{database_name}"'))
    admin_engine.dispose()

    engine = create_engine(settings.test_database_url, pool_pre_ping=True)
    # create_all never alters an existing table, so a persistent test database would
    # keep a stale schema forever once a model changes. Dropping first makes every run
    # start from the models as written.
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


class SessionProvider:
    """Dependency override handing every request the same test session."""

    def __init__(self, session: Session) -> None:
        """Store the session this provider hands out."""
        self.session = session

    def __call__(self) -> Session:
        """Return the stored test session."""
        return self.session


@pytest.fixture
def db_session(test_engine):
    """Yield a session inside a transaction that is rolled back after the test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    # autoflush mirrors SessionLocal so endpoints run under the flush semantics they
    # will meet in production rather than a more forgiving variant.
    session = Session(
        bind=connection,
        autoflush=False,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session):
    """Yield a TestClient whose requests share the test transaction."""
    app.dependency_overrides[get_db] = SessionProvider(db_session)
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
