import jwt
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import SESSION_COOKIE_NAME, get_current_user, require_roles
from app.core.enums import Role
from app.core.exceptions import register_exception_handlers
from app.core.security import create_access_token
from app.users.models import User
from tests.conftest import SessionProvider


async def read_whoami(current_user: User = Depends(get_current_user)) -> dict:
    """Return the authenticated user's email."""
    return {"email": current_user.email}


async def read_managers_only(
    current_user: User = Depends(require_roles(Role.MANAGER)),
) -> dict:
    """Return the caller's role once the manager guard has passed."""
    return {"role": current_user.role.value}


@pytest.fixture
def guarded_client(db_session):
    """Return a client for a throwaway app exposing role-guarded routes."""
    application = FastAPI()
    register_exception_handlers(application)
    application.add_api_route("/whoami", read_whoami, methods=["GET"])
    application.add_api_route("/managers-only", read_managers_only, methods=["GET"])
    application.dependency_overrides[get_db] = SessionProvider(db_session)
    with TestClient(application) as test_client:
        yield test_client


def authenticate(client, db_session, role: Role) -> User:
    """Persist a user of the given role and attach their session cookie."""
    user = User(email=f"{role.value.lower()}@supherman.com", role=role)
    db_session.add(user)
    db_session.flush()
    client.cookies.set(SESSION_COOKIE_NAME, create_access_token(user.id, role))
    return user


def test_missing_cookie_is_unauthenticated(guarded_client):
    """A request with no session cookie is rejected with 401."""
    assert guarded_client.get("/whoami").status_code == 401


def test_invalid_cookie_is_unauthenticated(guarded_client):
    """A forged or corrupted token is rejected with 401."""
    guarded_client.cookies.set(SESSION_COOKIE_NAME, "not-a-real-token")
    assert guarded_client.get("/whoami").status_code == 401


def test_valid_cookie_resolves_the_current_user(guarded_client, db_session):
    """A valid token resolves to the persisted user."""
    user = authenticate(guarded_client, db_session, Role.EMPLOYEE)
    response = guarded_client.get("/whoami")
    assert response.status_code == 200
    assert response.json()["email"] == user.email


def test_require_roles_admits_the_allowed_role(guarded_client, db_session):
    """A manager reaches a manager-only route."""
    authenticate(guarded_client, db_session, Role.MANAGER)
    response = guarded_client.get("/managers-only")
    assert response.status_code == 200
    assert response.json()["role"] == "MANAGER"


def test_require_roles_rejects_other_roles(guarded_client, db_session):
    """An employee is refused a manager-only route with 403."""
    authenticate(guarded_client, db_session, Role.EMPLOYEE)
    assert guarded_client.get("/managers-only").status_code == 403


def test_malformed_token_missing_subject_claim_is_unauthenticated(guarded_client):
    """A validly-signed token lacking 'sub' claim is rejected with 401."""
    malformed_token = jwt.encode(
        {"some_other_claim": "value"}, settings.secret_key, algorithm="HS256"
    )
    guarded_client.cookies.set(SESSION_COOKIE_NAME, malformed_token)
    assert guarded_client.get("/whoami").status_code == 401


def test_malformed_token_non_numeric_subject_is_unauthenticated(guarded_client):
    """A validly-signed token with non-numeric 'sub' is rejected with 401."""
    malformed_token = jwt.encode(
        {"sub": "not-a-number"}, settings.secret_key, algorithm="HS256"
    )
    guarded_client.cookies.set(SESSION_COOKIE_NAME, malformed_token)
    assert guarded_client.get("/whoami").status_code == 401
