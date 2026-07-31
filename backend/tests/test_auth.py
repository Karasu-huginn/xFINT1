from app.core.config import settings
from app.core.enums import Role
from app.core.security import hash_password
from app.users.models import User


def create_active_user(db_session, email: str, password: str, role: Role) -> User:
    """Persist a user who has already chosen a password."""
    user = User(email=email, password_hash=hash_password(password), role=role)
    db_session.add(user)
    db_session.flush()
    return user


def extract_cookie_attributes(set_cookie_header: str) -> list[str]:
    """Return the lowercased attribute segments of a Set-Cookie header."""
    # Skipping segment 0 drops the name=value pair, so a JWT payload that happens
    # to contain a word like "secure" can never be mistaken for an attribute.
    segments = set_cookie_header.split(";")[1:]
    return [segment.strip().lower() for segment in segments]


class VerifyPasswordSpy:
    """Counts password verifications so the timing mitigation can be asserted."""

    def __init__(self) -> None:
        """Start with no recorded calls."""
        self.call_count = 0

    def __call__(self, plain_password: str, password_hash: str | None) -> bool:
        """Record the call and report a mismatch."""
        self.call_count += 1
        return False


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


def test_unknown_email_still_costs_one_password_verification(
    client, db_session, monkeypatch
):
    """An unknown address spends the same bcrypt work as a real account."""
    verification_spy = VerifyPasswordSpy()
    monkeypatch.setattr("app.auth.service.verify_password", verification_spy)

    response = client.post(
        "/api/auth/login",
        json={"email": "nobody@supherman.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert verification_spy.call_count == 1


def test_unactivated_user_still_costs_one_password_verification(
    client, db_session, monkeypatch
):
    """An invited account spends the same bcrypt work as an activated one."""
    db_session.add(User(email="heidi@supherman.com", role=Role.EMPLOYEE))
    db_session.flush()
    verification_spy = VerifyPasswordSpy()
    monkeypatch.setattr("app.auth.service.verify_password", verification_spy)

    response = client.post(
        "/api/auth/login",
        json={"email": "heidi@supherman.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert verification_spy.call_count == 1


def test_wrong_password_costs_one_password_verification(
    client, db_session, monkeypatch
):
    """The real-account path is the baseline the failure paths must match."""
    create_active_user(db_session, "ivan@supherman.com", "Passw0rd!", Role.EMPLOYEE)
    verification_spy = VerifyPasswordSpy()
    monkeypatch.setattr("app.auth.service.verify_password", verification_spy)

    response = client.post(
        "/api/auth/login",
        json={"email": "ivan@supherman.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert verification_spy.call_count == 1


def test_session_cookie_carries_the_full_security_contract(client, db_session):
    """The cookie is httpOnly, SameSite=Lax, root-scoped and token-lifetime bound."""
    create_active_user(db_session, "judy@supherman.com", "Passw0rd!", Role.EMPLOYEE)

    response = client.post(
        "/api/auth/login",
        json={"email": "judy@supherman.com", "password": "Passw0rd!"},
    )

    attributes = extract_cookie_attributes(response.headers["set-cookie"])
    assert "httponly" in attributes
    assert "samesite=lax" in attributes
    assert "path=/" in attributes
    # The cookie must die with the token it carries, so this tracks the setting
    # rather than a literal 28800.
    expected_max_age = settings.access_token_expire_hours * 3600
    assert f"max-age={expected_max_age}" in attributes


def test_session_cookie_secure_flag_follows_the_setting(
    client, db_session, monkeypatch
):
    """The Secure attribute appears and disappears with settings.is_cookie_secure."""
    create_active_user(db_session, "mallory@supherman.com", "Passw0rd!", Role.EMPLOYEE)
    credentials = {"email": "mallory@supherman.com", "password": "Passw0rd!"}

    monkeypatch.setattr(settings, "is_cookie_secure", True)
    secure_response = client.post("/api/auth/login", json=credentials)
    assert "secure" in extract_cookie_attributes(secure_response.headers["set-cookie"])

    monkeypatch.setattr(settings, "is_cookie_secure", False)
    plain_response = client.post("/api/auth/login", json=credentials)
    assert "secure" not in extract_cookie_attributes(
        plain_response.headers["set-cookie"]
    )


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
    assert "password_hash" not in response.json()


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
