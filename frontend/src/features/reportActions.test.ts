import { describe, expect, it } from "vitest";

import type { CurrentUser, ReportDetail, ReportStatus, Role } from "../types/api";
import { listAvailableActions } from "./reportActions";

function buildViewer(role: Role, id = 1): CurrentUser {
  return { id, email: `${role.toLowerCase()}@supherman.com`, role };
}

function buildReport(
  status: ReportStatus,
  ownerEmail = "worker@supherman.com",
): ReportDetail {
  return {
    id: 10,
    title: "Train",
    status,
    submitted_at: "2026-09-12T08:30:00+00:00",
    owner_email: ownerEmail,
    comment: null,
    attachments: [],
  };
}

describe("listAvailableActions", () => {
  it("offers a manager both decisions on a created report", () => {
    const actions = listAvailableActions(
      buildReport("CREATED"),
      buildViewer("MANAGER"),
    );

    expect(actions.map((action) => action.targetStatus)).toEqual([
      "VALIDATED",
      "REFUSED",
    ]);
  });

  it("offers a manager nothing on a validated report", () => {
    expect(
      listAvailableActions(buildReport("VALIDATED"), buildViewer("MANAGER")),
    ).toEqual([]);
  });

  it("offers accounting only the processing action on a validated report", () => {
    const actions = listAvailableActions(
      buildReport("VALIDATED"),
      buildViewer("ACCOUNTING"),
    );

    expect(actions.map((action) => action.targetStatus)).toEqual(["PROCESSED"]);
  });

  it("offers accounting nothing on a created report", () => {
    expect(
      listAvailableActions(buildReport("CREATED"), buildViewer("ACCOUNTING")),
    ).toEqual([]);
  });

  it("offers an employee nothing at all", () => {
    expect(
      listAvailableActions(buildReport("CREATED"), buildViewer("EMPLOYEE")),
    ).toEqual([]);
  });

  it("offers nothing on a report the viewer owns", () => {
    const manager = buildViewer("MANAGER");
    const ownReport = buildReport("CREATED", manager.email);

    expect(listAvailableActions(ownReport, manager)).toEqual([]);
  });

  it("offers nothing on the two terminal statuses", () => {
    expect(
      listAvailableActions(buildReport("REFUSED"), buildViewer("MANAGER")),
    ).toEqual([]);
    expect(
      listAvailableActions(buildReport("PROCESSED"), buildViewer("ACCOUNTING")),
    ).toEqual([]);
  });
});
