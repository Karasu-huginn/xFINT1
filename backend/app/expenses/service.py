from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.enums import Role, Status
from app.core.exceptions import (
    NotFoundError,
    PermissionDeniedError,
    TransitionNotAllowedError,
    ValidationFailedError,
)
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


# Accounting exists to pay validated claims, so a report nobody has approved is
# none of their business. This is the whole of their read rule.
ACCOUNTING_VISIBLE_STATUSES: tuple[Status, ...] = (Status.VALIDATED, Status.PROCESSED)


def build_report_query():
    """Return a report select with owner and attachments eagerly loaded."""
    # Without these the list endpoints issue one extra query per row for the owner
    # address that every row displays.
    return select(ExpenseReport).options(
        selectinload(ExpenseReport.owner),
        selectinload(ExpenseReport.attachments),
    )


def is_report_visible_to(report: ExpenseReport, viewer: User) -> bool:
    """Report whether ownership or role lets the viewer read this report."""
    if report.owner_id == viewer.id:
        return True
    if viewer.role is Role.MANAGER:
        return True
    if viewer.role is Role.ACCOUNTING:
        return report.status in ACCOUNTING_VISIBLE_STATUSES
    return False


def list_reports_owned_by(session: Session, owner: User) -> list[ExpenseReport]:
    """Return the caller's own reports, most recently submitted first."""
    statement = (
        build_report_query()
        .where(ExpenseReport.owner_id == owner.id)
        .order_by(ExpenseReport.submitted_at.desc(), ExpenseReport.id.desc())
    )
    return list(session.execute(statement).scalars().all())


def list_reports_visible_to(session: Session, viewer: User) -> list[ExpenseReport]:
    """Return every report the viewer's role allows them to see on Page 4."""
    statement = build_report_query().order_by(
        ExpenseReport.submitted_at.desc(), ExpenseReport.id.desc()
    )
    if viewer.role is Role.ACCOUNTING:
        statement = statement.where(
            ExpenseReport.status.in_(ACCOUNTING_VISIBLE_STATUSES)
        )
    return list(session.execute(statement).scalars().all())


def get_visible_report(session: Session, viewer: User, report_id: int) -> ExpenseReport:
    """Return a report the viewer may read, or raise NotFoundError."""
    statement = build_report_query().where(ExpenseReport.id == report_id)
    report = session.execute(statement).scalar_one_or_none()
    # A 403 here would confirm the row exists, which is enough to map a colleague's
    # activity by walking ids. Invisible and absent must be indistinguishable.
    if report is None or not is_report_visible_to(report, viewer):
        raise NotFoundError("Expense report not found")
    return report


# This table is the entire state machine. Nothing else in the codebase may assign
# to ExpenseReport.status, so every rule about the lifecycle is readable here in
# four lines rather than spread across three endpoints.
ALLOWED_TRANSITIONS: dict[tuple[Status, Status], Role] = {
    (Status.CREATED, Status.VALIDATED): Role.MANAGER,
    (Status.CREATED, Status.REFUSED): Role.MANAGER,
    (Status.VALIDATED, Status.PROCESSED): Role.ACCOUNTING,
}


def apply_status_transition(
    session: Session, actor: User, report_id: int, target_status: Status
) -> ExpenseReport:
    """Move a report to the target status when the actor is entitled to do so."""
    report = get_visible_report(session, actor, report_id)

    required_role = ALLOWED_TRANSITIONS.get((report.status, target_status))
    if required_role is None:
        raise TransitionNotAllowedError(
            f"A report cannot go from {report.status.value} to {target_status.value}"
        )
    if actor.role is not required_role:
        raise PermissionDeniedError("Your role cannot make this decision")
    # Separation of duties. The brief is silent on the case, so this is a policy
    # decision: whoever submits a claim never approves it, managers included.
    if report.owner_id == actor.id:
        raise PermissionDeniedError("You cannot decide on your own expense report")

    report.status = target_status
    report.decided_by_id = actor.id
    report.decided_at = datetime.now(UTC)
    session.flush()
    return report


def get_visible_attachment(
    session: Session, viewer: User, attachment_id: int
) -> Attachment:
    """Return an attachment whose parent report the viewer may read."""
    attachment = session.get(Attachment, attachment_id)
    # Visibility is re-derived from the parent report on every request. Attachment
    # ids are sequential, so trusting the id alone would let anyone walk the volume.
    if attachment is None or not is_report_visible_to(attachment.report, viewer):
        raise NotFoundError("Attachment not found")
    return attachment
