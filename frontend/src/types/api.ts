export type Role = "EMPLOYEE" | "MANAGER" | "ACCOUNTING";

export type ReportStatus = "CREATED" | "VALIDATED" | "REFUSED" | "PROCESSED";

export interface CurrentUser {
  id: number;
  email: string;
  role: Role;
}

export interface InvitedUser extends CurrentUser {
  activation_token: string;
}

export interface Attachment {
  id: number;
  original_filename: string;
  content_type: string;
  size_bytes: number;
}

export interface ReportSummary {
  id: number;
  title: string;
  status: ReportStatus;
  submitted_at: string;
  owner_email: string;
}

export interface ReportDetail extends ReportSummary {
  comment: string | null;
  attachments: Attachment[];
}
