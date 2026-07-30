"""Provision the manager account the project brief requires for grading."""

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.enums import Role
from app.core.security import hash_password, is_password_acceptable
from app.users.models import User
from app.users.service import find_user_by_email, normalise_email


def seed_mandatory_manager(session: Session) -> User:
    """Create or return the manager account required by the brief."""
    email = normalise_email(settings.seed_manager_email)
    existing_user = find_user_by_email(session, email)
    if existing_user is not None:
        return existing_user

    # The brief refuses the project outright if these credentials fail, so the
    # account is created with its password already set, skipping activation.
    if not is_password_acceptable(settings.seed_manager_password):
        raise ValueError("The configured seed password violates the password policy")

    manager = User(
        email=email,
        password_hash=hash_password(settings.seed_manager_password),
        role=Role.MANAGER,
    )
    session.add(manager)
    session.flush()
    return manager


def run_seed() -> None:
    """Open a session, seed the mandatory manager and commit."""
    session = SessionLocal()
    try:
        seed_mandatory_manager(session)
        session.commit()
    finally:
        session.close()


if __name__ == "__main__":
    run_seed()
