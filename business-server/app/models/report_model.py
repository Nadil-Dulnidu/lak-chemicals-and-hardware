from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from app.utils.db import Base
from app.constants import ReportType


class Report(Base):
    """
    Report model for storing report configurations and metadata.

    Stores report parameters for regeneration and historical reference.
    Does not store actual report data - that's generated on-demand from transactional tables.
    """

    __tablename__ = "reports"

    report_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    report_name = Column(
        String(100), nullable=False, comment="User-defined report name"
    )
    report_type = Column(
        SQLEnum(ReportType),
        nullable=False,
        comment="Type of report (SALES, INVENTORY, etc.)",
    )

    parameters = Column(
        Text,
        nullable=True,
        comment="JSON string of report parameters (date range, filters, etc.)",
    )

    created_by = Column(
        String(50), nullable=False, comment="User ID who created the report"
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Report creation timestamp",
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Last update timestamp",
    )

    description = Column(
        String(500), nullable=True, comment="Optional report description"
    )

    def __repr__(self):
        return f"<Report(report_id={self.report_id}, name='{self.report_name}', type={self.report_type.value})>"
