from app.core.enums import Role
from app.core.security import hash_password
from app.users.models import User


def create_active_user(db_session, email: str, password: str, role: Role) -> User:
    """Persist a user who has already chosen a password."""
    user = User(email=email, password_hash=hash_password(password), role=role)
    db_session.add(user)
    db_session.flush()
    return user


def test_login_succeeds_and_sets_a_session_cookie(client, db_session):
    """Correct credentials return 204 and an httpOnly session cookie."""
    create_active_user(db_session, "alice@supherman.com", "Passw0rd!", Role.EMPLOYEE)

    response = client.post(
        "/api/auth/login",
        json={"email": "alice@supherman.com", "password": "Passw0rd!"},
    )

    assert response.status_code == 204
    assert "session" in response.cookies
    assert "httponly" in response.headers["set-cookie"].lower()


def test_login_is_case_insensitive_on_email(client, db_session):
    """A mixed-case address authenticates against the stored lowercase one."""
    create_active_user(db_session, "bob@supherman.com", "Passw0rd!", Role.EMPLOYEE)

    response = client.post(
        "/api/auth/login",
        json={"email": "BOB@SupHerman.com", "password": "Passw0rd!"},
    )
    assert response.status_code == 204


def test_login_rejects_a_wrong_password(client, db_session):
    """An incorrect password returns 401."""
    create_active_user(db_session, "carol@supherman.com", "Passw0rd!", Role.EMPLOYEE)

    response = client.post(
        "/api/auth/login",
        json={"email": "carol@supherman.com", "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_unknown_email_and_wrong_password_are_indistinguishable(client, db_session):
    """Both failures return the same body, so accounts cannot be enumerated."""
    create_active_user(db_session, "dave@supherman.com", "Passw0rd!", Role.EMPLOYEE)

    wrong_password = client.post(
        "/api/auth/login",
        json={"email": "dave@supherman.com", "password": "wrong-password"},
    )
    unknown_email = client.post(
        "/api/auth/login",
        json={"email": "nobody@supherman.com", "password": "wrong-password"},
    )

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


def test_unactivated_user_cannot_log_in(client, db_session):
    """An invited account with no password hash is refused."""
    db_session.add(User(email="erin@supherman.com", role=Role.EMPLOYEE))
    db_session.flush()

    response = client.post(
        "/api/auth/login",
        json={"email": "erin@supherman.com", "password": "anything1"},
    )
    assert response.status_code == 401


def test_me_returns_the_authenticated_user(client, db_session):
    """After login, /me reports the caller's email and role."""
    create_active_user(db_session, "frank@supherman.com", "Passw0rd!", Role.MANAGER)
    client.post(
        "/api/auth/login",
        json={"email": "frank@supherman.com", "password": "Passw0rd!"},
    )

    response = client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json()["email"] == "frank@supherman.com"
    assert response.json()["role"] == "MANAGER"


def test_me_requires_authentication(client):
    """An anonymous caller receives 401 from /me."""
    assert client.get("/api/auth/me").status_code == 401


def test_logout_clears_the_session(client, db_session):
    """After logout the session cookie no longer authenticates."""
    create_active_user(db_session, "grace@supherman.com", "Passw0rd!", Role.EMPLOYEE)
    client.post(
        "/api/auth/login",
        json={"email": "grace@supherman.com", "password": "Passw0rd!"},
    )

    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/auth/me").status_code == 401
