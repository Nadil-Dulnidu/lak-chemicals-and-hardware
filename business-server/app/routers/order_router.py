from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.db import get_async_session
from app.services.order_service import OrderService
from app.services.sales_service import SalesService
from app.schemas.order_schema import (
    OrderCreateFromCart,
    OrderCreateFromQuotation,
    OrderUpdateStatus,
    OrderResponse,
    OrderListResponse,
    OrderFilterParams,
    SaleResponse,
    SalesListResponse,
    SalesFilterParams,
    SalesSummaryResponse,
)

# from app.security.jwt import verify_clerk_token

router = APIRouter(prefix="/orders", tags=["Orders & Sales"])

# Initialize services
order_service = OrderService()
sales_service = SalesService()


# ============= Order Endpoints =============


@router.get(
    "",
    response_model=OrderListResponse,
    summary="Get all orders",
    description="Get all orders (Admin only)",
)
async def get_all_orders(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get all orders.

    - **skip**: Pagination offset (default: 0)
    - **limit**: Maximum records to return (default: 100, max: 500)

    Returns all orders ordered by date (newest first).
    """
    return await order_service.get_all_orders(session, skip, limit)


@router.post(
    "/from-cart",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create order from cart",
    description="Create a new order directly from the user's cart",
)
async def create_order_from_cart(
    order_data: OrderCreateFromCart,
    session: AsyncSession = Depends(get_async_session),
    # user_data: dict = Depends(verify_clerk_token),
):
    """
    Create a new order from the authenticated user's cart.

    - **cart_id**: The cart to convert (required)
    - **payment_method**: Payment method (optional)
    - **notes**: Additional notes (optional)
    - **customer_name / phone / address / city**: Shipping info (optional)

    The order is created in **PENDING** status.
    Stock availability is validated before creation.
    The source cart is referenced via `cart_id` on the order.
    """
    try:
        user_id = user_data.get("sub")

        order = await order_service.create_order_from_cart(session, user_id, order_data)

        if not order:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create order from cart",
            )

        return order

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/from-quotation",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create order from approved quotation",
    description="Create a new order from an APPROVED quotation",
)
async def create_order_from_quotation(
    order_data: OrderCreateFromQuotation,
    session: AsyncSession = Depends(get_async_session),
    user_data: dict = Depends(verify_clerk_token),
):
    """
    Create a new order from an approved quotation.

    - **quotation_id**: The approved quotation to convert (required)
    - **payment_method**: Payment method (optional)
    - **notes**: Additional notes (optional; falls back to quotation notes)
    - **customer_name / phone / address / city**: Shipping info (optional)

    The order is created in **PENDING** status.
    Quotation must be in **APPROVED** status.
    Stock availability is validated before creation.
    The source quotation is referenced via `quotation_id` on the order.
    """
    try:
        user_id = user_data.get("sub")

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
):
    """
    Get an order by its ID.

    - **order_id**: Order ID

    Returns order details including status, payment info, and the
    source entity reference (cart_id or quotation_id).
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
    "/user/{user_id}",
    response_model=OrderListResponse,
    summary="Get user orders",
    description="Get all orders for a specific user",
)
async def get_user_orders(
    user_id: str,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get all orders for a user.

    - **skip**: Pagination offset (default: 0)
    - **limit**: Maximum records to return (default: 100, max: 500)

    Returns orders ordered by order date (most recent first).
    """
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
    user_data: dict = Depends(verify_clerk_token),
):
    """
    Filter orders based on criteria.

    - **status**: Filter by status (PENDING/COMPLETED/CANCELLED)
    - **start_date**: Filter orders from this date
    - **end_date**: Filter orders until this date
    - **skip**: Pagination offset
    - **limit**: Maximum records to return
    """
    user_id = user_data.get("sub")
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
    user_data: dict = Depends(verify_clerk_token),
):
    """
    Update order status.

    - **order_id**: Order ID
    - **status**: New status (PENDING/COMPLETED/CANCELLED)

    Status transitions:
    - PENDING → COMPLETED: deducts stock from source entity items, creates Sale records
    - PENDING → CANCELLED: marks order as cancelled
    - COMPLETED and CANCELLED orders cannot be changed
    """
    try:
        user_id = user_data.get("sub")

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
    user_data: dict = Depends(verify_clerk_token),
):
    """
    Delete an order.

    - **order_id**: Order ID to delete

    Only PENDING or CANCELLED orders can be deleted.
    COMPLETED orders cannot be deleted.
    Only the order owner can delete it.
    """
    try:
        user_id = user_data.get("sub")

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
    user_data: dict = Depends(verify_clerk_token),
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
)
async def get_all_sales(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    session: AsyncSession = Depends(get_async_session),
    user_data: dict = Depends(verify_clerk_token),
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
)
async def filter_sales(
    filter_params: SalesFilterParams,
    session: AsyncSession = Depends(get_async_session),
    user_data: dict = Depends(verify_clerk_token),
):
    """
    Filter sales records based on criteria.

    - **product_id**: Filter by product UUID
    - **start_date**: Filter sales from this date
    - **end_date**: Filter sales until this date
    - **skip**: Pagination offset
    - **limit**: Maximum records to return
    """
    return await sales_service.filter_sales(session, filter_params)


@router.post(
    "/sales/summary",
    response_model=SalesSummaryResponse,
    summary="Get sales summary",
    description="Get sales summary/analytics",
)
async def get_sales_summary(
    filter_params: SalesFilterParams = None,
    session: AsyncSession = Depends(get_async_session),
    user_data: dict = Depends(verify_clerk_token),
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
    """
    return await sales_service.get_sales_summary(session, filter_params)
