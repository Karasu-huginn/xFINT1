import { describe, expect, it } from "vitest";

import type { ReportStatus, Role } from "../types/api";
import {
  ROLE_LABELS,
  STATUS_LABELS,
  describeApiError,
  formatSubmissionDate,
} from "./fr";

const EVERY_STATUS: ReportStatus[] = [
  "CREATED",
  "VALIDATED",
  "REFUSED",
  "PROCESSED",
];
const EVERY_ROLE: Role[] = ["EMPLOYEE", "MANAGER", "ACCOUNTING"];

describe("the label maps", () => {
  it("translates every status the API can return", () => {
    for (const status of EVERY_STATUS) {
      expect(STATUS_LABELS[status]).toBeTruthy();
    }
  });

  it("uses the wording of the brief for the four statuses", () => {
    expect(STATUS_LABELS.CREATED).toBe("Créée");
    expect(STATUS_LABELS.VALIDATED).toBe("Validée");
    expect(STATUS_LABELS.REFUSED).toBe("Refusée");
    expect(STATUS_LABELS.PROCESSED).toBe("Traitée");
  });

  it("translates every role the API can return", () => {
    for (const role of EVERY_ROLE) {
      expect(ROLE_LABELS[role]).toBeTruthy();
    }
  });
});

describe("formatSubmissionDate", () => {
  it("renders an ISO instant as a French day-month-year date", () => {
    expect(formatSubmissionDate("2026-09-12T08:30:00+00:00")).toMatch(
      /12\/09\/2026/,
    );
  });
});

describe("describeApiError", () => {
  it("translates the codes the API can return into French", () => {
    expect(describeApiError("unsupported_file_type", "secours")).toBe(
      "Seuls les fichiers PDF, JPEG et PNG sont acceptés.",
    );
    expect(describeApiError("file_too_large", "secours")).toBe(
      "Chaque fichier doit faire 5 Mo au maximum.",
    );
  });

  it("falls back to the page's own message for an unmapped code", () => {
    expect(describeApiError("something_new", "Message de secours.")).toBe(
      "Message de secours.",
    );
  });

  it("never returns an English API detail", () => {
    // The point of the map is that no backend sentence reaches the interface, so
    // an unknown code must yield the caller's French fallback and nothing else.
    const translated = describeApiError("unknown", "Repli en français.");

    expect(translated).not.toMatch(/[Tt]he |accepted|required/);
  });
});
