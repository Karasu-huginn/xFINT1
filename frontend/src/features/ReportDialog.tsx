import { useEffect, useState } from "react";
import type { ReactNode } from "react";

import { buildAttachmentUrl, fetchReport } from "../api/reports";
import Alert from "../components/Alert";
import Dialog from "../components/Dialog";
import StatusBar from "../components/StatusBar";
import { formatFileSize, formatSubmissionDate } from "../labels/fr";
import type { ReportDetail } from "../types/api";

interface ReportDialogProps {
  reportId: number;
  onClose: () => void;
  buildActions?: (report: ReportDetail) => ReactNode;
}

const TERM_CLASSES = "text-xs uppercase tracking-wide text-muted";

export default function ReportDialog({
  reportId,
  onClose,
  buildActions,
}: ReportDialogProps) {
  const [report, setReport] = useState<ReportDetail | null>(null);
  const [failureMessage, setFailureMessage] = useState<string | null>(null);

  useEffect(() => {
    fetchReport(reportId)
      .then(setReport)
      .catch(() => setFailureMessage("Cette note de frais est introuvable."));
  }, [reportId]);

  return (
    <Dialog
      title={report?.title ?? "Note de frais"}
      onClose={onClose}
      footer={
        report !== null && buildActions !== undefined
          ? buildActions(report)
          : undefined
      }
    >
      {failureMessage !== null && <Alert tone="error">{failureMessage}</Alert>}
      {report === null && failureMessage === null && (
        <p className="text-muted">Chargement...</p>
      )}
      {report !== null && (
        <div className="space-y-4">
          <StatusBar status={report.status} />
          <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <dt className={TERM_CLASSES}>Employé</dt>
              <dd className="text-ink">{report.owner_email}</dd>
            </div>
            <div>
              <dt className={TERM_CLASSES}>Soumise le</dt>
              <dd className="text-ink">
                {formatSubmissionDate(report.submitted_at)}
              </dd>
            </div>
          </dl>
          <div>
            <p className={TERM_CLASSES}>Commentaire</p>
            <p className="whitespace-pre-wrap text-ink">
              {report.comment ?? "Aucun commentaire."}
            </p>
          </div>
          <div>
            <p className={`mb-1 ${TERM_CLASSES}`}>Pièces justificatives</p>
            <ul className="divide-y divide-sheet-border rounded border border-sheet-border">
              {report.attachments.map((attachment) => (
                <li
                  key={attachment.id}
                  className="flex items-center justify-between gap-3 px-3 py-2"
                >
                  <a
                    href={buildAttachmentUrl(attachment.id)}
                    target="_blank"
                    rel="noreferrer"
                    className="break-all text-primary underline underline-offset-2 hover:text-primary-dark"
                  >
                    {attachment.original_filename}
                  </a>
                  <span className="whitespace-nowrap text-xs text-muted">
                    {formatFileSize(attachment.size_bytes)}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </Dialog>
  );
}
