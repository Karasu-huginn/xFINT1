import type { ReportStatus, Role } from "../types/api";

// The API speaks English identifiers and the interface speaks French. This module
// is the only place the two meet, so a change of wording is a one-file change.
export const STATUS_LABELS: Record<ReportStatus, string> = {
  CREATED: "Créée",
  VALIDATED: "Validée",
  REFUSED: "Refusée",
  PROCESSED: "Traitée",
};

export const ROLE_LABELS: Record<Role, string> = {
  EMPLOYEE: "Employé",
  MANAGER: "Manager",
  ACCOUNTING: "Comptabilité",
};

export function formatSubmissionDate(isoInstant: string): string {
  return new Date(isoInstant).toLocaleDateString("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

export function formatFileSize(sizeBytes: number): string {
  const sizeKilobytes = sizeBytes / 1024;
  if (sizeKilobytes < 1024) {
    return `${Math.max(1, Math.round(sizeKilobytes))} Ko`;
  }
  return `${(sizeKilobytes / 1024).toFixed(1)} Mo`;
}
