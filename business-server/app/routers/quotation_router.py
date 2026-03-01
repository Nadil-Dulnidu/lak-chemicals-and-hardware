from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.db import get_async_session
from app.services.quotation_service import QuotationService
from app.schemas.quotation_schema import (
    QuotationCreate,
    QuotationFromCart,
    QuotationUpdateStatus,
    QuotationResponse,
    QuotationListResponse,
    QuotationListResponse,
    QuotationFilterParams,
    OrderFromQuotation,
)
from app.schemas.order_schema import OrderResponse
from app.security.jwt import verify_clerk_token

router = APIRouter(prefix="/quotations", tags=["Quotations"])

# Initialize service
quotation_service = QuotationService()


@router.get(
    "",
    response_model=QuotationListResponse,
    summary="Get all quotations",
    description="Get all quotations (Admin only)",
)
async def get_all_quotations(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    session: AsyncSession = Depends(get_async_session),
    user_data: dict = Depends(verify_clerk_token),
):
    """
    Get all quotations.

    - **skip**: Pagination offset (default: 0)
    - **limit**: Maximum records to return (default: 100, max: 500)

    Returns all quotations ordered by date.
    """
    return await quotation_service.get_all_quotations(session, skip, limit)


@router.post(
    "",
    response_model=QuotationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create quotation",
    description="Create a new quotation request",
)
async def create_quotation(
    quotation_data: QuotationCreate,
    session: AsyncSession = Depends(get_async_session),
    user_data: dict = Depends(verify_clerk_token),
):
    """
    Create a new quotation.

    - **items**: List of items with product_id and quantity (required, at least 1 item)
    - **notes**: Additional notes or requirements (optional)

    The quotation will be created with PENDING status.
    Unit prices and subtotals will be calculated automatically based on current product prices.
    """
    try:
        user_id = user_data.get("sub")

        quotation = await quotation_service.create_quotation(
            session, user_id, quotation_data
        )

        if not quotation:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create quotation",
            )

        return quotation

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/from-cart",
    response_model=QuotationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create quotation from cart",
    description="Convert shopping cart into a quotation request",
)
async def create_quotation_from_cart(
    quotation_data: QuotationFromCart,
    session: AsyncSession = Depends(get_async_session),
    user_data: dict = Depends(verify_clerk_token),
):
    """
    Create a quotation from the user's cart.

    - **notes**: Additional notes or requirements (optional)

    This will:
    - Create a quotation with all items from the cart
    - Clear the cart after successful quotation creation
    - Set quotation status to PENDING
    """
    try:
        user_id = user_data.get("sub")

        quotation = await quotation_service.create_quotation_from_cart(
            session, user_id, quotation_data
        )

        if not quotation:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create quotation from cart",
            )

        return quotation

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{quotation_id}",
    response_model=QuotationResponse,
    summary="Get quotation by ID",
    description="Retrieve a specific quotation by its ID",
)
async def get_quotation(
    quotation_id: int,
    session: AsyncSession = Depends(get_async_session),
    user_data: dict = Depends(verify_clerk_token),
):
    """
    Get a quotation by its ID.

    - **quotation_id**: Quotation ID

    Returns quotation details including all items, status, and total amount.
    """
    user_id = user_data.get("sub")

    quotation = await quotation_service.get_quotation(session, quotation_id, user_id)

    if not quotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quotation {quotation_id} not found",
        )

    return quotation


@router.get(
    "/user/{user_id}",
    response_model=QuotationListResponse,
    summary="Get user quotations",
    description="Get all quotations for the current user",
)
async def get_user_quotations(
    user_id: str,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    session: AsyncSession = Depends(get_async_session),
    user_data: dict = Depends(verify_clerk_token),
):
    """
    Get all quotations for the current user.

    - **skip**: Pagination offset (default: 0)
    - **limit**: Maximum records to return (default: 100, max: 500)

    Returns quotations ordered by creation date (most recent first).
    """
    return await quotation_service.get_user_quotations(session, user_id, skip, limit)


@router.post(
    "/filter",
    response_model=QuotationListResponse,
    summary="Filter quotations",
    description="Filter quotations based on various criteria",
)
async def filter_quotations(
    filter_params: QuotationFilterParams,
    session: AsyncSession = Depends(get_async_session),
    user_data: dict = Depends(verify_clerk_token),
):
    """
    Filter quotations based on criteria.

    - **status**: Filter by status (PENDING/APPROVED/REJECTED)
    - **start_date**: Filter quotations from this date
    - **end_date**: Filter quotations until this date
    - **skip**: Pagination offset
    - **limit**: Maximum records to return
    """
    user_id = user_data.get("sub")

    return await quotation_service.filter_quotations(session, user_id, filter_params)


@router.patch(
    "/{quotation_id}/status",
    response_model=QuotationResponse,
    summary="Update quotation status",
    description="Update the status of a quotation (PENDING/APPROVED/REJECTED)",
)
async def update_quotation_status(
    quotation_id: int,
    status_data: QuotationUpdateStatus,
    session: AsyncSession = Depends(get_async_session),
    user_data: dict = Depends(verify_clerk_token),
):
    """
    Update quotation status.

    - **quotation_id**: Quotation ID
    - **status**: New status (PENDING/APPROVED/REJECTED)

    Status transitions:
    - PENDING → APPROVED (quotation accepted)
    - PENDING → REJECTED (quotation declined)
    - APPROVED → can be used to create confirmed orders
    """
    try:
        user_id = user_data.get("sub")

        quotation = await quotation_service.update_quotation_status(
            session, quotation_id, status_data, user_id
        )

        if not quotation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quotation {quotation_id} not found",
            )

        return quotation

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{quotation_id}/create-order",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create order from quotation",
    description="Create a confirmed order from an approved quotation",
)
async def create_order_from_quotation(
    quotation_id: int,
    order_data: OrderFromQuotation,
    session: AsyncSession = Depends(get_async_session),
    user_data: dict = Depends(verify_clerk_token),
):
    """
    Create an order from an approved quotation.

    - **quotation_id**: Quotation ID (must be APPROVED)
    - **payment_method**: Payment method
    - **customer_name**: Customer name (optional)
    - **phone**: Contact phone (optional)
    - **address**: Shipping address (optional)
    - **city**: City (optional)
    - **notes**: Additional notes

    The order total will reflect any discount applied to the quotation.
    """
    try:
        user_id = user_data.get("sub")

        order = await quotation_service.create_order_from_quotation(
            session, quotation_id, order_data, user_id
        )

        if not order:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create order from quotation (check if APPROVED)",
            )

        return order

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{quotation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete quotation",
    description="Delete a quotation",
)
async def delete_quotation(
    quotation_id: int,
    session: AsyncSession = Depends(get_async_session),
    user_data: dict = Depends(verify_clerk_token),
):
    """
    Delete a quotation.

    - **quotation_id**: Quotation ID to delete

    Only the quotation owner can delete it.
    """
    user_id = user_data.get("sub")

    success = await quotation_service.delete_quotation(session, quotation_id, user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quotation {quotation_id} not found",
        )

    return None
