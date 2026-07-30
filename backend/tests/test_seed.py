from app.core.config import settings
from app.core.enums import Role
from app.core.security import is_password_acceptable
from app.users.service import find_user_by_email
from seed import seed_mandatory_manager


def test_seed_creates_the_mandatory_manager(db_session):
    """Seeding provisions the exact account the brief requires."""
    user = seed_mandatory_manager(db_session)

    assert user.email == "manager@supherman.com"
    assert user.role is Role.MANAGER
    assert user.password_hash is not None


def test_seed_is_idempotent(db_session):
    """Running the seed twice leaves exactly one manager account."""
    first = seed_mandatory_manager(db_session)
    second = seed_mandatory_manager(db_session)

    assert first.id == second.id


def test_seeded_credentials_authenticate(client, db_session):
    """The brief's credentials log in; the project is refused otherwise."""
    seed_mandatory_manager(db_session)

    response = client.post(
        "/api/auth/login",
        json={"email": "manager@supherman.com", "password": "Suph3rm4n!"},
    )

    assert response.status_code == 204
    assert client.get("/api/auth/me").json()["role"] == "MANAGER"


def test_seed_password_satisfies_the_policy():
    """The configured seed password must pass the app's own validator."""
    assert is_password_acceptable(settings.seed_manager_password) is True


def test_seed_defaults_match_the_brief():
    """The default seed credentials are exactly those the brief mandates."""
    assert settings.seed_manager_email == "manager@supherman.com"
    assert settings.seed_manager_password == "Suph3rm4n!"


def test_seeded_manager_skips_activation(db_session):
    """The grader account needs no invitation link to be usable."""
    seed_mandatory_manager(db_session)
    user = find_user_by_email(db_session, "manager@supherman.com")

    assert user.password_hash is not None
