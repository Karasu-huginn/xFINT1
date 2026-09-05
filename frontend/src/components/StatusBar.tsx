import { STATUS_LABELS } from "../labels/fr";
import type { ReportStatus } from "../types/api";

// The happy path of the state machine, drawn as the pipeline Odoo puts at the top
// of every record. A refused report leaves that path, so it is shown on its own
// rather than as a stage.
const PIPELINE: ReportStatus[] = ["CREATED", "VALIDATED", "PROCESSED"];

function buildStageClasses(isCurrent: boolean, isPassed: boolean): string {
  const base = "px-3 py-1 text-xs font-medium";
  if (isCurrent) {
    return `${base} bg-primary text-white`;
  }
  if (isPassed) {
    return `${base} bg-primary-tint text-primary`;
  }
  return `${base} bg-white text-muted`;
}

export default function StatusBar({ status }: { status: ReportStatus }) {
  if (status === "REFUSED") {
    return (
      <div className="inline-flex overflow-hidden rounded border border-status-refused">
        <span className="bg-status-refused px-3 py-1 text-xs font-medium text-white">
          {STATUS_LABELS.REFUSED}
        </span>
      </div>
    );
  }

  const currentIndex = PIPELINE.indexOf(status);
  return (
    <div className="inline-flex divide-x divide-sheet-border overflow-hidden rounded border border-sheet-border">
      {PIPELINE.map((stage, index) => (
        <span
          key={stage}
          className={buildStageClasses(index === currentIndex, index < currentIndex)}
        >
          {STATUS_LABELS[stage]}
        </span>
      ))}
    </div>
  );
}
