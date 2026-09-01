from datetime import UTC, datetime

from sqlalchemy import text

from app.core.enums import Role, Status
from app.expenses.models import Attachment, ExpenseReport
from tests.helpers import create_active_user


def build_report(db_session, owner) -> ExpenseReport:
    """Persist a minimal report owned by the given user."""
    report = ExpenseReport(title="Train Paris-Lyon", owner_id=owner.id)
    db_session.add(report)
    db_session.flush()
    return report


def test_a_new_report_starts_as_created(db_session):
    """A report inserted without an explicit status defaults to CREATED."""
    owner = create_active_user(db_session, "owner@supherman.com", Role.EMPLOYEE)

    report = build_report(db_session, owner)

    assert report.status is Status.CREATED


def test_a_new_report_has_no_decision_recorded(db_session):
    """The audit columns stay empty until somebody decides on the report."""
    owner = create_active_user(db_session, "owner@supherman.com", Role.EMPLOYEE)

    report = build_report(db_session, owner)

    assert report.decided_by_id is None
    assert report.decided_at is None


def test_owner_email_is_exposed_for_the_all_reports_view(db_session):
    """Page 4 needs the submitter's address, so the model surfaces it directly."""
    owner = create_active_user(db_session, "owner@supherman.com", Role.EMPLOYEE)

    report = build_report(db_session, owner)

    assert report.owner_email == "owner@supherman.com"


def test_submitted_at_is_stored_as_an_absolute_instant(db_session):
    """The submission timestamp survives a non-UTC session without drifting."""
    owner = create_active_user(db_session, "owner@supherman.com", Role.EMPLOYEE)
    # The timezone has to be set before the insert, not after it. Postgres converts
    # a naive value to an instant using the session timezone in force at write time,
    # so setting it afterwards leaves the defect invisible and this test vacuous.
    # SET LOCAL is rolled back with the surrounding test transaction.
    db_session.execute(text("SET LOCAL TIME ZONE 'America/New_York'"))
    report = build_report(db_session, owner)
    db_session.expire(report)

    drift_seconds = abs((datetime.now(UTC) - report.submitted_at).total_seconds())

    assert report.submitted_at.tzinfo is not None
    assert drift_seconds < 60


def test_deleting_a_report_deletes_its_attachments(db_session):
    """Attachment rows are meaningless without their report, so they cascade."""
    owner = create_active_user(db_session, "owner@supherman.com", Role.EMPLOYEE)
    report = build_report(db_session, owner)
    db_session.add(
        Attachment(
            report_id=report.id,
            original_filename="receipt.pdf",
            stored_filename="abc123.pdf",
            content_type="application/pdf",
            size_bytes=64,
        )
    )
    db_session.flush()

    db_session.delete(report)
    db_session.flush()

    assert db_session.query(Attachment).count() == 0


def test_attachments_are_returned_in_upload_order(db_session):
    """The list is ordered by id so the UI shows files as they were attached."""
    owner = create_active_user(db_session, "owner@supherman.com", Role.EMPLOYEE)
    report = build_report(db_session, owner)
    for index in range(3):
        db_session.add(
            Attachment(
                report_id=report.id,
                original_filename=f"receipt-{index}.pdf",
                stored_filename=f"stored-{index}.pdf",
                content_type="application/pdf",
                size_bytes=64,
            )
        )
    db_session.flush()
    db_session.expire(report)

    names = [attachment.original_filename for attachment in report.attachments]

    assert names == ["receipt-0.pdf", "receipt-1.pdf", "receipt-2.pdf"]
