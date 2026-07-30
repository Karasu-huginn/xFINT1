import secrets
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import ActivationToken
from app.core.exceptions import (
    AuthenticationError,
    NotFoundError,
    ValidationFailedError,
)
from app.core.security import (
    hash_activation_token,
    hash_password,
    is_password_acceptable,
    verify_password,
)
from app.users.models import User
from app.users.service import find_user_by_email

INVALID_CREDENTIALS_MESSAGE = "Invalid email or password"
INVALID_TOKEN_MESSAGE = "This activation link is invalid or has expired"
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


def find_usable_activation_token(session: Session, raw_token: str) -> ActivationToken:
    """Return the unconsumed, unexpired token matching the raw value."""
    # The row lock is what makes single-use hold under concurrent activation:
    # used_at is tested here and written by the caller in a separate statement, so
    # without it two requests racing on one token both read used_at as NULL and
    # both activate. A double-clicked submit button is enough to reach that.
    statement = (
        select(ActivationToken)
        .where(ActivationToken.token_hash == hash_activation_token(raw_token))
        .with_for_update()
    )
    token = session.execute(statement).scalar_one_or_none()
    # Absent, consumed and expired all answer identically: distinguishing them
    # would turn the probe endpoint into an invitation-status oracle.
    if token is None:
        raise NotFoundError(INVALID_TOKEN_MESSAGE)
    if token.used_at is not None:
        raise NotFoundError(INVALID_TOKEN_MESSAGE)
    if token.expires_at <= datetime.now(UTC):
        raise NotFoundError(INVALID_TOKEN_MESSAGE)
    return token


def activate_account(session: Session, raw_token: str, password: str) -> User:
    """Set the invited user's password and consume their activation token."""
    # Policy runs before the lookup so a rejected password leaves the invitation
    # usable: burning someone's only invite on a typo is unrecoverable for them.
    if not is_password_acceptable(password):
        raise ValidationFailedError(
            "Password must be at least 8 characters and contain a letter and a digit"
        )

    token = find_usable_activation_token(session, raw_token)
    token.user.password_hash = hash_password(password)
    token.used_at = datetime.now(UTC)
    session.flush()
    return token.user
