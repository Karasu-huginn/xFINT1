from app.core.enums import Role
from tests.helpers import build_upload_files, log_in_as


def test_an_employee_submits_a_report_with_one_receipt(client, db_session):
    """A valid multipart submission creates a CREATED report owned by the caller."""
    employee = log_in_as(client, db_session, Role.EMPLOYEE)

    response = client.post(
        "/api/reports",
        data={"title": "Train Paris-Lyon", "comment": "Client visit"},
        files=build_upload_files(1),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Train Paris-Lyon"
    assert body["comment"] == "Client visit"
    assert body["status"] == "CREATED"
    assert body["owner_email"] == employee.email
    assert len(body["attachments"]) == 1
    assert body["attachments"][0]["original_filename"] == "receipt-0.pdf"
    assert body["attachments"][0]["content_type"] == "application/pdf"


def test_a_report_can_be_submitted_without_a_comment(client, db_session):
    """The comment is optional, so omitting it is a success with a null comment."""
    log_in_as(client, db_session, Role.EMPLOYEE)

    response = client.post(
        "/api/reports", data={"title": "Taxi"}, files=build_upload_files(1)
    )

    assert response.status_code == 201
    assert response.json()["comment"] is None


def test_several_receipts_are_all_attached(client, db_session):
    """Every file in the submission becomes an attachment row."""
    log_in_as(client, db_session, Role.EMPLOYEE)

    response = client.post(
        "/api/reports", data={"title": "Conference"}, files=build_upload_files(3)
    )

    assert response.status_code == 201
    assert len(response.json()["attachments"]) == 3


def test_a_report_with_no_receipt_is_refused(client, db_session):
    """The files field is required, so a submission without one fails validation."""
    log_in_as(client, db_session, Role.EMPLOYEE)

    response = client.post("/api/reports", data={"title": "Nothing attached"})

    assert response.status_code == 422


def test_a_blank_title_is_refused(client, db_session):
    """A title of spaces only is empty once stripped and cannot be stored."""
    log_in_as(client, db_session, Role.EMPLOYEE)

    response = client.post(
        "/api/reports", data={"title": "   "}, files=build_upload_files(1)
    )

    assert response.status_code == 400


def test_a_title_over_the_length_limit_is_refused(client, db_session):
    """A title past 120 characters fails schema validation with 422."""
    log_in_as(client, db_session, Role.EMPLOYEE)

    response = client.post(
        "/api/reports", data={"title": "x" * 121}, files=build_upload_files(1)
    )

    assert response.status_code == 422


def test_a_receipt_of_a_disallowed_type_is_refused(client, db_session):
    """An executable disguised as a PDF is rejected with 415."""
    log_in_as(client, db_session, Role.EMPLOYEE)

    response = client.post(
        "/api/reports",
        data={"title": "Malware"},
        files=[("files", ("payload.pdf", b"MZ\x90\x00", "application/pdf"))],
    )

    assert response.status_code == 415


def test_too_many_receipts_are_refused(client, db_session):
    """Eleven files exceeds the configured maximum of ten."""
    log_in_as(client, db_session, Role.EMPLOYEE)

    response = client.post(
        "/api/reports", data={"title": "Too many"}, files=build_upload_files(11)
    )

    assert response.status_code == 400


def test_anonymous_callers_cannot_submit_a_report(client):
    """An unauthenticated submission is refused with 401."""
    response = client.post(
        "/api/reports", data={"title": "Anonymous"}, files=build_upload_files(1)
    )

    assert response.status_code == 401


def test_the_title_is_stored_stripped(client, db_session):
    """Leading and trailing whitespace is removed before the title is stored."""
    log_in_as(client, db_session, Role.EMPLOYEE)

    response = client.post(
        "/api/reports", data={"title": "  Hotel Nantes  "}, files=build_upload_files(1)
    )

    assert response.json()["title"] == "Hotel Nantes"


def test_a_manager_may_submit_their_own_report(client, db_session):
    """Page 3 is open to every role, managers included."""
    log_in_as(client, db_session, Role.MANAGER)

    response = client.post(
        "/api/reports", data={"title": "Manager expense"}, files=build_upload_files(1)
    )

    assert response.status_code == 201
    assert response.json()["status"] == "CREATED"
