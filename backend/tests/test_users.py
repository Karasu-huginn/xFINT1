import pytest

from app.core.enums import Role
from app.core.security import hash_password
from app.users.models import User


def log_in_as(client, db_session, role: Role) -> User:
    """Persist an active user of the given role and log the client in."""
    email = f"{role.value.lower()}@supherman.com"
    user = User(email=email, password_hash=hash_password("Passw0rd!"), role=role)
    db_session.add(user)
    db_session.flush()
    client.post("/api/auth/login", json={"email": email, "password": "Passw0rd!"})
    return user


def test_manager_creates_an_account_and_receives_a_token(client, db_session):
    """A manager provisions an account and gets the one-time activation token."""
    log_in_as(client, db_session, Role.MANAGER)

    response = client.post(
        "/api/users",
        json={"email": "newhire@supherman.com", "role": "EMPLOYEE"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "newhire@supherman.com"
    assert body["role"] == "EMPLOYEE"
    assert len(body["activation_token"]) > 20


@pytest.mark.parametrize("role", [Role.EMPLOYEE, Role.ACCOUNTING])
def test_non_managers_cannot_create_accounts(client, db_session, role):
    """Employees and accounting are refused account creation with 403."""
    log_in_as(client, db_session, role)

    response = client.post(
        "/api/users",
        json={"email": "blocked@supherman.com", "role": "EMPLOYEE"},
    )
    assert response.status_code == 403


def test_anonymous_callers_cannot_create_accounts(client):
    """An unauthenticated request is refused with 401."""
    response = client.post(
        "/api/users",
        json={"email": "anon@supherman.com", "role": "EMPLOYEE"},
    )
    assert response.status_code == 401


def test_duplicate_email_is_a_conflict(client, db_session):
    """Provisioning the same address twice returns 409."""
    log_in_as(client, db_session, Role.MANAGER)
    client.post("/api/users", json={"email": "dup@supherman.com", "role": "EMPLOYEE"})

    response = client.post(
        "/api/users",
        json={"email": "DUP@supherman.com", "role": "ACCOUNTING"},
    )
    assert response.status_code == 409


def test_invalid_role_is_rejected(client, db_session):
    """An unknown role value fails schema validation with 422."""
    log_in_as(client, db_session, Role.MANAGER)

    response = client.post(
        "/api/users",
        json={"email": "weird@supherman.com", "role": "SUPERUSER"},
    )
    assert response.status_code == 422
