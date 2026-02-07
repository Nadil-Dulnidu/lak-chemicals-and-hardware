from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.db import get_async_session
from app.services.order_service import OrderService
from app.services.sales_service import SalesService
from app.schemas.order_schema import (
    OrderCreate,
    OrderFromQuotation,
    OrderUpdateStatus,
    OrderResponse,
    OrderListResponse,
    OrderFilterParams,
    SaleResponse,
    SalesListResponse,
    SalesFilterParams,
    SalesSummaryResponse,
)

router = APIRouter(prefix="/orders", tags=["Orders"])

# Initialize services
order_service = OrderService()
sales_service = SalesService()


# ============= Order Endpoints =============


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create order",
    description="Create a new order directly",
)
async def create_order(
    order_data: OrderCreate,
    session: AsyncSession = Depends(get_async_session),
    # user_id: str = Depends(get_current_user)  # Add authentication later
):
    """
    Create a new order.

    - **items**: List of items with product_id and quantity (required, at least 1 item)
    - **payment_method**: Payment method (optional)
    - **notes**: Additional notes (optional)

    The order will be created with PENDING status.
    Stock availability will be checked before order creation.
    """
    try:
        user_id = "admin"  # Replace with actual user_id from authentication

        order = await order_service.create_order(session, user_id, order_data)

        if not order:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create order",
            )

        return order

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/from-quotation",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create order from quotation",
    description="Convert an approved quotation into an order",
)
async def create_order_from_quotation(
    order_data: OrderFromQuotation,
    session: AsyncSession = Depends(get_async_session),
    # user_id: str = Depends(get_current_user)  # Add authentication later
):
    """
    Create an order from an approved quotation.

    - **quotation_id**: ID of the approved quotation (required)
    - **payment_method**: Payment method (optional)
    - **notes**: Additional notes (optional)

    Requirements:
    - Quotation must exist and belong to the user
    - Quotation status must be APPROVED
    - Stock availability will be checked
    """
    try:
        user_id = "admin"  # Replace with actual user_id from authentication

        order = await order_service.create_order_from_quotation(
            session, user_id, order_data
        )

        if not order:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create order from quotation",
            )

        return order

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get order by ID",
    description="Retrieve a specific order by its ID",
)
async def get_order(
    order_id: int,
    session: AsyncSession = Depends(get_async_session),
    # user_id: str = Depends(get_current_user)  # Add authentication later
):
    """
    Get an order by its ID.

    - **order_id**: Order ID

    Returns order details including all items, status, and payment information.
    """
    user_id = "admin"  # Replace with actual user_id from authentication

    order = await order_service.get_order(session, order_id, user_id)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found",
        )

    return order


@router.get(
    "",
    response_model=OrderListResponse,
    summary="Get user orders",
    description="Get all orders for the current user",
)
async def get_user_orders(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    session: AsyncSession = Depends(get_async_session),
    # user_id: str = Depends(get_current_user)  # Add authentication later
):
    """
    Get all orders for the current user.

    - **skip**: Pagination offset (default: 0)
    - **limit**: Maximum records to return (default: 100, max: 500)

    Returns orders ordered by order date (most recent first).
    """
    user_id = "admin"  # Replace with actual user_id from authentication

    return await order_service.get_user_orders(session, user_id, skip, limit)


@router.post(
    "/filter",
    response_model=OrderListResponse,
    summary="Filter orders",
    description="Filter orders based on various criteria",
)
async def filter_orders(
    filter_params: OrderFilterParams,
    session: AsyncSession = Depends(get_async_session),
    # user_id: str = Depends(get_current_user)  # Add authentication later
):
    """
    Filter orders based on criteria.

    - **status**: Filter by status (PENDING/COMPLETED/CANCELLED)
    - **start_date**: Filter orders from this date
    - **end_date**: Filter orders until this date
    - **skip**: Pagination offset
    - **limit**: Maximum records to return
    """
    user_id = "admin"  # Replace with actual user_id from authentication

    return await order_service.filter_orders(session, user_id, filter_params)


@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
    summary="Update order status",
    description="Update the status of an order (PENDING/COMPLETED/CANCELLED)",
)
async def update_order_status(
    order_id: int,
    status_data: OrderUpdateStatus,
    session: AsyncSession = Depends(get_async_session),
    # user_id: str = Depends(get_current_user)  # Add authentication later
):
    """
    Update order status.

    - **order_id**: Order ID
    - **status**: New status (PENDING/COMPLETED/CANCELLED)

    Status transitions:
    - PENDING → COMPLETED (processes order, updates inventory, creates sales records)
    - PENDING → CANCELLED (cancels order)
    - COMPLETED and CANCELLED orders cannot be changed

    When order is marked COMPLETED:
    - Inventory stock is reduced
    - Stock movement records are created
    - Sales records are generated for analytics
    """
    try:
        user_id = "admin"  # Replace with actual user_id from authentication

        order = await order_service.update_order_status(
            session, order_id, status_data, user_id
        )

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order {order_id} not found",
            )

        return order

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete order",
    description="Delete an order (only PENDING or CANCELLED)",
)
async def delete_order(
    order_id: int,
    session: AsyncSession = Depends(get_async_session),
    # user_id: str = Depends(get_current_user)  # Add authentication later
):
    """
    Delete an order.

    - **order_id**: Order ID to delete

    Only PENDING or CANCELLED orders can be deleted.
    COMPLETED orders cannot be deleted.
    Only the order owner can delete it.
    """
    try:
        user_id = "admin"  # Replace with actual user_id from authentication

        success = await order_service.delete_order(session, order_id, user_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order {order_id} not found",
            )

        return None

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============= Sales Endpoints =============


@router.get(
    "/{order_id}/sales",
    response_model=list[SaleResponse],
    summary="Get sales records for order",
    description="Get all sales records generated from an order",
)
async def get_order_sales(
    order_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get all sales records for a specific order.

    - **order_id**: Order ID

    Returns one sale record per product in the completed order.
    Only available for COMPLETED orders.
    """
    sales = await sales_service.get_sales_by_order(session, order_id)

    return sales


@router.get(
    "/sales/all",
    response_model=SalesListResponse,
    summary="Get all sales records",
    description="Get all sales records for analytics",
    tags=["Sales"],
)
async def get_all_sales(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get all sales records.

    - **skip**: Pagination offset (default: 0)
    - **limit**: Maximum records to return (default: 100, max: 500)

    Returns sales ordered by sale date (most recent first).
    Used for analytics and AI forecasting.
    """
    return await sales_service.get_all_sales(session, skip, limit)


@router.post(
    "/sales/filter",
    response_model=SalesListResponse,
    summary="Filter sales records",
    description="Filter sales records for analytics",
    tags=["Sales"],
)
async def filter_sales(
    filter_params: SalesFilterParams,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Filter sales records based on criteria.

    - **product_id**: Filter by product UUID
    - **start_date**: Filter sales from this date
    - **end_date**: Filter sales until this date
    - **skip**: Pagination offset
    - **limit**: Maximum records to return

    Used for product-specific analytics and time-based reporting.
    """
    return await sales_service.filter_sales(session, filter_params)


@router.post(
    "/sales/summary",
    response_model=SalesSummaryResponse,
    summary="Get sales summary",
    description="Get sales summary/analytics",
    tags=["Sales"],
)
async def get_sales_summary(
    filter_params: SalesFilterParams = None,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get sales summary (total sales count and revenue).

    - **product_id**: Optional filter by product
    - **start_date**: Optional filter from this date
    - **end_date**: Optional filter until this date

    Returns:
    - Total number of sales
    - Total revenue
    - Date range (if filtered)

    Used for dashboard analytics and reporting.
    """
    return await sales_service.get_sales_summary(session, filter_params)
