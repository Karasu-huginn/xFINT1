import uuid
from pathlib import Path

import pytest

from app.core.config import settings
from app.core.exceptions import (
    FileTooLargeError,
    NotFoundError,
    UnsupportedFileTypeError,
    ValidationFailedError,
)
from app.storage.files import (
    check_file_count,
    get_read_limit_bytes,
    persist_upload,
    read_stored_file,
)

PDF_BYTES = b"%PDF-1.4\n" + b"0" * 64
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"0" * 64
JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"0" * 64


@pytest.fixture(autouse=True)
def upload_root(tmp_path, monkeypatch):
    """Redirect every upload in this module to a throwaway directory."""
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    return tmp_path


@pytest.mark.parametrize(
    ("content", "expected_type", "expected_suffix"),
    [
        (PDF_BYTES, "application/pdf", ".pdf"),
        (PNG_BYTES, "image/png", ".png"),
        (JPEG_BYTES, "image/jpeg", ".jpg"),
    ],
)
def test_allowed_types_are_stored_under_a_generated_name(
    content, expected_type, expected_suffix, upload_root
):
    """Each accepted format is written out under a uuid name with the right suffix."""
    stored_filename, content_type, size_bytes = persist_upload(content)

    assert content_type == expected_type
    assert stored_filename.endswith(expected_suffix)
    assert size_bytes == len(content)
    uuid.UUID(hex=Path(stored_filename).stem)
    assert (upload_root / stored_filename).read_bytes() == content


def test_declared_type_cannot_override_the_magic_bytes():
    """A file whose leading bytes match nothing on the allowlist is refused."""
    with pytest.raises(UnsupportedFileTypeError):
        persist_upload(b"MZ\x90\x00 this is a windows executable")


def test_an_empty_payload_is_refused():
    """A zero-byte upload matches no signature and is refused."""
    with pytest.raises(UnsupportedFileTypeError):
        persist_upload(b"")


def test_a_payload_over_the_limit_is_refused():
    """A file one byte past the configured maximum raises the 413 error."""
    oversized_content = PDF_BYTES + b"0" * (settings.max_upload_size_mb * 1024 * 1024)

    with pytest.raises(FileTooLargeError):
        persist_upload(oversized_content)


def test_the_size_check_runs_before_the_type_check():
    """An oversized payload of a disallowed type reports the size, not the type."""
    oversized_content = b"MZ" + b"0" * (settings.max_upload_size_mb * 1024 * 1024)

    with pytest.raises(FileTooLargeError):
        persist_upload(oversized_content)


def test_the_read_limit_is_one_byte_past_the_maximum():
    """Reading one byte extra is what lets an oversized upload be detected."""
    assert get_read_limit_bytes() == settings.max_upload_size_mb * 1024 * 1024 + 1


def test_a_report_needs_at_least_one_attachment():
    """Zero files is a business-rule failure, not an empty success."""
    with pytest.raises(ValidationFailedError):
        check_file_count(0)


def test_too_many_attachments_are_refused():
    """One file past the configured maximum is refused."""
    with pytest.raises(ValidationFailedError):
        check_file_count(settings.max_files_per_report + 1)


@pytest.mark.parametrize("file_count", [1, 2])
def test_an_acceptable_file_count_passes(file_count):
    """A count inside the allowed range raises nothing."""
    check_file_count(file_count)


def test_stored_files_are_read_back_verbatim(upload_root):
    """A persisted upload round-trips through read_stored_file unchanged."""
    stored_filename, _, _ = persist_upload(PNG_BYTES)

    assert read_stored_file(stored_filename) == PNG_BYTES


@pytest.mark.parametrize(
    "escaping_name",
    ["../../etc/passwd", "../secrets.pdf", "/etc/passwd"],
)
def test_a_name_escaping_the_upload_root_is_not_found(escaping_name):
    """Traversal attempts resolve outside the root and are refused as missing."""
    with pytest.raises(NotFoundError):
        read_stored_file(escaping_name)


def test_a_name_inside_the_root_that_does_not_exist_is_not_found():
    """A well-formed but absent filename is refused rather than raising OSError."""
    with pytest.raises(NotFoundError):
        read_stored_file("deadbeef.pdf")
