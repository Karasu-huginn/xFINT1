import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import ActivationToken
from app.core.config import settings
from app.core.enums import Role
from app.core.exceptions import ConflictError
from app.core.security import hash_activation_token
from app.users.models import User


def normalise_email(email: str) -> str:
    """Return the address lowercased and stripped for storage and lookup."""
    return email.strip().lower()


def find_user_by_email(session: Session, email: str) -> User | None:
    """Return the user registered under the given address, or None."""
    statement = select(User).where(User.email == normalise_email(email))
    return session.execute(statement).scalar_one_or_none()


def create_user(session: Session, email: str, role: Role) -> tuple[User, str]:
    """Create an unactivated account and return it with its raw invite token."""
    normalised_email = normalise_email(email)
    if find_user_by_email(session, normalised_email) is not None:
        raise ConflictError("An account already exists for this email address")

    user = User(email=normalised_email, role=role)
    session.add(user)
    session.flush()

    raw_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(UTC) + timedelta(
        days=settings.activation_token_expire_days
    )
    session.add(
        ActivationToken(
            user_id=user.id,
            token_hash=hash_activation_token(raw_token),
            expires_at=expires_at,
        )
    )
    session.flush()
    return user, raw_token
