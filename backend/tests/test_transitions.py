import itertools

import pytest

from app.core.enums import Role, Status
from app.core.exceptions import (
    NotFoundError,
    PermissionDeniedError,
    TransitionNotAllowedError,
)
from app.expenses.models import ExpenseReport
from app.expenses.service import (
    ALLOWED_TRANSITIONS,
    apply_status_transition,
    is_report_visible_to,
)
from tests.helpers import build_upload_files, create_active_user, log_in_as


def build_report(db_session, owner, status: Status) -> ExpenseReport:
    """Persist a report owned by the given user in the given status."""
    report = ExpenseReport(title="Train Paris-Lyon", owner_id=owner.id, status=status)
    db_session.add(report)
    db_session.flush()
    return report


@pytest.mark.parametrize(
    ("source_status", "target_status"),
    list(itertools.product(Status, Status)),
)
def test_the_transition_table_is_exhaustive_for_a_manager(
    db_session, source_status, target_status
):
    """All 16 pairs, judged by a manager who can see every report: 2 move, 14 do not."""
    # A manager sees every report whatever its status, so visibility never masks the
    # transition rule here. That is what makes this the exhaustive proof of the table
    # rather than a proof of the visibility filter.
    owner = create_active_user(db_session, "owner@supherman.com", Role.EMPLOYEE)
    manager = create_active_user(db_session, "boss@supherman.com", Role.MANAGER)
    report = build_report(db_session, owner, source_status)
    required_role = ALLOWED_TRANSITIONS.get((source_status, target_status))

    if required_role is None:
        with pytest.raises(TransitionNotAllowedError):
            apply_status_transition(db_session, manager, report.id, target_status)
        return

    if required_role is not Role.MANAGER:
        with pytest.raises(PermissionDeniedError):
            apply_status_transition(db_session, manager, report.id, target_status)
        return

    updated = apply_status_transition(db_session, manager, report.id, target_status)
    assert updated.status is target_status


@pytest.mark.parametrize(
    ("source_status", "target_status", "actor_role"),
    list(itertools.product(Status, Status, Role)),
)
def test_every_combination_of_status_and_role_is_accounted_for(
    db_session, source_status, target_status, actor_role
):
    """All 48 combinations resolve through the documented ladder and nowhere else."""
    owner = create_active_user(db_session, "owner@supherman.com", Role.EMPLOYEE)
    actor = create_active_user(db_session, "actor@supherman.com", actor_role)
    report = build_report(db_session, owner, source_status)

    # The order below is the order the service checks in, and the point of the test
    # is that no combination escapes it. An actor who cannot see the report is
    # refused before the transition rules are ever consulted.
    if not is_report_visible_to(report, actor):
        with pytest.raises(NotFoundError):
            apply_status_transition(db_session, actor, report.id, target_status)
        return

    required_role = ALLOWED_TRANSITIONS.get((source_status, target_status))
    if required_role is None:
        with pytest.raises(TransitionNotAllowedError):
            apply_status_transition(db_session, actor, report.id, target_status)
        return

    if required_role is not actor_role:
        with pytest.raises(PermissionDeniedError):
            apply_status_transition(db_session, actor, report.id, target_status)
        return

    updated = apply_status_transition(db_session, actor, report.id, target_status)
    assert updated.status is target_status


def test_the_outcome_distribution_across_the_matrix_is_fixed(db_session):
    """Counting the 48 outcomes pins the behaviour without deriving it from the code."""
    owner = create_active_user(db_session, "owner@supherman.com", Role.EMPLOYEE)
    outcomes: dict[str, int] = {
        "moved": 0,
        "not_found": 0,
        "wrong_role": 0,
        "impossible": 0,
    }
    actors = {
        role: create_active_user(db_session, f"{role.value}@supherman.com", role)
        for role in Role
    }

    for source_status, target_status, actor_role in itertools.product(
        Status, Status, Role
    ):
        report = build_report(db_session, owner, source_status)
        try:
            apply_status_transition(
                db_session, actors[actor_role], report.id, target_status
            )
            outcomes["moved"] += 1
        except NotFoundError:
            outcomes["not_found"] += 1
        except PermissionDeniedError:
            outcomes["wrong_role"] += 1
        except TransitionNotAllowedError:
            outcomes["impossible"] += 1

    assert sum(outcomes.values()) == 48
    assert outcomes == {
        "moved": 3,
        "not_found": 24,
        "wrong_role": 1,
        "impossible": 20,
    }


def test_the_table_holds_exactly_the_three_documented_transitions():
    """The table is the specification, so its contents are asserted directly."""
    assert ALLOWED_TRANSITIONS == {
        (Status.CREATED, Status.VALIDATED): Role.MANAGER,
        (Status.CREATED, Status.REFUSED): Role.MANAGER,
        (Status.VALIDATED, Status.PROCESSED): Role.ACCOUNTING,
    }


@pytest.mark.parametrize(
    ("source_status", "target_status", "actor_role"),
    [
        (Status.CREATED, Status.VALIDATED, Role.MANAGER),
        (Status.CREATED, Status.REFUSED, Role.MANAGER),
        (Status.VALIDATED, Status.PROCESSED, Role.ACCOUNTING),
    ],
)
def test_nobody_decides_on_their_own_report(
    db_session, source_status, target_status, actor_role
):
    """Separation of duties: the right role is not enough if you own the row."""
    actor = create_active_user(db_session, "actor@supherman.com", actor_role)
    report = build_report(db_session, actor, source_status)

    with pytest.raises(PermissionDeniedError):
        apply_status_transition(db_session, actor, report.id, target_status)


def test_a_decision_records_who_made_it_and_when(db_session):
    """The audit columns are stamped on every accepted transition."""
    owner = create_active_user(db_session, "owner@supherman.com", Role.EMPLOYEE)
    manager = create_active_user(db_session, "boss@supherman.com", Role.MANAGER)
    report = build_report(db_session, owner, Status.CREATED)

    updated = apply_status_transition(db_session, manager, report.id, Status.VALIDATED)

    assert updated.decided_by_id == manager.id
    assert updated.decided_at is not None


def test_an_invisible_report_cannot_be_transitioned(db_session):
    """Accounting cannot act on a CREATED report they are not allowed to see."""
    owner = create_active_user(db_session, "owner@supherman.com", Role.EMPLOYEE)
    accountant = create_active_user(db_session, "money@supherman.com", Role.ACCOUNTING)
    report = build_report(db_session, owner, Status.CREATED)

    with pytest.raises(NotFoundError):
        apply_status_transition(db_session, accountant, report.id, Status.PROCESSED)


def test_a_manager_validates_a_report_over_http(client, db_session):
    """The endpoint returns the updated report to the caller."""
    log_in_as(client, db_session, Role.EMPLOYEE, "worker@supherman.com")
    report_id = client.post(
        "/api/reports", data={"title": "Train"}, files=build_upload_files(1)
    ).json()["id"]
    log_in_as(client, db_session, Role.MANAGER)

    response = client.patch(
        f"/api/reports/{report_id}/status", json={"status": "VALIDATED"}
    )

    assert response.status_code == 200
    assert response.json()["status"] == "VALIDATED"


def test_an_employee_cannot_reach_the_transition_endpoint(client, db_session):
    """The route guard refuses employees before any business rule runs."""
    log_in_as(client, db_session, Role.EMPLOYEE)
    report_id = client.post(
        "/api/reports", data={"title": "Train"}, files=build_upload_files(1)
    ).json()["id"]

    response = client.patch(
        f"/api/reports/{report_id}/status", json={"status": "VALIDATED"}
    )

    assert response.status_code == 403


def test_an_impossible_transition_is_a_conflict_over_http(client, db_session):
    """A refused report is terminal, so validating it afterwards returns 409."""
    log_in_as(client, db_session, Role.EMPLOYEE, "worker@supherman.com")
    report_id = client.post(
        "/api/reports", data={"title": "Train"}, files=build_upload_files(1)
    ).json()["id"]
    log_in_as(client, db_session, Role.MANAGER)
    client.patch(f"/api/reports/{report_id}/status", json={"status": "REFUSED"})

    response = client.patch(
        f"/api/reports/{report_id}/status", json={"status": "VALIDATED"}
    )

    assert response.status_code == 409
    assert response.json()["code"] == "transition_not_allowed"
