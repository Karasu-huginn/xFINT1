from datetime import UTC, datetime, timedelta

from sqlalchemy import text

from app.auth.models import ActivationToken
from app.core.config import settings
from app.core.enums import Role
from app.users.service import create_user


def invite(db_session, email: str = "newhire@supherman.com") -> str:
    """Provision an account directly and return its raw activation token."""
    _, raw_token = create_user(db_session, email, Role.EMPLOYEE)
    return raw_token


def test_activation_probe_returns_the_invited_email(client, db_session):
    """A valid token reports which address it activates."""
    raw_token = invite(db_session)

    response = client.get(f"/api/auth/activation/{raw_token}")
    assert response.status_code == 200
    assert response.json()["email"] == "newhire@supherman.com"


def test_activation_probe_rejects_an_unknown_token(client):
    """A forged token is indistinguishable from a missing one."""
    assert client.get("/api/auth/activation/forged-token").status_code == 404


def test_activation_sets_the_password_and_logs_the_user_in(client, db_session):
    """Activating stores the chosen password and issues a session cookie."""
    raw_token = invite(db_session)

    response = client.post(
        "/api/auth/activate",
        json={"token": raw_token, "password": "Ch0senPass"},
    )

    assert response.status_code == 204
    assert "session" in response.cookies
    assert client.get("/api/auth/me").json()["email"] == "newhire@supherman.com"


def test_activated_user_can_log_in_with_the_new_password(client, db_session):
    """The password chosen at activation works on the normal login form."""
    raw_token = invite(db_session)
    client.post(
        "/api/auth/activate",
        json={"token": raw_token, "password": "Ch0senPass"},
    )
    client.post("/api/auth/logout")

    response = client.post(
        "/api/auth/login",
        json={"email": "newhire@supherman.com", "password": "Ch0senPass"},
    )
    assert response.status_code == 204


def test_token_cannot_be_reused(client, db_session):
    """A consumed token is refused on a second activation attempt."""
    raw_token = invite(db_session)
    client.post(
        "/api/auth/activate",
        json={"token": raw_token, "password": "Ch0senPass"},
    )

    response = client.post(
        "/api/auth/activate",
        json={"token": raw_token, "password": "An0therPass"},
    )
    assert response.status_code == 404


def test_expired_token_is_refused(client, db_session):
    """A token past its expiry cannot activate an account."""
    raw_token = invite(db_session)
    stored = db_session.query(ActivationToken).one()
    stored.expires_at = datetime.now(UTC) - timedelta(days=1)
    db_session.flush()

    response = client.post(
        "/api/auth/activate",
        json={"token": raw_token, "password": "Ch0senPass"},
    )
    assert response.status_code == 404


def test_weak_password_is_refused_at_activation(client, db_session):
    """A password failing the policy returns 400 and leaves the token unused."""
    raw_token = invite(db_session)

    response = client.post(
        "/api/auth/activate",
        json={"token": raw_token, "password": "short"},
    )

    assert response.status_code == 400
    assert db_session.query(ActivationToken).one().used_at is None


def test_a_weak_password_is_refused_before_the_token_is_looked_up(client, db_session):
    """With both inputs bad the policy answers first, so the status is 400 not 404."""
    raw_token = invite(db_session)
    client.post(
        "/api/auth/activate",
        json={"token": raw_token, "password": "Ch0senPass"},
    )

    # Status precedence is the only observable consequence of running the policy
    # check before the lookup, since the lookup itself writes nothing. Asserting an
    # unused token after a weak password passes whichever order the two run in.
    response = client.post(
        "/api/auth/activate",
        json={"token": raw_token, "password": "short"},
    )
    assert response.status_code == 400


def test_minted_token_expiry_holds_under_a_non_utc_session_timezone(db_session):
    """A minted token expires the configured days out whatever the session zone."""
    # The session timezone is deliberately not UTC. Postgres reads a timestamptz
    # back as aware whatever Python wrote, so a naive expiry passes every check
    # made under a UTC session while silently landing hours off the mark here.
    db_session.execute(text("SET LOCAL TIME ZONE 'America/New_York'"))

    invite(db_session)

    stored = db_session.query(ActivationToken).one()
    expected_expiry = datetime.now(UTC) + timedelta(
        days=settings.activation_token_expire_days
    )
    assert abs((stored.expires_at - expected_expiry).total_seconds()) < 60
