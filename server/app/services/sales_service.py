from typing import Optional, List
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.repository.sales_repo import SalesRepository
from app.schemas.order_schema import (
    SaleResponse,
    SalesListResponse,
    SalesFilterParams,
    SalesSummaryResponse,
)
from app.config.logging import get_logger, create_owasp_log_context


class SalesService:
    """
    Service layer for Sales business logic.
    Handles sales data retrieval for analytics and reporting.
    """

    def __init__(self):
        self.repo = SalesRepository()
        self._logger = get_logger(__name__)

    async def get_sales_by_order(
        self, session: AsyncSession, order_id: int
    ) -> List[SaleResponse]:
        """
        Get all sales records for an order.

        Args:
            session: Database session
            order_id: Order ID

        Returns:
            List of SaleResponse
        """
        try:
            sales = await self.repo.get_by_order(session, order_id)

            return [await self._to_response(sale) for sale in sales]

        except Exception as e:
            self._logger.error(
                f"Service error getting sales by order: {str(e)}",
                extra=create_owasp_log_context(
                    user="system",
                    action="get_sales_by_order_error",
                    location="SalesService.get_sales_by_order",
                ),
            )
            return []

    async def get_all_sales(
        self,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
    ) -> SalesListResponse:
        """
        Get all sales records.

        Args:
            session: Database session
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            SalesListResponse with sales
        """
        try:
            sales = await self.repo.get_all(session, skip, limit)
            total = await self.repo.count_sales(session)

            sale_responses = [await self._to_response(sale) for sale in sales]

            return SalesListResponse(
                sales=sale_responses,
                total=total,
                skip=skip,
                limit=limit,
                has_more=skip + len(sales) < total,
            )

        except Exception as e:
            self._logger.error(
                f"Service error getting all sales: {str(e)}",
                extra=create_owasp_log_context(
                    user="system",
                    action="get_all_sales_error",
                    location="SalesService.get_all_sales",
                ),
            )
            return SalesListResponse(
                sales=[], total=0, skip=skip, limit=limit, has_more=False
            )

    async def filter_sales(
        self,
        session: AsyncSession,
        filter_params: SalesFilterParams,
    ) -> SalesListResponse:
        """
        Filter sales based on criteria.

        Args:
            session: Database session
            filter_params: Filter parameters

        Returns:
            SalesListResponse with filtered sales
        """
        try:
            # Convert Pydantic model to dict for repository
            filters = filter_params.model_dump(
                exclude={"skip", "limit"}, exclude_unset=True
            )

            sales = await self.repo.filter_sales(
                session, filters, filter_params.skip, filter_params.limit
            )

            total = await self.repo.count_sales(session, filters)

            sale_responses = [await self._to_response(sale) for sale in sales]

            return SalesListResponse(
                sales=sale_responses,
                total=total,
                skip=filter_params.skip,
                limit=filter_params.limit,
                has_more=filter_params.skip + len(sales) < total,
            )

        except Exception as e:
            self._logger.error(
                f"Service error filtering sales: {str(e)}",
                extra=create_owasp_log_context(
                    user="system",
                    action="filter_sales_error",
                    location="SalesService.filter_sales",
                ),
            )
            return SalesListResponse(
                sales=[],
                total=0,
                skip=filter_params.skip,
                limit=filter_params.limit,
                has_more=False,
            )

    async def get_sales_summary(
        self,
        session: AsyncSession,
        filter_params: Optional[SalesFilterParams] = None,
    ) -> SalesSummaryResponse:
        """
        Get sales summary (total sales and revenue).

        Args:
            session: Database session
            filter_params: Optional filter parameters

        Returns:
            SalesSummaryResponse with summary data
        """
        try:
            filters = None
            if filter_params:
                filters = filter_params.model_dump(
                    exclude={"skip", "limit"}, exclude_unset=True
                )

            summary = await self.repo.get_sales_summary(session, filters)

            return SalesSummaryResponse(
                total_sales=summary["total_sales"],
                total_revenue=summary["total_revenue"],
                start_date=summary.get("start_date"),
                end_date=summary.get("end_date"),
            )

        except Exception as e:
            self._logger.error(
                f"Service error getting sales summary: {str(e)}",
                extra=create_owasp_log_context(
                    user="system",
                    action="get_sales_summary_error",
                    location="SalesService.get_sales_summary",
                ),
            )
            return SalesSummaryResponse(
                total_sales=0,
                total_revenue=Decimal("0.00"),
            )

    async def _to_response(self, sale) -> SaleResponse:
        """
        Convert Sale model to SaleResponse schema.

        Args:
            sale: Sale model instance

        Returns:
            SaleResponse schema
        """
        product = sale.product

        return SaleResponse(
            sale_id=sale.sale_id,
            order_id=sale.order_id,
            product_id=str(sale.product_id),
            product_name=product.name if product else None,
            quantity=sale.quantity,
            revenue=sale.revenue,
            sale_date=sale.sale_date,
        )
