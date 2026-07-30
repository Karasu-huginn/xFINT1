import hashlib
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.core.config import settings
from app.core.enums import Role

MINIMUM_PASSWORD_LENGTH = 8
# bcrypt silently truncates beyond 72 bytes, so longer inputs are refused outright.
MAXIMUM_PASSWORD_BYTES = 72


def hash_password(plain_password: str) -> str:
    """Return a bcrypt hash of the given plaintext password."""
    return bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, password_hash: str | None) -> bool:
    """Return True when the plaintext matches the stored bcrypt hash."""
    if not password_hash:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode(), password_hash.encode())
    except ValueError:
        return False


def is_password_acceptable(plain_password: str) -> bool:
    """Return True when the password meets the length and composition policy."""
    if len(plain_password) < MINIMUM_PASSWORD_LENGTH:
        return False
    if len(plain_password.encode()) > MAXIMUM_PASSWORD_BYTES:
        return False
    has_letter = any(character.isalpha() for character in plain_password)
    has_digit = any(character.isdigit() for character in plain_password)
    return has_letter and has_digit


def create_access_token(user_id: int, role: Role) -> str:
    """Return a signed JWT carrying the user's identity and role."""
    expires_at = datetime.now(UTC) + timedelta(hours=settings.access_token_expire_hours)
    claims = {"sub": str(user_id), "role": role.value, "exp": expires_at}
    return jwt.encode(claims, settings.secret_key, algorithm="HS256")


def decode_access_token(token: str) -> dict | None:
    """Return the token's claims, or None when it is invalid or expired."""
    try:
        return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None


def hash_activation_token(raw_token: str) -> str:
    """Return the SHA-256 digest stored in place of a raw activation token."""
    return hashlib.sha256(raw_token.encode()).hexdigest()
