from app.core.enums import Role, Status
from app.expenses.models import ExpenseReport
from tests.helpers import PDF_BYTES, build_upload_files, log_in_as


def submit_and_get_attachment_id(client) -> int:
    """Submit a one-file report for the logged-in client and return its file id."""
    response = client.post(
        "/api/reports", data={"title": "Train"}, files=build_upload_files(1)
    )
    return response.json()["attachments"][0]["id"]


def test_an_owner_downloads_their_own_attachment(client, db_session):
    """The stored bytes are returned verbatim under the recorded content type."""
    log_in_as(client, db_session, Role.EMPLOYEE)
    attachment_id = submit_and_get_attachment_id(client)

    response = client.get(f"/api/attachments/{attachment_id}")

    assert response.status_code == 200
    assert response.content == PDF_BYTES
    assert response.headers["content-type"] == "application/pdf"


def test_the_download_offers_the_original_filename(client, db_session):
    """The generated storage name never reaches the user, the uploaded one does."""
    log_in_as(client, db_session, Role.EMPLOYEE)
    attachment_id = submit_and_get_attachment_id(client)

    response = client.get(f"/api/attachments/{attachment_id}")

    assert "receipt-0.pdf" in response.headers["content-disposition"]


def test_an_employee_cannot_download_a_colleagues_attachment(client, db_session):
    """Attachment ids are sequential, so visibility is re-derived from the report."""
    log_in_as(client, db_session, Role.EMPLOYEE, "colleague@supherman.com")
    foreign_id = submit_and_get_attachment_id(client)
    log_in_as(client, db_session, Role.EMPLOYEE, "nosy@supherman.com")

    assert client.get(f"/api/attachments/{foreign_id}").status_code == 404


def test_accounting_cannot_download_from_a_created_report(client, db_session):
    """The report's visibility governs its files, not the attachment id."""
    log_in_as(client, db_session, Role.EMPLOYEE, "worker@supherman.com")
    attachment_id = submit_and_get_attachment_id(client)
    log_in_as(client, db_session, Role.ACCOUNTING)

    assert client.get(f"/api/attachments/{attachment_id}").status_code == 404


def test_accounting_downloads_from_a_validated_report(client, db_session):
    """Once validated, the same file becomes readable by accounting."""
    log_in_as(client, db_session, Role.EMPLOYEE, "worker@supherman.com")
    attachment_id = submit_and_get_attachment_id(client)
    db_session.query(ExpenseReport).update({"status": Status.VALIDATED})
    db_session.flush()
    log_in_as(client, db_session, Role.ACCOUNTING)

    assert client.get(f"/api/attachments/{attachment_id}").status_code == 200


def test_a_manager_downloads_any_attachment(client, db_session):
    """Managers see every report, so they can open every file."""
    log_in_as(client, db_session, Role.EMPLOYEE, "worker@supherman.com")
    attachment_id = submit_and_get_attachment_id(client)
    log_in_as(client, db_session, Role.MANAGER)

    assert client.get(f"/api/attachments/{attachment_id}").status_code == 200


def test_an_unknown_attachment_is_not_found(client, db_session):
    """A missing id returns the same 404 as a forbidden one."""
    log_in_as(client, db_session, Role.MANAGER)

    assert client.get("/api/attachments/999999").status_code == 404


def test_anonymous_callers_cannot_download(client, db_session):
    """No session means 401 before visibility is even considered."""
    log_in_as(client, db_session, Role.EMPLOYEE)
    attachment_id = submit_and_get_attachment_id(client)
    client.post("/api/auth/logout")

    assert client.get(f"/api/attachments/{attachment_id}").status_code == 401
