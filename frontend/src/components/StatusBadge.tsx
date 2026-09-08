import { STATUS_LABELS } from "../labels/fr";
import type { ReportStatus } from "../types/api";

const BADGE_CLASSES: Record<ReportStatus, string> = {
  CREATED: "bg-status-created-tint text-status-created",
  VALIDATED: "bg-status-validated-tint text-status-validated",
  REFUSED: "bg-status-refused-tint text-status-refused",
  PROCESSED: "bg-status-processed-tint text-status-processed",
};

export default function StatusBadge({ status }: { status: ReportStatus }) {
  return (
    <span
      className={`inline-block whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-medium ${BADGE_CLASSES[status]}`}
    >
      {STATUS_LABELS[status]}
    </span>
  );
}
