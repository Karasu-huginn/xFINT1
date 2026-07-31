import pytest

from app.auth.models import ActivationToken
from app.core.enums import Role
from app.core.exceptions import ConflictError
from app.core.security import hash_activation_token
from app.users.service import create_user, find_user_by_email


def test_create_user_returns_user_and_raw_token(db_session):
    """Creating an account yields an unactivated user and a raw invite token."""
    user, raw_token = create_user(db_session, "alice@supherman.com", Role.EMPLOYEE)

    assert user.id is not None
    assert user.password_hash is None
    assert user.role is Role.EMPLOYEE
    assert len(raw_token) > 20


def test_create_user_persists_only_the_token_hash(db_session):
    """The database stores a digest, never the raw activation token."""
    _, raw_token = create_user(db_session, "bob@supherman.com", Role.EMPLOYEE)

    stored = db_session.query(ActivationToken).one()
    assert stored.token_hash == hash_activation_token(raw_token)
    assert stored.token_hash != raw_token
    assert stored.used_at is None


def test_create_user_normalises_email_to_lowercase(db_session):
    """Mixed-case addresses are stored lowercased so duplicates cannot slip in."""
    user, _ = create_user(db_session, "Carol@SupHerman.com", Role.MANAGER)
    assert user.email == "carol@supherman.com"


def test_create_user_rejects_a_duplicate_email(db_session):
    """A second account on the same address raises a conflict."""
    create_user(db_session, "dave@supherman.com", Role.EMPLOYEE)
    with pytest.raises(ConflictError):
        create_user(db_session, "DAVE@supherman.com", Role.ACCOUNTING)


def test_find_user_by_email_is_case_insensitive(db_session):
    """Lookup normalises the address before querying."""
    create_user(db_session, "erin@supherman.com", Role.EMPLOYEE)
    assert find_user_by_email(db_session, "ERIN@supherman.com") is not None
    assert find_user_by_email(db_session, "nobody@supherman.com") is None
