import { STATUS_LABELS, formatSubmissionDate } from "../labels/fr";
import type { ReportSummary } from "../types/api";
import StatusBadge from "./StatusBadge";

interface ReportListViewProps {
  reports: ReportSummary[];
  onSelect: (reportId: number) => void;
  isOwnerColumnVisible?: boolean;
}

const HEADER_CLASSES =
  "px-4 py-2 text-xs font-semibold uppercase tracking-wide text-muted";

export default function ReportListView({
  reports,
  onSelect,
  isOwnerColumnVisible = false,
}: ReportListViewProps) {
  if (reports.length === 0) {
    return (
      <p className="rounded border border-dashed border-sheet-border bg-white p-8 text-center text-muted">
        Aucune note de frais à afficher.
      </p>
    );
  }

  // A table and a card list are rendered from the same data, with exactly one of
  // them shown at a time. A table that only scrolls sideways at 375 px is not
  // usable, and the brief marks responsiveness explicitly.
  return (
    <>
      <table className="hidden w-full border-collapse overflow-hidden rounded border border-sheet-border bg-sheet md:table">
        <thead>
          <tr className="border-b border-sheet-border bg-canvas text-left">
            <th className={HEADER_CLASSES}>Titre</th>
            {isOwnerColumnVisible && <th className={HEADER_CLASSES}>Employé</th>}
            <th className={HEADER_CLASSES}>Statut</th>
            <th className={HEADER_CLASSES}>Soumise le</th>
          </tr>
        </thead>
        <tbody>
          {reports.map((report) => (
            <tr
              key={report.id}
              tabIndex={0}
              onClick={() => onSelect(report.id)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  onSelect(report.id);
                }
              }}
              className="cursor-pointer border-b border-sheet-border last:border-0 hover:bg-primary-tint focus:bg-primary-tint focus:outline-none"
            >
              <td className="px-4 py-2 font-medium text-ink">{report.title}</td>
              {isOwnerColumnVisible && (
                <td className="px-4 py-2 text-muted">{report.owner_email}</td>
              )}
              <td className="px-4 py-2">
                <StatusBadge status={report.status} />
              </td>
              <td className="px-4 py-2 text-muted">
                {formatSubmissionDate(report.submitted_at)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <ul className="space-y-2 md:hidden">
        {reports.map((report) => (
          <li key={report.id}>
            <button
              type="button"
              onClick={() => onSelect(report.id)}
              aria-label={`${report.title}, ${STATUS_LABELS[report.status]}`}
              className="w-full rounded border border-sheet-border bg-sheet p-3 text-left shadow-sheet"
            >
              <div className="flex items-start justify-between gap-2">
                <span className="font-medium text-ink">{report.title}</span>
                <StatusBadge status={report.status} />
              </div>
              <p className="mt-1 text-xs text-muted">
                {formatSubmissionDate(report.submitted_at)}
                {isOwnerColumnVisible && ` - ${report.owner_email}`}
              </p>
            </button>
          </li>
        ))}
      </ul>
    </>
  );
}
