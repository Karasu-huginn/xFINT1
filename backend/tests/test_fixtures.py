from sqlalchemy import func, select

from app.core.enums import Role
from app.users.models import User


def count_users(db_session):
    """Return the number of user rows visible to the given session."""
    return db_session.scalar(select(func.count()).select_from(User))


def test_client_fixture_serves_requests(client):
    """The client fixture builds a working TestClient with get_db overridden."""
    response = client.get("/api/health")

    assert response.status_code == 200


def test_pending_rows_are_not_autoflushed(db_session):
    """The test session mirrors SessionLocal, so a pending row stays invisible."""
    db_session.add(User(email="carol@supherman.com", role=Role.EMPLOYEE))

    assert count_users(db_session) == 0


def test_commit_inside_a_test_is_visible_to_the_same_session(db_session):
    """An explicit commit succeeds without destroying the enclosing transaction."""
    db_session.add(User(email="bob@supherman.com", role=Role.MANAGER))
    db_session.commit()

    assert count_users(db_session) == 1


def test_row_committed_by_a_previous_test_is_rolled_back(db_session):
    """The row committed by the preceding test left nothing behind."""
    assert count_users(db_session) == 0
