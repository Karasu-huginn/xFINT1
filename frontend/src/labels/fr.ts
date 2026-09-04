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

// The API answers in English because its identifiers and messages are part of a
// contract, not of the interface. Every response also carries a stable `code`, and
// this map is where that code becomes the sentence a user at SUP Herman reads. A
// page that knows its own context passes a fallback rather than leaking English.
const ERROR_MESSAGES: Record<string, string> = {
  unsupported_file_type: "Seuls les fichiers PDF, JPEG et PNG sont acceptés.",
  file_too_large: "Chaque fichier doit faire 5 Mo au maximum.",
  permission_denied: "Vous n'êtes pas autorisé à effectuer cette action.",
  not_found: "Cet élément est introuvable ou ne vous est pas accessible.",
  conflict: "Un compte existe déjà pour cette adresse e-mail.",
  transition_not_allowed:
    "Cette note a déjà été décidée, l'action n'est plus possible.",
  internal_error: "Une erreur interne est survenue, merci de réessayer.",
};

export function describeApiError(code: string, fallbackMessage: string): string {
  return ERROR_MESSAGES[code] ?? fallbackMessage;
}
