import type { CurrentUser, ReportDetail, ReportStatus, Role } from "../types/api";

export interface ReportAction {
  targetStatus: ReportStatus;
  label: string;
  variant: "primary" | "secondary" | "danger";
}

interface TransitionRule extends ReportAction {
  sourceStatus: ReportStatus;
  requiredRole: Role;
}

// This mirrors ALLOWED_TRANSITIONS in the backend service. It decides which buttons
// to draw and nothing more: the server re-checks the same rules on the request, so
// a user who forces a hidden action still gets a 409 or a 403.
const TRANSITION_RULES: TransitionRule[] = [
  {
    sourceStatus: "CREATED",
    requiredRole: "MANAGER",
    targetStatus: "VALIDATED",
    label: "Valider",
    variant: "primary",
  },
  {
    sourceStatus: "CREATED",
    requiredRole: "MANAGER",
    targetStatus: "REFUSED",
    label: "Refuser",
    variant: "danger",
  },
  {
    sourceStatus: "VALIDATED",
    requiredRole: "ACCOUNTING",
    targetStatus: "PROCESSED",
    label: "Marquer comme traitée",
    variant: "primary",
  },
];

export function listAvailableActions(
  report: ReportDetail,
  viewer: CurrentUser,
): ReportAction[] {
  // Separation of duties, shown rather than only enforced: nobody is offered a
  // decision on a claim they submitted themselves.
  if (report.owner_email === viewer.email) {
    return [];
  }
  return TRANSITION_RULES.filter(
    (rule) =>
      rule.sourceStatus === report.status && rule.requiredRole === viewer.role,
  ).map((rule) => ({
    targetStatus: rule.targetStatus,
    label: rule.label,
    variant: rule.variant,
  }));
}
