from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import Status
from app.users.models import User


class ExpenseReport(Base):
    """Expense claim submitted by a user and moved through the approval flow."""

    __tablename__ = "expense_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(120))
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[Status] = mapped_column(
        Enum(Status, name="status_enum"), default=Status.CREATED
    )
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    # There is no draft state, so creating a report is submitting it. A separate
    # created_at would hold the same value and the two would eventually diverge.
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    decided_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Two foreign keys point at users, so each relationship has to say which one.
    owner: Mapped[User] = relationship(foreign_keys=[owner_id])
    decided_by: Mapped[User | None] = relationship(foreign_keys=[decided_by_id])
    attachments: Mapped[list["Attachment"]] = relationship(
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="Attachment.id",
    )

    @property
    def owner_email(self) -> str:
        """Return the address of the user who submitted this report."""
        return self.owner.email


class Attachment(Base):
    """Supporting document held on the uploads volume and described by this row."""

    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_id: Mapped[int] = mapped_column(
        ForeignKey("expense_reports.id", ondelete="CASCADE"), index=True
    )
    original_filename: Mapped[str] = mapped_column(String(255))
    stored_filename: Mapped[str] = mapped_column(String(255), unique=True)
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    report: Mapped[ExpenseReport] = relationship(back_populates="attachments")
