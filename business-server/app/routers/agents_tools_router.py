from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any

from app.utils.db import get_async_session
from app.services.report_service import ReportService
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
    RunReportParams,
    SalesReportData,
    InventoryReportData,
    ProductPerformanceData,
    LowStockReportData,
)

router = APIRouter(prefix="/tools", tags=["Agent Tools"])

report_service = ReportService()


@router.post(
    "/sales",
    response_model=SalesReportData,
    summary="Generate sales report",
    description="Generate a sales report with revenue and quantity analysis",
)
async def generate_sales_report(
    params: SalesReportParams,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Generate a sales report based on parameters.

    - **start_date**: Report start date (required)
    - **end_date**: Report end date (required)
    - **product_id**: Filter by specific product (optional)
    - **category**: Filter by product category (optional)
    - **group_by**: Group results by day/week/month (default: day)

    Returns:
    - Overall summary (total sales, revenue, quantity)
    - Time-based breakdown
    - Product-wise breakdown
    - Category-wise breakdown

    Data source: `sales`, `orders`, `order_items` tables
    """
    try:
        return await report_service.generate_sales_report(session, params)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating sales report: {str(e)}",
        )


@router.post(
    "/inventory",
    response_model=InventoryReportData,
    summary="Generate inventory report",
    description="Generate an inventory report with stock levels and value analysis",
)
async def generate_inventory_report(
    params: InventoryReportParams,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Generate an inventory report based on parameters.

    - **category**: Filter by product category (optional)
    - **low_stock**: Filter by low stock (optional)

    Returns:
    - Overall summary (total stock, value)
    - Product-wise breakdown

    Data source: `inventory`, `products` tables
    """
    try:
        return await report_service.generate_inventory_report(session, params)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating inventory report: {str(e)}",
        )


@router.post(
    "/product-performance",
    response_model=ProductPerformanceData,
    summary="Generate product performance report",
    description="Generate a product performance report with sales and revenue analysis",
)
async def generate_product_performance_report(
    params: ProductPerformanceParams,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Generate a product performance report based on parameters.

    - **start_date**: Report start date (required)
    - **end_date**: Report end date (required)
    - **category**: Filter by product category (optional)
    - **top_n**: Top N products to show (default: 10)

    Returns:
    - Overall summary (total sales, revenue, quantity)
    - Product-wise breakdown

    Data source: `sales`, `orders`, `order_items` tables
    """
    try:
        return await report_service.generate_product_performance_report(session, params)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating product performance report: {str(e)}",
        )
