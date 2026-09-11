import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { fetchMyReports } from "../api/reports";
import Alert from "../components/Alert";
import Button from "../components/Button";
import ControlPanel from "../components/ControlPanel";
import ReportListView from "../components/ReportListView";
import ReportDialog from "../features/ReportDialog";
import { describeEmptyReportList } from "../labels/fr";
import type { ReportSummary } from "../types/api";

export default function MyReportsPage() {
  const navigate = useNavigate();
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [selectedReportId, setSelectedReportId] = useState<number | null>(null);
  const [failureMessage, setFailureMessage] = useState<string | null>(null);

  useEffect(() => {
    fetchMyReports()
      .then(setReports)
      .catch(() => setFailureMessage("Impossible de charger vos notes de frais."));
  }, []);

  return (
    <>
      <ControlPanel
        title="Mes notes de frais"
        count={reports.length}
        actions={
          <Button variant="primary" onClick={() => navigate("/expenses/new")}>
            Nouvelle note
          </Button>
        }
      />
      <main className="mx-auto max-w-6xl p-4">
        {failureMessage !== null && <Alert tone="error">{failureMessage}</Alert>}
        <ReportListView
          reports={reports}
          onSelect={setSelectedReportId}
          emptyMessage={describeEmptyReportList("EMPLOYEE")}
        />
      </main>
      {selectedReportId !== null && (
        <ReportDialog
          reportId={selectedReportId}
          onClose={() => setSelectedReportId(null)}
        />
      )}
    </>
  );
}
