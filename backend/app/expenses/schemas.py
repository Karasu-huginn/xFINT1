from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.core.enums import Status


class AttachmentResponse(BaseModel):
    """Metadata describing one supporting document of a report."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    original_filename: str
    content_type: str
    size_bytes: int


class ReportSummaryResponse(BaseModel):
    """Row shown in the report lists of Pages 2 and 4."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    status: Status
    submitted_at: datetime
    owner_email: str


class ReportDetailResponse(ReportSummaryResponse):
    """Full report as shown in the detail dialog."""

    comment: str | None
    attachments: list[AttachmentResponse]


class StatusChangeRequest(BaseModel):
    """Target status a manager or the accounting team is moving a report to."""

    status: Status
