import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import select, delete, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.models.report_model import Report
from app.constants import ReportType
from app.config.logging import get_logger, create_owasp_log_context


class ReportRepository:
    """
    Singleton repository for Report CRUD operations.
    Handles report configuration storage and retrieval.
    """

    _instance: Optional["ReportRepository"] = None
    _logger = None

    def __new__(cls):
        """Singleton pattern implementation"""
        if cls._instance is None:
            cls._instance = super(ReportRepository, cls).__new__(cls)
            cls._logger = get_logger(__name__)
            cls._logger.info(
                "ReportRepository singleton instance created",
                extra=create_owasp_log_context(
                    user="system",
                    action="repository_initialization",
                    location="ReportRepository.__new__",
                ),
            )
        return cls._instance

    async def create(
        self, session: AsyncSession, report_data: Dict[str, Any]
    ) -> Optional[Report]:
        """
        Create a new report configuration.

        Args:
            session: AsyncSession for database operations
            report_data: Dictionary containing report information

        Returns:
            Created Report object or None if creation fails
        """
        try:
            # Serialize parameters to JSON string
            parameters_json = None
            if report_data.get("parameters"):
                parameters_json = json.dumps(report_data["parameters"])

            report = Report(
                report_name=report_data["report_name"],
                report_type=report_data["report_type"],
                parameters=parameters_json,
                created_by=report_data["created_by"],
                description=report_data.get("description"),
            )

            session.add(report)
            await session.commit()
            await session.refresh(report)

            self._logger.info(
                f"Report created: {report.report_id} ({report.report_name})",
                extra=create_owasp_log_context(
                    user=report.created_by,
                    action="create_report_success",
                    location="ReportRepository.create",
                ),
            )

            return report

        except SQLAlchemyError as e:
            await session.rollback()
            error_msg = f"Database error creating report: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="create_report_db_error",
                    location="ReportRepository.create",
                ),
            )
            return None

    async def get_by_id(
        self, session: AsyncSession, report_id: int
    ) -> Optional[Report]:
        """
        Get report by ID.

        Args:
            session: AsyncSession for database operations
            report_id: Report ID

        Returns:
            Report object or None if not found
        """
        try:
            result = await session.execute(
                select(Report).where(Report.report_id == report_id)
            )
            report = result.scalar_one_or_none()

            if report:
                self._logger.info(
                    f"Report retrieved: {report_id}",
                    extra=create_owasp_log_context(
                        user="system",
                        action="get_report_by_id_success",
                        location="ReportRepository.get_by_id",
                    ),
                )

            return report

        except SQLAlchemyError as e:
            error_msg = f"Database error retrieving report {report_id}: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="get_report_by_id_db_error",
                    location="ReportRepository.get_by_id",
                ),
            )
            return None

    async def get_all(
        self, session: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[Report]:
        """
        Get all reports.

        Args:
            session: AsyncSession for database operations
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Report objects
        """
        try:
            query = (
                select(Report)
                .offset(skip)
                .limit(limit)
                .order_by(desc(Report.created_at))
            )

            result = await session.execute(query)
            reports = result.scalars().all()

            self._logger.info(
                f"Retrieved {len(reports)} reports",
                extra=create_owasp_log_context(
                    user="system",
                    action="get_all_reports_success",
                    location="ReportRepository.get_all",
                ),
            )

            return list(reports)

        except SQLAlchemyError as e:
            error_msg = f"Database error retrieving all reports: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="get_all_reports_db_error",
                    location="ReportRepository.get_all",
                ),
            )
            return []

    async def filter_reports(
        self,
        session: AsyncSession,
        filters: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
    ) -> List[Report]:
        """
        Filter reports based on criteria.

        Args:
            session: AsyncSession for database operations
            filters: Dictionary of filter criteria
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of filtered Report objects
        """
        try:
            query = select(Report)
            conditions = []

            # Report type filter
            if "report_type" in filters and filters["report_type"]:
                report_type = filters["report_type"]
                if isinstance(report_type, str):
                    report_type = ReportType[report_type]
                conditions.append(Report.report_type == report_type)

            # Creator filter
            if "created_by" in filters and filters["created_by"]:
                conditions.append(Report.created_by == filters["created_by"])

            # Date range filter
            if "start_date" in filters and filters["start_date"]:
                conditions.append(Report.created_at >= filters["start_date"])

            if "end_date" in filters and filters["end_date"]:
                conditions.append(Report.created_at <= filters["end_date"])

            # Apply all conditions
            if conditions:
                query = query.where(and_(*conditions))

            # Apply pagination and ordering
            query = query.offset(skip).limit(limit).order_by(desc(Report.created_at))

            result = await session.execute(query)
            reports = result.scalars().all()

            self._logger.info(
                f"Filtered reports: {len(reports)} results (filters={filters})",
                extra=create_owasp_log_context(
                    user="system",
                    action="filter_reports_success",
                    location="ReportRepository.filter_reports",
                ),
            )

            return list(reports)

        except SQLAlchemyError as e:
            error_msg = f"Database error filtering reports: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="filter_reports_db_error",
                    location="ReportRepository.filter_reports",
                ),
            )
            return []

    async def count_reports(
        self, session: AsyncSession, filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Count total reports matching filters.

        Args:
            session: AsyncSession for database operations
            filters: Optional filter criteria

        Returns:
            Total count of reports
        """
        try:
            query = select(func.count(Report.report_id))
            conditions = []

            if filters:
                if "report_type" in filters and filters["report_type"]:
                    report_type = filters["report_type"]
                    if isinstance(report_type, str):
                        report_type = ReportType[report_type]
                    conditions.append(Report.report_type == report_type)

                if "created_by" in filters and filters["created_by"]:
                    conditions.append(Report.created_by == filters["created_by"])

                if "start_date" in filters and filters["start_date"]:
                    conditions.append(Report.created_at >= filters["start_date"])

                if "end_date" in filters and filters["end_date"]:
                    conditions.append(Report.created_at <= filters["end_date"])

            if conditions:
                query = query.where(and_(*conditions))

            result = await session.execute(query)
            count = result.scalar()

            return count or 0

        except SQLAlchemyError as e:
            error_msg = f"Database error counting reports: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="count_reports_db_error",
                    location="ReportRepository.count_reports",
                ),
            )
            return 0

    async def update(
        self, session: AsyncSession, report_id: int, update_data: Dict[str, Any]
    ) -> Optional[Report]:
        """
        Update report configuration.

        Args:
            session: AsyncSession for database operations
            report_id: Report ID
            update_data: Dictionary of fields to update

        Returns:
            Updated Report or None if not found
        """
        try:
            result = await session.execute(
                select(Report).where(Report.report_id == report_id)
            )
            report = result.scalar_one_or_none()

            if not report:
                return None

            # Update fields
            if "report_name" in update_data:
                report.report_name = update_data["report_name"]

            if "parameters" in update_data:
                report.parameters = json.dumps(update_data["parameters"])

            if "description" in update_data:
                report.description = update_data["description"]

            await session.commit()
            await session.refresh(report)

            self._logger.info(
                f"Report updated: {report_id}",
                extra=create_owasp_log_context(
                    user="system",
                    action="update_report_success",
                    location="ReportRepository.update",
                ),
            )

            return report

        except SQLAlchemyError as e:
            await session.rollback()
            error_msg = f"Database error updating report: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="update_report_db_error",
                    location="ReportRepository.update",
                ),
            )
            return None

    async def delete(self, session: AsyncSession, report_id: int) -> bool:
        """
        Delete a report configuration.

        Args:
            session: AsyncSession for database operations
            report_id: Report ID to delete

        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            stmt = delete(Report).where(Report.report_id == report_id)
            result = await session.execute(stmt)
            await session.commit()

            if result.rowcount == 0:
                return False

            self._logger.info(
                f"Report deleted: {report_id}",
                extra=create_owasp_log_context(
                    user="system",
                    action="delete_report_success",
                    location="ReportRepository.delete",
                ),
            )

            return True

        except SQLAlchemyError as e:
            await session.rollback()
            error_msg = f"Database error deleting report: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="delete_report_db_error",
                    location="ReportRepository.delete",
                ),
            )
            return False
