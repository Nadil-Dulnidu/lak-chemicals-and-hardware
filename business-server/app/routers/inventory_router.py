from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.utils.db import get_async_session
from app.services.inventory_service import InventoryService
from app.schemas.inventory_schema import (
    StockMovementCreate,
    StockMovementResponse,
    StockMovementListResponse,
    StockMovementFilterParams,
    InventoryLevelResponse,
    StockAdjustmentRequest,
)
from app.security.jwt import verify_clerk_token, require_admin

router = APIRouter(prefix="/inventory", tags=["Inventory"])

# Initialize service
inventory_service = InventoryService()


@router.post(
    "/stock-update",
    response_model=StockMovementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Update stock (IN/OUT)",
    description="Record stock movement (incoming or outgoing) and update inventory levels",
)
async def update_stock(
    movement_data: StockMovementCreate,
    session: AsyncSession = Depends(get_async_session),
    user_data: dict = Depends(verify_clerk_token),
    _admin_data: dict = Depends(require_admin)
):
    """
    Record a stock movement (IN or OUT).

    - **product_id**: Product UUID (required)
    - **movement_type**: "IN" for incoming stock, "OUT" for outgoing stock (required)
    - **quantity**: Quantity to add/remove (required, must be positive)
    - **reference**: Reference number or note (optional)
    - **movement_date**: Date of movement (optional, defaults to now)

    **For IN movements:**
    - Creates a stock movement record
    - Automatically increases the product's stock quantity

    **For OUT movements:**
    - Validates sufficient stock is available
    - Creates a stock movement record
    - Automatically decreases the product's stock quantity
    - Triggers low stock alerts if applicable
    """
    try:
        movement = await inventory_service.record_stock_movement(
            session, movement_data, user_id=user_data.get("sub")
        )

        if not movement:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to record stock movement",
            )

        return movement

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/movements/{movement_id}",
    response_model=StockMovementResponse,
    summary="Get movement by ID",
    description="Retrieve a single stock movement by its ID",
)
async def get_movement(
    movement_id: int,
    session: AsyncSession = Depends(get_async_session),
    user_data: dict = Depends(verify_clerk_token),
    _admin_data: dict = Depends(require_admin)
):
    """
    Get a stock movement by its ID.

    - **movement_id**: ID of the movement
    """
    movement = await inventory_service.get_movement(
        session, movement_id, user_id=user_data.get("sub")
    )

    if not movement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movement with ID {movement_id} not found",
        )

    return movement


@router.get(
    "/movements",
    response_model=StockMovementListResponse,
    summary="Get all movements",
    description="Retrieve all stock movements with pagination",
)
async def get_all_movements(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    session: AsyncSession = Depends(get_async_session),
    user_data: dict = Depends(verify_clerk_token),
    _admin_data: dict = Depends(require_admin)
):
    """
    Get all stock movements with pagination.

    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum records to return (default: 100, max: 500)

    Returns movements ordered by date (most recent first).
    """
    return await inventory_service.get_all_movements(
        session, skip, limit, user_id=user_data.get("sub")
    )


@router.post(
    "/movements/filter",
    response_model=StockMovementListResponse,
    summary="Filter movements",
    description="Filter stock movements based on various criteria",
)
async def filter_movements(
    filter_params: StockMovementFilterParams,
    session: AsyncSession = Depends(get_async_session),
    user_data: dict = Depends(verify_clerk_token),
    _admin_data: dict = Depends(require_admin)
):
    """
    Filter stock movements based on criteria.

    - **product_id**: Filter by product UUID
    - **movement_type**: Filter by type (IN/OUT)
    - **start_date**: Filter movements from this date
    - **end_date**: Filter movements until this date
    - **skip**: Pagination offset
    - **limit**: Maximum records to return
    """
    return await inventory_service.filter_movements(
        session, filter_params, user_id=user_data.get("sub")
    )


@router.get(
    "/products/{product_id}/movements",
    response_model=StockMovementListResponse,
    summary="Get product movements",
    description="Get all stock movements for a specific product",
)
async def get_product_movements(
    product_id: uuid.UUID,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    session: AsyncSession = Depends(get_async_session),
    user_data: dict = Depends(verify_clerk_token),
    _admin_data: dict = Depends(require_admin)
):
    """
    Get all stock movements for a specific product.

    - **product_id**: UUID of the product
    - **skip**: Pagination offset
    - **limit**: Maximum records to return

    Returns complete movement history for the product.
    """
    return await inventory_service.get_product_movements(
        session, product_id, skip, limit, user_id=user_data.get("sub")
    )


@router.get(
    "/products/{product_id}/level",
    response_model=InventoryLevelResponse,
    summary="Get inventory level",
    description="Get current inventory level for a product",
)
async def get_inventory_level(
    product_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    user_data: dict = Depends(verify_clerk_token),
    _admin_data: dict = Depends(require_admin)
):
    """
    Get current inventory level for a product.

    - **product_id**: UUID of the product

    Returns:
    - Current stock quantity
    - Total stock-in
    - Total stock-out
    - Last movement date
    """
    level = await inventory_service.get_inventory_level(
        session, product_id, user_id=user_data.get("sub")
    )

    if not level:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found",
        )

    return level


@router.delete(
    "/movements/{movement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete movement record",
    description="Delete a historical stock movement record (does NOT reverse stock quantity)",
)
async def delete_movement(
    movement_id: int,
    session: AsyncSession = Depends(get_async_session),
    user_data: dict = Depends(verify_clerk_token),
    _admin_data: dict = Depends(require_admin)
):
    """
    Delete a historical stock movement record.

    - **movement_id**: ID of the movement to delete

    ⚠️ WARNING: This only deletes the record from history.
    It does NOT reverse the stock quantity change.
    Use stock adjustment endpoint to correct stock levels.
    """
    success = await inventory_service.delete_movement(
        session, movement_id, user_id=user_data.get("sub")
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movement with ID {movement_id} not found",
        )

    return None


@router.post(
    "/adjust",
    response_model=StockMovementResponse,
    summary="Adjust stock to target quantity",
    description="Adjust product stock to a specific target quantity",
)
async def adjust_stock(
    adjustment: StockAdjustmentRequest,
    session: AsyncSession = Depends(get_async_session),
    user_data: dict = Depends(verify_clerk_token),
    _admin_data: dict = Depends(require_admin)
):
    """
    Adjust stock to a specific target quantity.

    - **product_id**: Product UUID
    - **target_quantity**: Desired stock quantity
    - **reference**: Reason for adjustment (optional)

    This will:
    - Calculate the difference between current and target
    - Create an IN or OUT movement to reach the target
    - Update the product's stock quantity

    Example: If current stock is 50 and target is 100,
    this creates an IN movement of 50 units.
    """
    try:
        movement = await inventory_service.adjust_stock(
            session, adjustment, user_id=user_data.get("sub")
        )

        if not movement:
            # No adjustment needed (already at target)
            raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail="No adjustment needed - already at target quantity",
            )

        return movement

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
