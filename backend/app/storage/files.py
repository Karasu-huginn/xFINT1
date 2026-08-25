import uuid
from pathlib import Path

from app.core.config import settings
from app.core.exceptions import (
    FileTooLargeError,
    NotFoundError,
    UnsupportedFileTypeError,
    ValidationFailedError,
)

# The declared Content-Type is client-controlled and can simply lie, so the format
# is decided from the leading bytes of the payload and from nothing else.
MAGIC_SIGNATURES: tuple[tuple[bytes, str, str], ...] = (
    (b"%PDF-", "application/pdf", ".pdf"),
    (b"\xff\xd8\xff", "image/jpeg", ".jpg"),
    (b"\x89PNG\r\n\x1a\n", "image/png", ".png"),
)


def get_maximum_size_bytes() -> int:
    """Return the configured per-file size limit in bytes."""
    return settings.max_upload_size_mb * 1024 * 1024


def get_read_limit_bytes() -> int:
    """Return how many bytes to read per upload: one past the maximum."""
    # Reading exactly one byte more than is allowed is enough to prove a payload is
    # oversized, so a caller cannot force the whole file into memory to find out.
    return get_maximum_size_bytes() + 1


def check_file_size(content: bytes) -> None:
    """Refuse a payload larger than the configured per-file maximum."""
    if len(content) > get_maximum_size_bytes():
        raise FileTooLargeError(
            f"Each file must be {settings.max_upload_size_mb} MB or smaller"
        )


def check_file_count(file_count: int) -> None:
    """Refuse a submission with no attachments or more than the maximum."""
    if file_count < 1:
        raise ValidationFailedError("At least one supporting document is required")
    if file_count > settings.max_files_per_report:
        raise ValidationFailedError(
            f"A report carries at most {settings.max_files_per_report} files"
        )


def detect_file_type(content: bytes) -> tuple[str, str]:
    """Return the content type and extension proven by the leading magic bytes."""
    for signature, content_type, extension in MAGIC_SIGNATURES:
        if content.startswith(signature):
            return content_type, extension
    raise UnsupportedFileTypeError("Only PDF, JPEG and PNG files are accepted")


def get_upload_root() -> Path:
    """Return the resolved directory every stored upload must live under."""
    return Path(settings.upload_dir).resolve()


def resolve_inside_upload_root(filename: str) -> Path | None:
    """Return the resolved path for a filename, or None when it escapes the root."""
    upload_root = get_upload_root()
    candidate_path = (upload_root / filename).resolve()
    if not candidate_path.is_relative_to(upload_root):
        return None
    return candidate_path


def persist_upload(content: bytes) -> tuple[str, str, int]:
    """Validate a payload, write it to disk and return its storage metadata."""
    check_file_size(content)
    content_type, extension = detect_file_type(content)
    # The stored name is generated, never derived from user input, so the extension
    # comes from the verified type and the stem cannot carry a path or a script name.
    stored_filename = f"{uuid.uuid4().hex}{extension}"
    stored_path = resolve_inside_upload_root(stored_filename)
    if stored_path is None:
        raise ValidationFailedError("Invalid upload destination")
    stored_path.parent.mkdir(parents=True, exist_ok=True)
    stored_path.write_bytes(content)
    return stored_filename, content_type, len(content)


def read_stored_file(stored_filename: str) -> bytes:
    """Return the bytes of a stored upload, refusing anything outside the root."""
    stored_path = resolve_inside_upload_root(stored_filename)
    if stored_path is None or not stored_path.is_file():
        raise NotFoundError("Attachment file is missing")
    return stored_path.read_bytes()
