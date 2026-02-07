import json
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.repository.report_repo import ReportRepository
from app.models.sale_model import Sale
from app.models.product_model import Product
from app.models.order_model import Order, OrderItem
from app.constants import ReportType
from app.schemas.report_schema import (
    ReportCreate,
    ReportUpdate,
    ReportResponse,
    ReportListResponse,
    ReportFilterParams,
    SalesReportParams,
    InventoryReportParams,
    ProductPerformanceParams,
    LowStockReportParams,
    SalesReportData,
    SalesReportItem,
    InventoryReportData,
    InventoryReportItem,
    ProductPerformanceData,
    ProductPerformanceItem,
    LowStockReportData,
    LowStockItem,
)
from app.config.logging import get_logger, create_owasp_log_context


class ReportService:
    """
    Service layer for Report business logic.
    Handles report configuration CRUD and report generation.
    """

    def __init__(self):
        self.repo = ReportRepository()
        self._logger = get_logger(__name__)

    # ============= Report Configuration CRUD =============

    async def create_report(
        self, session: AsyncSession, user_id: str, report_data: ReportCreate
    ) -> Optional[ReportResponse]:
        """
        Create a new report configuration.

        Args:
            session: Database session
            user_id: User ID
            report_data: Report configuration data

        Returns:
            ReportResponse or None if creation fails
        """
        try:
            self._logger.info(
                f"Creating report configuration: {report_data.report_name}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="create_report",
                    location="ReportService.create_report",
                ),
            )

            # Convert enum to ReportType
            report_type = ReportType[report_data.report_type.value]

            report_dict = {
                "report_name": report_data.report_name,
                "report_type": report_type,
                "parameters": report_data.parameters,
                "created_by": user_id,
                "description": report_data.description,
            }

            report = await self.repo.create(session, report_dict)

            if report:
                return await self._to_response(report)

            return None

        except Exception as e:
            self._logger.error(
                f"Service error creating report: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="create_report_error",
                    location="ReportService.create_report",
                ),
            )
            return None

    async def get_report(
        self, session: AsyncSession, report_id: int
    ) -> Optional[ReportResponse]:
        """Get report configuration by ID."""
        try:
            report = await self.repo.get_by_id(session, report_id)

            if report:
                return await self._to_response(report)

            return None

        except Exception as e:
            self._logger.error(
                f"Service error getting report: {str(e)}",
                extra=create_owasp_log_context(
                    user="system",
                    action="get_report_error",
                    location="ReportService.get_report",
                ),
            )
            return None

    async def get_all_reports(
        self, session: AsyncSession, skip: int = 0, limit: int = 100
    ) -> ReportListResponse:
        """Get all report configurations."""
        try:
            reports = await self.repo.get_all(session, skip, limit)
            total = await self.repo.count_reports(session)

            report_responses = []
            for report in reports:
                response = await self._to_response(report)
                if response:
                    report_responses.append(response)

            return ReportListResponse(
                reports=report_responses,
                total=total,
                skip=skip,
                limit=limit,
                has_more=skip + len(reports) < total,
            )

        except Exception as e:
            self._logger.error(
                f"Service error getting all reports: {str(e)}",
                extra=create_owasp_log_context(
                    user="system",
                    action="get_all_reports_error",
                    location="ReportService.get_all_reports",
                ),
            )
            return ReportListResponse(
                reports=[], total=0, skip=skip, limit=limit, has_more=False
            )

    async def filter_reports(
        self, session: AsyncSession, filter_params: ReportFilterParams
    ) -> ReportListResponse:
        """Filter report configurations."""
        try:
            filters = filter_params.model_dump(
                exclude={"skip", "limit"}, exclude_unset=True
            )

            reports = await self.repo.filter_reports(
                session, filters, filter_params.skip, filter_params.limit
            )

            total = await self.repo.count_reports(session, filters)

            report_responses = []
            for report in reports:
                response = await self._to_response(report)
                if response:
                    report_responses.append(response)

            return ReportListResponse(
                reports=report_responses,
                total=total,
                skip=filter_params.skip,
                limit=filter_params.limit,
                has_more=filter_params.skip + len(reports) < total,
            )

        except Exception as e:
            self._logger.error(
                f"Service error filtering reports: {str(e)}",
                extra=create_owasp_log_context(
                    user="system",
                    action="filter_reports_error",
                    location="ReportService.filter_reports",
                ),
            )
            return ReportListResponse(
                reports=[],
                total=0,
                skip=filter_params.skip,
                limit=filter_params.limit,
                has_more=False,
            )

    async def update_report(
        self, session: AsyncSession, report_id: int, update_data: ReportUpdate
    ) -> Optional[ReportResponse]:
        """Update report configuration."""
        try:
            update_dict = update_data.model_dump(exclude_unset=True)

            report = await self.repo.update(session, report_id, update_dict)

            if report:
                return await self._to_response(report)

            return None

        except Exception as e:
            self._logger.error(
                f"Service error updating report: {str(e)}",
                extra=create_owasp_log_context(
                    user="system",
                    action="update_report_error",
                    location="ReportService.update_report",
                ),
            )
            return None

    async def delete_report(self, session: AsyncSession, report_id: int) -> bool:
        """Delete report configuration."""
        try:
            return await self.repo.delete(session, report_id)

        except Exception as e:
            self._logger.error(
                f"Service error deleting report: {str(e)}",
                extra=create_owasp_log_context(
                    user="system",
                    action="delete_report_error",
                    location="ReportService.delete_report",
                ),
            )
            return False

    # ============= Report Generation =============

    async def generate_sales_report(
        self, session: AsyncSession, params: SalesReportParams
    ) -> SalesReportData:
        """
        Generate sales report based on parameters.

        Aggregates sales data by time period and provides breakdowns.
        """
        try:
            self._logger.info(
                f"Generating sales report: {params.start_date} to {params.end_date}",
                extra=create_owasp_log_context(
                    user="system",
                    action="generate_sales_report",
                    location="ReportService.generate_sales_report",
                ),
            )

            # Build base query
            query = select(Sale).where(
                and_(
                    Sale.sale_date >= params.start_date,
                    Sale.sale_date <= params.end_date,
                )
            )

            # Apply filters
            if params.product_id:
                query = query.where(Sale.product_id == params.product_id)

            if params.category:
                query = query.join(Product).where(Product.category == params.category)

            result = await session.execute(query)
            sales = result.scalars().all()

            # Calculate summary
            total_sales = len(sales)
            total_revenue = sum(sale.revenue for sale in sales)
            total_quantity = sum(sale.quantity for sale in sales)

            summary = {
                "total_sales": total_sales,
                "total_revenue": float(total_revenue),
                "total_quantity": total_quantity,
                "average_sale_value": (
                    float(total_revenue / total_sales) if total_sales > 0 else 0
                ),
            }

            # Group by time period
            items = await self._group_sales_by_period(sales, params.group_by)

            # Product breakdown
            product_breakdown = await self._get_product_breakdown(session, sales)

            # Category breakdown
            category_breakdown = await self._get_category_breakdown(session, sales)

            return SalesReportData(
                start_date=params.start_date,
                end_date=params.end_date,
                summary=summary,
                items=items,
                product_breakdown=product_breakdown,
                category_breakdown=category_breakdown,
            )

        except Exception as e:
            self._logger.error(
                f"Error generating sales report: {str(e)}",
                extra=create_owasp_log_context(
                    user="system",
                    action="generate_sales_report_error",
                    location="ReportService.generate_sales_report",
                ),
            )
            raise

    async def generate_inventory_report(
        self, session: AsyncSession, params: InventoryReportParams
    ) -> InventoryReportData:
        """
        Generate inventory report showing current stock levels.
        """
        try:
            self._logger.info(
                "Generating inventory report",
                extra=create_owasp_log_context(
                    user="system",
                    action="generate_inventory_report",
                    location="ReportService.generate_inventory_report",
                ),
            )

            # Build query
            query = select(Product)

            if params.category:
                query = query.where(Product.category == params.category)

            result = await session.execute(query)
            products = result.scalars().all()

            # Build inventory items
            items = []
            low_stock_items = []
            total_stock_value = Decimal("0.00")

            for product in products:
                stock_value = Decimal(str(product.price)) * product.stock_qty

                # Determine status
                if product.stock_qty == 0:
                    status = "OUT_OF_STOCK"
                elif product.stock_qty <= product.reorder_level:
                    status = "LOW"
                else:
                    status = "OK"

                item = InventoryReportItem(
                    product_id=str(product.id),
                    product_name=product.name,
                    category=product.category.value,
                    current_stock=product.stock_qty,
                    reorder_level=product.reorder_level,
                    stock_value=stock_value,
                    status=status,
                )

                items.append(item)
                total_stock_value += stock_value

                if status in ["LOW", "OUT_OF_STOCK"]:
                    low_stock_items.append(item)

            # Apply low stock filter if requested
            if params.low_stock_only:
                items = low_stock_items

            # Summary
            summary = {
                "total_products": len(products),
                "total_stock_value": float(total_stock_value),
                "low_stock_count": len(low_stock_items),
                "out_of_stock_count": len(
                    [item for item in items if item.status == "OUT_OF_STOCK"]
                ),
            }

            return InventoryReportData(
                generated_at=datetime.utcnow(),
                summary=summary,
                items=items,
                low_stock_items=low_stock_items,
            )

        except Exception as e:
            self._logger.error(
                f"Error generating inventory report: {str(e)}",
                extra=create_owasp_log_context(
                    user="system",
                    action="generate_inventory_report_error",
                    location="ReportService.generate_inventory_report",
                ),
            )
            raise

    async def generate_product_performance_report(
        self, session: AsyncSession, params: ProductPerformanceParams
    ) -> ProductPerformanceData:
        """
        Generate product performance report showing top sellers.
        """
        try:
            self._logger.info(
                f"Generating product performance report: {params.start_date} to {params.end_date}",
                extra=create_owasp_log_context(
                    user="system",
                    action="generate_product_performance_report",
                    location="ReportService.generate_product_performance_report",
                ),
            )

            # Query sales with product info
            query = (
                select(
                    Sale.product_id,
                    Product.name,
                    Product.category,
                    func.sum(Sale.quantity).label("total_quantity"),
                    func.sum(Sale.revenue).label("total_revenue"),
                    func.count(Sale.sale_id).label("number_of_orders"),
                )
                .join(Product, Sale.product_id == Product.id)
                .where(
                    and_(
                        Sale.sale_date >= params.start_date,
                        Sale.sale_date <= params.end_date,
                    )
                )
                .group_by(Sale.product_id, Product.name, Product.category)
                .order_by(desc("total_revenue"))
                .limit(params.top_n)
            )

            if params.category:
                query = query.where(Product.category == params.category)

            result = await session.execute(query)
            rows = result.all()

            # Build top products list
            top_products = []
            for row in rows:
                avg_quantity = (
                    Decimal(str(row.total_quantity)) / row.number_of_orders
                    if row.number_of_orders > 0
                    else Decimal("0")
                )

                top_products.append(
                    ProductPerformanceItem(
                        product_id=str(row.product_id),
                        product_name=row.name,
                        category=row.category.value,
                        total_quantity_sold=row.total_quantity,
                        total_revenue=Decimal(str(row.total_revenue)),
                        number_of_orders=row.number_of_orders,
                        average_order_quantity=avg_quantity,
                    )
                )

            # Category performance
            category_query = (
                select(
                    Product.category,
                    func.sum(Sale.quantity).label("total_quantity"),
                    func.sum(Sale.revenue).label("total_revenue"),
                    func.count(func.distinct(Sale.product_id)).label("unique_products"),
                )
                .join(Product, Sale.product_id == Product.id)
                .where(
                    and_(
                        Sale.sale_date >= params.start_date,
                        Sale.sale_date <= params.end_date,
                    )
                )
                .group_by(Product.category)
                .order_by(desc("total_revenue"))
            )

            category_result = await session.execute(category_query)
            category_rows = category_result.all()

            category_performance = [
                {
                    "category": row.category.value,
                    "total_quantity": row.total_quantity,
                    "total_revenue": float(row.total_revenue),
                    "unique_products": row.unique_products,
                }
                for row in category_rows
            ]

            # Summary
            total_revenue = sum(p.total_revenue for p in top_products)
            total_quantity = sum(p.total_quantity_sold for p in top_products)

            summary = {
                "total_revenue": float(total_revenue),
                "total_quantity_sold": total_quantity,
                "top_product_count": len(top_products),
                "date_range_days": (params.end_date - params.start_date).days + 1,
            }

            return ProductPerformanceData(
                start_date=params.start_date,
                end_date=params.end_date,
                summary=summary,
                top_products=top_products,
                category_performance=category_performance,
            )

        except Exception as e:
            self._logger.error(
                f"Error generating product performance report: {str(e)}",
                extra=create_owasp_log_context(
                    user="system",
                    action="generate_product_performance_report_error",
                    location="ReportService.generate_product_performance_report",
                ),
            )
            raise

    async def generate_low_stock_report(
        self, session: AsyncSession, params: LowStockReportParams
    ) -> LowStockReportData:
        """
        Generate low stock report showing products requiring reorder.
        """
        try:
            self._logger.info(
                f"Generating low stock report (threshold: {params.threshold_percentage}%)",
                extra=create_owasp_log_context(
                    user="system",
                    action="generate_low_stock_report",
                    location="ReportService.generate_low_stock_report",
                ),
            )

            # Build query
            query = select(Product)

            if params.category:
                query = query.where(Product.category == params.category)

            result = await session.execute(query)
            products = result.scalars().all()

            # Filter low stock products
            low_stock_items = []

            for product in products:
                if product.reorder_level == 0:
                    continue

                stock_percentage = (
                    Decimal(product.stock_qty) / product.reorder_level * 100
                )

                if stock_percentage <= params.threshold_percentage:
                    # Calculate recommended order quantity
                    recommended_qty = max(
                        product.reorder_level - product.stock_qty,
                        product.reorder_level,
                    )

                    low_stock_items.append(
                        LowStockItem(
                            product_id=str(product.id),
                            product_name=product.name,
                            category=product.category.value,
                            current_stock=product.stock_qty,
                            reorder_level=product.reorder_level,
                            stock_percentage=stock_percentage,
                            recommended_order_quantity=recommended_qty,
                        )
                    )

            # Sort by stock percentage (lowest first)
            low_stock_items.sort(key=lambda x: x.stock_percentage)

            # Summary
            summary = {
                "total_low_stock_products": len(low_stock_items),
                "out_of_stock_count": len(
                    [item for item in low_stock_items if item.current_stock == 0]
                ),
                "critical_count": len(
                    [item for item in low_stock_items if item.stock_percentage <= 10]
                ),
                "total_recommended_order_quantity": sum(
                    item.recommended_order_quantity for item in low_stock_items
                ),
            }

            return LowStockReportData(
                generated_at=datetime.utcnow(),
                threshold_percentage=params.threshold_percentage,
                summary=summary,
                items=low_stock_items,
            )

        except Exception as e:
            self._logger.error(
                f"Error generating low stock report: {str(e)}",
                extra=create_owasp_log_context(
                    user="system",
                    action="generate_low_stock_report_error",
                    location="ReportService.generate_low_stock_report",
                ),
            )
            raise

    # ============= Helper Methods =============

    async def _to_response(self, report) -> ReportResponse:
        """Convert Report model to ReportResponse schema."""
        # Parse JSON parameters
        parameters = None
        if report.parameters:
            try:
                parameters = json.loads(report.parameters)
            except json.JSONDecodeError:
                parameters = None

        return ReportResponse(
            report_id=report.report_id,
            report_name=report.report_name,
            report_type=report.report_type.value,
            parameters=parameters,
            created_by=report.created_by,
            created_at=report.created_at,
            updated_at=report.updated_at,
            description=report.description,
        )

    async def _group_sales_by_period(
        self, sales: List, group_by: str
    ) -> List[SalesReportItem]:
        """Group sales by time period (day, week, month)."""
        grouped = {}

        for sale in sales:
            if group_by == "day":
                period = sale.sale_date.strftime("%Y-%m-%d")
            elif group_by == "week":
                period = sale.sale_date.strftime("%Y-W%W")
            elif group_by == "month":
                period = sale.sale_date.strftime("%Y-%m")
            else:
                period = sale.sale_date.strftime("%Y-%m-%d")

            if period not in grouped:
                grouped[period] = {
                    "total_sales": 0,
                    "total_revenue": Decimal("0.00"),
                    "total_quantity": 0,
                }

            grouped[period]["total_sales"] += 1
            grouped[period]["total_revenue"] += sale.revenue
            grouped[period]["total_quantity"] += sale.quantity

        # Convert to list
        items = [
            SalesReportItem(
                period=period,
                total_sales=data["total_sales"],
                total_revenue=data["total_revenue"],
                total_quantity=data["total_quantity"],
            )
            for period, data in sorted(grouped.items())
        ]

        return items

    async def _get_product_breakdown(
        self, session: AsyncSession, sales: List
    ) -> List[Dict[str, Any]]:
        """Get product-wise sales breakdown."""
        product_sales = {}

        for sale in sales:
            product_id = str(sale.product_id)

            if product_id not in product_sales:
                product_sales[product_id] = {
                    "product_id": product_id,
                    "quantity": 0,
                    "revenue": Decimal("0.00"),
                    "sales_count": 0,
                }

            product_sales[product_id]["quantity"] += sale.quantity
            product_sales[product_id]["revenue"] += sale.revenue
            product_sales[product_id]["sales_count"] += 1

        # Get product names
        breakdown = []
        for product_id, data in product_sales.items():
            # Fetch product name
            result = await session.execute(
                select(Product.name).where(Product.id == product_id)
            )
            product_name = result.scalar_one_or_none()

            breakdown.append(
                {
                    "product_id": product_id,
                    "product_name": product_name or "Unknown",
                    "quantity_sold": data["quantity"],
                    "revenue": float(data["revenue"]),
                    "sales_count": data["sales_count"],
                }
            )

        # Sort by revenue
        breakdown.sort(key=lambda x: x["revenue"], reverse=True)

        return breakdown

    async def _get_category_breakdown(
        self, session: AsyncSession, sales: List
    ) -> List[Dict[str, Any]]:
        """Get category-wise sales breakdown."""
        category_sales = {}

        for sale in sales:
            # Fetch product category
            result = await session.execute(
                select(Product.category).where(Product.id == sale.product_id)
            )
            category = result.scalar_one_or_none()

            if category:
                category_name = category.value

                if category_name not in category_sales:
                    category_sales[category_name] = {
                        "quantity": 0,
                        "revenue": Decimal("0.00"),
                        "sales_count": 0,
                    }

                category_sales[category_name]["quantity"] += sale.quantity
                category_sales[category_name]["revenue"] += sale.revenue
                category_sales[category_name]["sales_count"] += 1

        # Convert to list
        breakdown = [
            {
                "category": category,
                "quantity_sold": data["quantity"],
                "revenue": float(data["revenue"]),
                "sales_count": data["sales_count"],
            }
            for category, data in category_sales.items()
        ]

        # Sort by revenue
        breakdown.sort(key=lambda x: x["revenue"], reverse=True)

        return breakdown
