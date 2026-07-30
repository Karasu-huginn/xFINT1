from app.core.enums import Role
from app.users.models import User


def test_user_persists_with_null_password_hash(db_session):
    """A newly invited user is stored with no password hash."""
    user = User(email="alice@supherman.com", role=Role.EMPLOYEE)
    db_session.add(user)
    db_session.flush()

    assert user.id is not None
    assert user.password_hash is None
    assert user.role is Role.EMPLOYEE
