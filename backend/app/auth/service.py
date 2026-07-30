import secrets

from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError
from app.core.security import hash_password, verify_password
from app.users.models import User
from app.users.service import find_user_by_email

INVALID_CREDENTIALS_MESSAGE = "Invalid email or password"
# Verifying against a throwaway hash on the failure paths costs the same bcrypt
# time as a real check, so response latency cannot reveal which addresses exist.
DUMMY_PASSWORD_HASH = hash_password(secrets.token_urlsafe(32))


def authenticate_user(session: Session, email: str, password: str) -> User:
    """Return the user matching the credentials, or refuse authentication."""
    user = find_user_by_email(session, email)
    if user is None or user.password_hash is None:
        verify_password(password, DUMMY_PASSWORD_HASH)
        raise AuthenticationError(INVALID_CREDENTIALS_MESSAGE)
    if not verify_password(password, user.password_hash):
        raise AuthenticationError(INVALID_CREDENTIALS_MESSAGE)
    return user
