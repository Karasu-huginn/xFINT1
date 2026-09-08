import type { ReportDetail, ReportStatus, ReportSummary } from "../types/api";
import { jsonBody, requestJson } from "./client";

export async function fetchMyReports(): Promise<ReportSummary[]> {
  return requestJson<ReportSummary[]>("/api/reports/mine");
}

export async function fetchAllReports(): Promise<ReportSummary[]> {
  return requestJson<ReportSummary[]>("/api/reports");
}

export async function fetchReport(reportId: number): Promise<ReportDetail> {
  return requestJson<ReportDetail>(`/api/reports/${reportId}`);
}

export async function submitReport(
  title: string,
  comment: string,
  documents: File[],
): Promise<ReportDetail> {
  const payload = new FormData();
  payload.append("title", title);
  if (comment.trim().length > 0) {
    payload.append("comment", comment);
  }
  for (const document of documents) {
    payload.append("files", document);
  }
  // No Content-Type header here on purpose: the browser has to set it itself so
  // that it can append the multipart boundary.
  return requestJson<ReportDetail>("/api/reports", {
    method: "POST",
    body: payload,
  });
}

export async function changeReportStatus(
  reportId: number,
  status: ReportStatus,
): Promise<ReportDetail> {
  return requestJson<ReportDetail>(`/api/reports/${reportId}/status`, {
    method: "PATCH",
    ...jsonBody({ status }),
  });
}

export function buildAttachmentUrl(attachmentId: number): string {
  return `/api/attachments/${attachmentId}`;
}
