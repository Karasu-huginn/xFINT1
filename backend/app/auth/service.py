import secrets

from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError
from app.core.security import hash_password, verify_password
from app.users.models import User
from app.users.service import find_user_by_email

INVALID_CREDENTIALS_MESSAGE = "Invalid email or password"
# A throwaway hash the failure paths can verify against, so they cost the same
# bcrypt time as a real check. Built through hash_password so it always inherits
# the current work factor and cannot drift from the hashes it has to imitate.
DUMMY_PASSWORD_HASH = hash_password(secrets.token_urlsafe(32))


def authenticate_user(session: Session, email: str, password: str) -> User:
    """Return the user matching the credentials, or refuse authentication."""
    user = find_user_by_email(session, email)
    if user is None or user.password_hash is None:
        # Result deliberately discarded: the bcrypt cost is the point, not the
        # answer. Deleting this line restores a ~200 ms enumeration oracle, so it
        # is not a no-op. test_auth.py pins it by counting verify_password calls.
        verify_password(password, DUMMY_PASSWORD_HASH)
        raise AuthenticationError(INVALID_CREDENTIALS_MESSAGE)
    if not verify_password(password, user.password_hash):
        raise AuthenticationError(INVALID_CREDENTIALS_MESSAGE)
    return user
