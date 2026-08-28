from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.expenses.models import ExpenseReport
from app.expenses.schemas import ReportDetailResponse
from app.expenses.service import create_report
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
