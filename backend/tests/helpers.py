from app.core.enums import Role
from app.core.security import hash_password
from app.users.models import User

PDF_BYTES = b"%PDF-1.4\n" + b"0" * 64
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"0" * 64
DEFAULT_PASSWORD = "Passw0rd!"


def create_active_user(db_session, email: str, role: Role) -> User:
    """Persist a user who has already chosen a password."""
    user = User(email=email, password_hash=hash_password(DEFAULT_PASSWORD), role=role)
    db_session.add(user)
    db_session.flush()
    return user


def log_in_as(client, db_session, role: Role, email: str | None = None) -> User:
    """Persist an active user of the given role and log the client in as them."""
    address = email or f"{role.value.lower()}@supherman.com"
    user = create_active_user(db_session, address, role)
    client.post(
        "/api/auth/login", json={"email": address, "password": DEFAULT_PASSWORD}
    )
    return user


def build_upload_files(count: int = 1) -> list[tuple[str, tuple[str, bytes, str]]]:
    """Return a multipart files payload carrying the given number of valid PDFs."""
    uploads = []
    for index in range(count):
        uploads.append(
            ("files", (f"receipt-{index}.pdf", PDF_BYTES, "application/pdf"))
        )
    return uploads
