import { useCallback, useEffect, useState } from "react";

import { ApiError } from "../api/client";
import { changeReportStatus, fetchAllReports } from "../api/reports";
import { useAuth } from "../auth/useAuth";
import Alert from "../components/Alert";
import Button from "../components/Button";
import ControlPanel from "../components/ControlPanel";
import ReportListView from "../components/ReportListView";
import ReportDialog from "../features/ReportDialog";
import { listAvailableActions } from "../features/reportActions";
import { describeApiError, describeEmptyReportList } from "../labels/fr";
import type { ReportDetail, ReportStatus, ReportSummary } from "../types/api";

export default function AllReportsPage() {
  const { currentUser } = useAuth();
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [selectedReportId, setSelectedReportId] = useState<number | null>(null);
  const [failureMessage, setFailureMessage] = useState<string | null>(null);

  const reload = useCallback(async () => {
    try {
      setReports(await fetchAllReports());
    } catch {
      setFailureMessage("Impossible de charger les notes de frais.");
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  async function decide(reportId: number, targetStatus: ReportStatus) {
    setFailureMessage(null);
    try {
      await changeReportStatus(reportId, targetStatus);
      setSelectedReportId(null);
      await reload();
    } catch (error) {
      setFailureMessage(
        error instanceof ApiError
          ? describeApiError(
              error.code,
              "La décision n'a pas pu être enregistrée.",
            )
          : "La décision n'a pas pu être enregistrée.",
      );
    }
  }

  function buildActions(report: ReportDetail) {
    if (currentUser === null) {
      return null;
    }
    return listAvailableActions(report, currentUser).map((action) => (
      <Button
        key={action.targetStatus}
        variant={action.variant}
        onClick={() => void decide(report.id, action.targetStatus)}
      >
        {action.label}
      </Button>
    ));
  }

  return (
    <>
      <ControlPanel title="Toutes les notes de frais" count={reports.length} />
      <main className="mx-auto max-w-6xl p-4">
        {failureMessage !== null && <Alert tone="error">{failureMessage}</Alert>}
        <ReportListView
          reports={reports}
          onSelect={setSelectedReportId}
          emptyMessage={describeEmptyReportList(currentUser?.role ?? "MANAGER")}
          isOwnerColumnVisible
        />
      </main>
      {selectedReportId !== null && (
        <ReportDialog
          reportId={selectedReportId}
          onClose={() => setSelectedReportId(null)}
          buildActions={buildActions}
        />
      )}
    </>
  );
}
