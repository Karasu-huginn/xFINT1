"""Provision the manager account the project brief requires for grading."""

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.enums import Role
from app.core.security import hash_password, is_password_acceptable
from app.users.models import User
from app.users.service import find_user_by_email, normalise_email


def build_seed_password_hash() -> str:
    """Return the hash of the configured seed password, refusing a weak one."""
    if not is_password_acceptable(settings.seed_manager_password):
        raise ValueError("The configured seed password violates the password policy")
    return hash_password(settings.seed_manager_password)


def repair_mandatory_manager(session: Session, existing_user: User) -> User:
    """Restore the mandated role and password on an account that already exists."""
    # The mandated credentials are an auto-refusal criterion for the whole project, so
    # the seed self-heals a row left unusable by an earlier state instead of trusting
    # whatever it finds. A password that is actually set is never overwritten.
    if not existing_user.password_hash:
        existing_user.password_hash = build_seed_password_hash()
    if existing_user.role is not Role.MANAGER:
        existing_user.role = Role.MANAGER
    session.flush()
    return existing_user


def seed_mandatory_manager(session: Session) -> User:
    """Create or repair the manager account required by the brief."""
    email = normalise_email(settings.seed_manager_email)
    existing_user = find_user_by_email(session, email)
    if existing_user is not None:
        return repair_mandatory_manager(session, existing_user)

    # The account is created with its password already set, skipping the activation
    # flow every other account goes through, so the grader can log in immediately.
    manager = User(
        email=email,
        password_hash=build_seed_password_hash(),
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
