from sqlalchemy.orm import Session

from app.core.exceptions import ValidationFailedError
from app.expenses.models import Attachment, ExpenseReport
from app.storage.files import check_file_count, persist_upload
from app.users.models import User


def create_report(
    session: Session,
    owner: User,
    title: str,
    comment: str | None,
    uploads: list[tuple[str, bytes]],
) -> ExpenseReport:
    """Create a report owned by the caller from a validated title and file bytes."""
    stripped_title = title.strip()
    if not stripped_title:
        raise ValidationFailedError("A title is required")
    check_file_count(len(uploads))

    # Assigning the relationships rather than the foreign keys leaves owner and
    # attachments populated on the returned object. Setting owner_id would leave
    # both unloaded, and serialising owner_email would then fire a second query
    # against a session the response is about to close.
    report = ExpenseReport(title=stripped_title, comment=comment, owner=owner)
    session.add(report)

    for original_filename, content in uploads:
        stored_filename, content_type, size_bytes = persist_upload(content)
        report.attachments.append(
            Attachment(
                original_filename=original_filename,
                stored_filename=stored_filename,
                content_type=content_type,
                size_bytes=size_bytes,
            )
        )
    session.flush()
    return report
