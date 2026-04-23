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
from app.security.jwt import verify_clerk_token, require_admin

router = APIRouter(prefix="/reports", tags=["Reports & Analytics"])

report_service = ReportService()


# ============= Report Configuration Endpoints =============


@router.post(
    "",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create report configuration",
    description="Save a report configuration for future use",
)
async def create_report(
    report_data: ReportCreate,
    session: AsyncSession = Depends(get_async_session),
    user_data: dict = Depends(verify_clerk_token),
    _admin_data: dict = Depends(require_admin)
):
    """
    Create a new report configuration.

    - **report_name**: Name for the report (required)
    - **report_type**: Type of report (SALES, INVENTORY, PRODUCT_PERFORMANCE, LOW_STOCK)
    - **parameters**: Report parameters as JSON object (optional)
    - **description**: Report description (optional)

    The configuration can be used to regenerate the report later.
    """
    user_id = user_data.get("sub")

    report = await report_service.create_report(session, user_id, report_data)

    if not report:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create report configuration",
        )

    return report


@router.get(
    "/{report_id}",
    response_model=ReportResponse,
    summary="Get report configuration",
    description="Retrieve a saved report configuration by ID",
)
async def get_report(
    report_id: int,
    session: AsyncSession = Depends(get_async_session),
    _user_data: dict = Depends(verify_clerk_token),
    _admin_data: dict = Depends(require_admin)
):
    """
    Get a report configuration by its ID.

    - **report_id**: Report configuration ID

    Returns the saved report parameters and metadata.
    """
    report = await report_service.get_report(session, report_id)

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found",
        )

    return report


@router.get(
    "",
    response_model=ReportListResponse,
    summary="Get all report configurations",
    description="List all saved report configurations",
)
async def get_all_reports(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    session: AsyncSession = Depends(get_async_session),
    _user_data: dict = Depends(verify_clerk_token),
    _admin_data: dict = Depends(require_admin)
):
    """
    Get all saved report configurations.

    - **skip**: Pagination offset (default: 0)
    - **limit**: Maximum records to return (default: 100, max: 500)

    Returns configurations ordered by creation date (most recent first).
    """
    return await report_service.get_all_reports(session, skip, limit)


@router.post(
    "/filter",
    response_model=ReportListResponse,
    summary="Filter report configurations",
    description="Filter saved reports by type, creator, or date",
)
async def filter_reports(
    filter_params: ReportFilterParams,
    session: AsyncSession = Depends(get_async_session),
    _user_data: dict = Depends(verify_clerk_token),
    _admin_data: dict = Depends(require_admin)
):
    """
    Filter report configurations based on criteria.

    - **report_type**: Filter by report type
    - **created_by**: Filter by creator user ID
    - **start_date**: Filter from this date
    - **end_date**: Filter until this date
    - **skip**: Pagination offset
    - **limit**: Maximum records to return
    """
    return await report_service.filter_reports(session, filter_params)


@router.patch(
    "/{report_id}",
    response_model=ReportResponse,
    summary="Update report configuration",
    description="Update a saved report configuration",
)
async def update_report(
    report_id: int,
    update_data: ReportUpdate,
    session: AsyncSession = Depends(get_async_session),
    _user_data: dict = Depends(verify_clerk_token),
    _admin_data: dict = Depends(require_admin)
):
    """
    Update a report configuration.

    - **report_id**: Report configuration ID
    - **report_name**: New report name (optional)
    - **parameters**: Updated parameters (optional)
    - **description**: Updated description (optional)

    Only provided fields will be updated.
    """
    report = await report_service.update_report(session, report_id, update_data)

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found",
        )

    return report


@router.delete(
    "/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete report configuration",
    description="Delete a saved report configuration",
)
async def delete_report(
    report_id: int,
    session: AsyncSession = Depends(get_async_session),
    _user_data: dict = Depends(verify_clerk_token),
    _admin_data: dict = Depends(require_admin)
):
    """
    Delete a report configuration.

    - **report_id**: Report configuration ID to delete

    Note: This only deletes the configuration, not the underlying transaction data.
    """
    success = await report_service.delete_report(session, report_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found",
        )

    return None


@router.post(
    "/{report_id}/run",
    response_model=Dict[str, Any],
    summary="Run saved report",
    description="Generate a report using a saved configuration",
)
async def run_saved_report(
    report_id: int,
    overrides: Optional[RunReportParams] = None,
    session: AsyncSession = Depends(get_async_session),
    _user_data: dict = Depends(verify_clerk_token),
    _admin_data: dict = Depends(require_admin)
):
    """
    Run a saved report configuration to generate report data.

    - **report_id**: ID of the saved report configuration
    - **overrides**: Optional parameter overrides (start_date, end_date, category, etc.)

    This endpoint bridges saved configurations with report generation.
    You can optionally override specific parameters without modifying the saved config.

    Example:
    - Save a "Monthly Sales Report" config with fixed parameters
    - Run it anytime with `POST /reports/5/run`
    - Override just the date range: `POST /reports/5/run` with body `{"start_date": "2024-02-01"}`
    """
    try:
        override_dict = overrides.model_dump(exclude_unset=True) if overrides else None
        result = await report_service.run_saved_report(
            session, report_id, override_dict
        )
        return result
    except ValueError as e:
        message = str(e)
        if "not found" in message.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error running saved report: {str(e)}",
        )


# ============= Report Generation Endpoints =============


@router.post(
    "/generate/sales",
    response_model=SalesReportData,
    summary="Generate sales report",
    description="Generate a sales report with revenue and quantity analysis",
)
async def generate_sales_report(
    params: SalesReportParams,
    session: AsyncSession = Depends(get_async_session),
    _user_data: dict = Depends(verify_clerk_token),
    _admin_data: dict = Depends(require_admin)
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
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating sales report: {str(e)}",
        )


@router.post(
    "/generate/inventory",
    response_model=InventoryReportData,
    summary="Generate inventory report",
    description="Generate current inventory status report",
)
async def generate_inventory_report(
    params: InventoryReportParams,
    session: AsyncSession = Depends(get_async_session),
    _user_data: dict = Depends(verify_clerk_token),
    _admin_data: dict = Depends(require_admin)
):
    """
    Generate an inventory report showing current stock levels.

    - **category**: Filter by product category (optional)
    - **low_stock_only**: Show only low stock products (default: false)

    Returns:
    - Overall inventory summary
    - Product-wise stock levels
    - Stock status (OK, LOW, OUT_OF_STOCK)
    - Stock value calculations
    - Low stock items list

    Data source: `products` table
    """
    try:
        return await report_service.generate_inventory_report(session, params)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating inventory report: {str(e)}",
        )


@router.post(
    "/generate/product-performance",
    response_model=ProductPerformanceData,
    summary="Generate product performance report",
    description="Generate top-selling products report",
)
async def generate_product_performance_report(
    params: ProductPerformanceParams,
    session: AsyncSession = Depends(get_async_session),
    _user_data: dict = Depends(verify_clerk_token),
    _admin_data: dict = Depends(require_admin)
):
    """
    Generate a product performance report showing best sellers.

    - **start_date**: Report start date (required)
    - **end_date**: Report end date (required)
    - **category**: Filter by product category (optional)
    - **top_n**: Number of top products to show (default: 10, max: 100)

    Returns:
    - Top N products by revenue
    - Quantity sold per product
    - Number of orders per product
    - Average order quantity
    - Category-wise performance

    Data source: `sales`, `products` tables
    """
    try:
        return await report_service.generate_product_performance_report(session, params)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating product performance report: {str(e)}",
        )


@router.post(
    "/generate/low-stock",
    response_model=LowStockReportData,
    summary="Generate low stock report",
    description="Generate report of products requiring reorder",
)
async def generate_low_stock_report(
    params: LowStockReportParams,
    session: AsyncSession = Depends(get_async_session),
    _user_data: dict = Depends(verify_clerk_token),
    _admin_data: dict = Depends(require_admin)
):
    """
    Generate a low stock report for inventory management.

    - **category**: Filter by product category (optional)
    - **threshold_percentage**: Stock level threshold % (default: 20, max: 100)

    Products are flagged if: (current_stock / reorder_level) * 100 <= threshold

    Returns:
    - Products below threshold
    - Current stock vs reorder level
    - Stock percentage
    - Recommended order quantities
    - Critical stock alerts

    Data source: `products` table
    """
    try:
        return await report_service.generate_low_stock_report(session, params)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating low stock report: {str(e)}",
        )
