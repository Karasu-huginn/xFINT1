from app.core.enums import Role, Status
from app.expenses.models import ExpenseReport
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


def submit_report_as(client, title: str) -> int:
    """Submit a report for the logged-in client and return its id."""
    response = client.post(
        "/api/reports", data={"title": title}, files=build_upload_files(1)
    )
    return response.json()["id"]


def test_mine_lists_only_the_callers_own_reports(client, db_session):
    """An employee sees their own reports and nobody else's."""
    log_in_as(client, db_session, Role.EMPLOYEE, "colleague@supherman.com")
    submit_report_as(client, "Colleague report")
    log_in_as(client, db_session, Role.EMPLOYEE, "self@supherman.com")
    submit_report_as(client, "My report")

    response = client.get("/api/reports/mine")

    assert response.status_code == 200
    assert [row["title"] for row in response.json()] == ["My report"]


def test_mine_returns_the_newest_report_first(client, db_session):
    """The list is ordered by submission, most recent at the top."""
    log_in_as(client, db_session, Role.EMPLOYEE)
    submit_report_as(client, "Older")
    submit_report_as(client, "Newer")

    titles = [row["title"] for row in client.get("/api/reports/mine").json()]

    assert titles == ["Newer", "Older"]


def test_an_employee_cannot_list_all_reports(client, db_session):
    """Page 4 is closed to employees, so the route refuses them with 403."""
    log_in_as(client, db_session, Role.EMPLOYEE)

    assert client.get("/api/reports").status_code == 403


def test_a_manager_lists_every_report_with_the_owner_address(client, db_session):
    """Managers see all reports in every status, each carrying its submitter."""
    log_in_as(client, db_session, Role.EMPLOYEE, "worker@supherman.com")
    submit_report_as(client, "Worker report")
    log_in_as(client, db_session, Role.MANAGER)

    rows = client.get("/api/reports").json()

    assert [row["title"] for row in rows] == ["Worker report"]
    assert rows[0]["owner_email"] == "worker@supherman.com"


def test_accounting_sees_only_validated_and_processed_reports(client, db_session):
    """A CREATED report is invisible to accounting until a manager validates it."""
    log_in_as(client, db_session, Role.EMPLOYEE, "worker@supherman.com")
    created_id = submit_report_as(client, "Still pending")
    validated_id = submit_report_as(client, "Already validated")
    db_session.query(ExpenseReport).filter(ExpenseReport.id == validated_id).update(
        {"status": Status.VALIDATED}
    )
    db_session.flush()
    log_in_as(client, db_session, Role.ACCOUNTING)

    visible_ids = [row["id"] for row in client.get("/api/reports").json()]

    assert visible_ids == [validated_id]
    assert created_id not in visible_ids


def test_an_employee_cannot_read_a_colleagues_report(client, db_session):
    """Guessing a report id returns 404, so the API is not an existence oracle."""
    log_in_as(client, db_session, Role.EMPLOYEE, "colleague@supherman.com")
    foreign_id = submit_report_as(client, "Private")
    log_in_as(client, db_session, Role.EMPLOYEE, "nosy@supherman.com")

    assert client.get(f"/api/reports/{foreign_id}").status_code == 404


def test_accounting_cannot_read_a_created_report_by_id(client, db_session):
    """Invisible by role means invisible by direct fetch too, and it is a 404."""
    log_in_as(client, db_session, Role.EMPLOYEE, "worker@supherman.com")
    created_id = submit_report_as(client, "Still pending")
    log_in_as(client, db_session, Role.ACCOUNTING)

    assert client.get(f"/api/reports/{created_id}").status_code == 404


def test_a_manager_reads_any_report_in_full(client, db_session):
    """The detail response carries the comment and the attachment list."""
    log_in_as(client, db_session, Role.EMPLOYEE, "worker@supherman.com")
    response = client.post(
        "/api/reports",
        data={"title": "Detailed", "comment": "Two nights"},
        files=build_upload_files(2),
    )
    report_id = response.json()["id"]
    log_in_as(client, db_session, Role.MANAGER)

    body = client.get(f"/api/reports/{report_id}").json()

    assert body["comment"] == "Two nights"
    assert len(body["attachments"]) == 2


def test_an_owner_reads_their_own_report(client, db_session):
    """Ownership beats role, so an employee always reads their own report."""
    log_in_as(client, db_session, Role.EMPLOYEE)
    report_id = submit_report_as(client, "Mine")

    assert client.get(f"/api/reports/{report_id}").status_code == 200


def test_a_missing_report_is_not_found(client, db_session):
    """An id that never existed returns the same 404 as an invisible one."""
    log_in_as(client, db_session, Role.MANAGER)

    assert client.get("/api/reports/999999").status_code == 404
