from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.core.enums import Role
from app.expenses.models import ExpenseReport
from app.expenses.schemas import ReportDetailResponse, ReportSummaryResponse
from app.expenses.service import (
    create_report,
    get_visible_report,
    list_reports_owned_by,
    list_reports_visible_to,
)
from app.storage.files import get_read_limit_bytes
from app.users.models import User

reports_router = APIRouter(prefix="/api/reports", tags=["reports"])
attachments_router = APIRouter(prefix="/api/attachments", tags=["attachments"])


async def read_uploads(uploads: list[UploadFile]) -> list[tuple[str, bytes]]:
    """Return the name and bytes of each upload, capped one byte past the limit."""
    # Reading no further than the limit plus one keeps an oversized upload from
    # being buffered whole just to discover that it is oversized.
    read_limit = get_read_limit_bytes()
    contents: list[tuple[str, bytes]] = []
    for upload in uploads:
        contents.append((upload.filename or "document", await upload.read(read_limit)))
    return contents


@reports_router.post(
    "", response_model=ReportDetailResponse, status_code=status.HTTP_201_CREATED
)
async def submit_report(
    title: Annotated[str, Form(max_length=120)],
    files: Annotated[list[UploadFile], File()],
    comment: Annotated[str | None, Form(max_length=2000)] = None,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExpenseReport:
    """Create an expense report owned by the caller from a multipart submission."""
    uploads = await read_uploads(files)
    report = create_report(session, current_user, title, comment, uploads)
    session.commit()
    return report


# /mine must stay above /{report_id}. FastAPI matches routes in registration order,
# so the reverse order makes this path try to parse "mine" as an integer id.
@reports_router.get("/mine", response_model=list[ReportSummaryResponse])
def list_my_reports(
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ExpenseReport]:
    """Return the reports submitted by the caller."""
    return list_reports_owned_by(session, current_user)


@reports_router.get("", response_model=list[ReportSummaryResponse])
def list_all_reports(
    session: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.MANAGER, Role.ACCOUNTING)),
) -> list[ExpenseReport]:
    """Return every report the caller's role allows them to see."""
    return list_reports_visible_to(session, current_user)


@reports_router.get("/{report_id}", response_model=ReportDetailResponse)
def read_report(
    report_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExpenseReport:
    """Return one report, provided the caller is allowed to see it."""
    return get_visible_report(session, current_user, report_id)
