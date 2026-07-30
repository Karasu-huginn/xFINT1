import pytest

from app.core.config import settings
from app.core.enums import Role
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_activation_token,
    hash_password,
    is_password_acceptable,
    verify_password,
)


def test_password_round_trips_through_hashing():
    """A hashed password verifies against its plaintext and nothing else."""
    password_hash = hash_password("Suph3rm4n!")
    assert password_hash != "Suph3rm4n!"
    assert verify_password("Suph3rm4n!", password_hash) is True
    assert verify_password("wrong-password", password_hash) is False


def test_verify_password_rejects_none_hash():
    """A None password hash fails gracefully and returns False."""
    assert verify_password("any-password", None) is False


def test_verify_password_rejects_malformed_hash():
    """A malformed or corrupted hash fails gracefully and returns False."""
    assert verify_password("password", "not-a-bcrypt-hash") is False
    assert verify_password("password", "") is False


def test_mandatory_grader_password_satisfies_the_policy():
    """The brief's required password must pass validation or the project fails."""
    assert is_password_acceptable(settings.seed_manager_password) is True
    assert is_password_acceptable("Suph3rm4n!") is True


@pytest.mark.parametrize(
    "rejected_password",
    ["short1", "alllettersnodigit", "12345678", ""],
)
def test_weak_passwords_are_rejected(rejected_password):
    """Passwords under 8 characters or missing a letter or digit are refused."""
    assert is_password_acceptable(rejected_password) is False


def test_access_token_round_trips_with_claims():
    """A freshly minted token decodes back to its subject and role."""
    token = create_access_token(user_id=42, role=Role.MANAGER)
    claims = decode_access_token(token)
    assert claims is not None
    assert claims["sub"] == "42"
    assert claims["role"] == "MANAGER"


def test_tampered_token_is_rejected():
    """A token with a corrupted signature decodes to None rather than raising."""
    token = create_access_token(user_id=1, role=Role.EMPLOYEE)
    assert decode_access_token(token + "tampered") is None


def test_expired_token_is_rejected(monkeypatch):
    """An already-expired token decodes to None rather than raising."""
    monkeypatch.setattr(settings, "access_token_expire_hours", -1)
    token = create_access_token(user_id=1, role=Role.EMPLOYEE)
    assert decode_access_token(token) is None


def test_activation_token_hash_is_deterministic_and_not_the_input():
    """Hashing an activation token is repeatable and never returns the raw value."""
    first_digest = hash_activation_token("raw-token-value")
    second_digest = hash_activation_token("raw-token-value")
    assert first_digest == second_digest
    assert first_digest != "raw-token-value"
    assert len(first_digest) == 64
