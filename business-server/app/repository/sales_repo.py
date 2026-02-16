import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.models.sale_model import Sale
from app.config.logging import get_logger, create_owasp_log_context


class SalesRepository:
    """
    Singleton repository for Sales CRUD operations.
    Handles sales data retrieval for analytics and reporting.
    """

    _instance: Optional["SalesRepository"] = None
    _logger = None

    def __new__(cls):
        """Singleton pattern implementation"""
        if cls._instance is None:
            cls._instance = super(SalesRepository, cls).__new__(cls)
            cls._logger = get_logger(__name__)
            cls._logger.info(
                "SalesRepository singleton instance created",
                extra=create_owasp_log_context(
                    user="system",
                    action="repository_initialization",
                    location="SalesRepository.__new__",
                ),
            )
        return cls._instance

    async def get_by_order(self, session: AsyncSession, order_id: int) -> List[Sale]:
        """
        Get all sales records for an order.

        Args:
            session: AsyncSession for database operations
            order_id: Order ID

        Returns:
            List of Sale objects
        """
        try:
            result = await session.execute(
                select(Sale).where(Sale.order_id == order_id).order_by(Sale.sale_id)
            )
            sales = result.scalars().all()

            self._logger.info(
                f"Retrieved {len(sales)} sales for order {order_id}",
                extra=create_owasp_log_context(
                    user="system",
                    action="get_sales_by_order_success",
                    location="SalesRepository.get_by_order",
                ),
            )

            return list(sales)

        except SQLAlchemyError as e:
            error_msg = f"Database error retrieving sales for order: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="get_sales_by_order_db_error",
                    location="SalesRepository.get_by_order",
                ),
            )
            return []

    async def get_all(
        self, session: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[Sale]:
        """
        Get all sales records.

        Args:
            session: AsyncSession for database operations
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Sale objects
        """
        try:
            query = (
                select(Sale).offset(skip).limit(limit).order_by(desc(Sale.sale_date))
            )

            result = await session.execute(query)
            sales = result.scalars().all()

            self._logger.info(
                f"Retrieved {len(sales)} sales records",
                extra=create_owasp_log_context(
                    user="system",
                    action="get_all_sales_success",
                    location="SalesRepository.get_all",
                ),
            )

            return list(sales)

        except SQLAlchemyError as e:
            error_msg = f"Database error retrieving all sales: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="get_all_sales_db_error",
                    location="SalesRepository.get_all",
                ),
            )
            return []

    async def filter_sales(
        self,
        session: AsyncSession,
        filters: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
    ) -> List[Sale]:
        """
        Filter sales based on criteria.

        Args:
            session: AsyncSession for database operations
            filters: Dictionary of filter criteria
                - product_id: UUID
                - start_date: datetime
                - end_date: datetime
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of filtered Sale objects
        """
        try:
            query = select(Sale)
            conditions = []

            # Product filter
            if "product_id" in filters and filters["product_id"]:
                product_id = uuid.UUID(filters["product_id"])
                conditions.append(Sale.product_id == product_id)

            # Date range filter
            if "start_date" in filters and filters["start_date"]:
                conditions.append(Sale.sale_date >= filters["start_date"])

            if "end_date" in filters and filters["end_date"]:
                conditions.append(Sale.sale_date <= filters["end_date"])

            # Apply all conditions
            if conditions:
                query = query.where(and_(*conditions))

            # Apply pagination and ordering
            query = query.offset(skip).limit(limit).order_by(desc(Sale.sale_date))

            result = await session.execute(query)
            sales = result.scalars().all()

            self._logger.info(
                f"Filtered sales: {len(sales)} results (filters={filters})",
                extra=create_owasp_log_context(
                    user="system",
                    action="filter_sales_success",
                    location="SalesRepository.filter_sales",
                ),
            )

            return list(sales)

        except SQLAlchemyError as e:
            error_msg = f"Database error filtering sales: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="filter_sales_db_error",
                    location="SalesRepository.filter_sales",
                ),
            )
            return []

    async def count_sales(
        self, session: AsyncSession, filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Count total sales matching filters.

        Args:
            session: AsyncSession for database operations
            filters: Optional filter criteria

        Returns:
            Total count of sales
        """
        try:
            query = select(func.count(Sale.sale_id))
            conditions = []

            if filters:
                if "product_id" in filters and filters["product_id"]:
                    product_id = uuid.UUID(filters["product_id"])
                    conditions.append(Sale.product_id == product_id)

                if "start_date" in filters and filters["start_date"]:
                    conditions.append(Sale.sale_date >= filters["start_date"])

                if "end_date" in filters and filters["end_date"]:
                    conditions.append(Sale.sale_date <= filters["end_date"])

            if conditions:
                query = query.where(and_(*conditions))

            result = await session.execute(query)
            count = result.scalar()

            return count or 0

        except SQLAlchemyError as e:
            error_msg = f"Database error counting sales: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="count_sales_db_error",
                    location="SalesRepository.count_sales",
                ),
            )
            return 0

    async def get_sales_summary(
        self, session: AsyncSession, filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get sales summary (total sales count and revenue).

        Args:
            session: AsyncSession for database operations
            filters: Optional filter criteria

        Returns:
            Dictionary with total_sales and total_revenue
        """
        try:
            query = select(
                func.count(Sale.sale_id).label("total_sales"),
                func.sum(Sale.revenue).label("total_revenue"),
            )
            conditions = []

            if filters:
                if "product_id" in filters and filters["product_id"]:
                    product_id = uuid.UUID(filters["product_id"])
                    conditions.append(Sale.product_id == product_id)

                if "start_date" in filters and filters["start_date"]:
                    conditions.append(Sale.sale_date >= filters["start_date"])

                if "end_date" in filters and filters["end_date"]:
                    conditions.append(Sale.sale_date <= filters["end_date"])

            if conditions:
                query = query.where(and_(*conditions))

            result = await session.execute(query)
            row = result.one()

            summary = {
                "total_sales": row.total_sales or 0,
                "total_revenue": Decimal(str(row.total_revenue or 0)),
            }

            if filters:
                summary["start_date"] = filters.get("start_date")
                summary["end_date"] = filters.get("end_date")

            self._logger.info(
                f"Sales summary: {summary['total_sales']} sales, ${summary['total_revenue']} revenue",
                extra=create_owasp_log_context(
                    user="system",
                    action="get_sales_summary_success",
                    location="SalesRepository.get_sales_summary",
                ),
            )

            return summary

        except SQLAlchemyError as e:
            error_msg = f"Database error getting sales summary: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="get_sales_summary_db_error",
                    location="SalesRepository.get_sales_summary",
                ),
            )
            return {
                "total_sales": 0,
                "total_revenue": Decimal("0.00"),
            }
