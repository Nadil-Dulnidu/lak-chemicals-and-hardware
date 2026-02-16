from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.db import get_async_session
from app.services.cart_service import CartService
from app.schemas.cart_schema import (
    CartItemCreate,
    CartItemUpdate,
    CartResponse,
    CartSummaryResponse,
)
from app.security.jwt import verify_clerk_token

router = APIRouter(prefix="/cart", tags=["Cart"])

# Initialize service
cart_service = CartService()


@router.post(
    "/items",
    response_model=CartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add item to cart",
    description="Add a product to the user's shopping cart",
)
async def add_item_to_cart(
    item_data: CartItemCreate,
    session: AsyncSession = Depends(get_async_session),
    user_data: dict = Depends(verify_clerk_token),
):
    """
    Add an item to the cart.

    - **product_id**: Product UUID (required)
    - **quantity**: Quantity to add (required, must be positive)

    If the product already exists in the cart, the quantity will be added to the existing quantity.
    """
    try:
        user_id = user_data.get("sub")

        cart = await cart_service.add_item_to_cart(session, user_id, item_data)

        if not cart:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add item to cart",
            )

        return cart

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/items",
    response_model=CartResponse,
    summary="Get cart",
    description="Get the user's shopping cart with all items",
)
async def get_cart(
    session: AsyncSession = Depends(get_async_session),
    user_data: dict = Depends(verify_clerk_token)
):
    """
    Get the user's cart with all items and calculated totals.

    Returns:
    - Cart ID
    - User ID
    - List of items with product details
    - Total items count
    - Total amount
    """
    user_id = user_data.get("sub")

    cart = await cart_service.get_cart(session, user_id)

    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found",
        )

    return cart


@router.get(
    "/summary",
    response_model=CartSummaryResponse,
    summary="Get cart summary",
    description="Get cart summary without item details",
)
async def get_cart_summary(
    session: AsyncSession = Depends(get_async_session),
    user_data: dict = Depends(verify_clerk_token),
):
    """
    Get cart summary (total items and amount only).

    Useful for displaying cart badge or quick overview.
    """
    user_id = user_data.get("sub")

    summary = await cart_service.get_cart_summary(session, user_id)

    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found",
        )

    return summary


@router.put(
    "/items/{cart_item_id}",
    response_model=CartResponse,
    summary="Update cart item quantity",
    description="Update the quantity of an item in the cart",
)
async def update_cart_item(
    cart_item_id: int,
    update_data: CartItemUpdate,
    session: AsyncSession = Depends(get_async_session),
    user_data: dict = Depends(verify_clerk_token),
):
    """
    Update cart item quantity.

    - **cart_item_id**: Cart item ID (required)
    - **quantity**: New quantity (required, must be positive)
    """
    try:
        user_id = user_data.get("sub")

        cart = await cart_service.update_cart_item(
            session, user_id, cart_item_id, update_data
        )

        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cart item {cart_item_id} not found",
            )

        return cart

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/items/{cart_item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove item from cart",
    description="Remove a specific item from the cart",
)
async def remove_cart_item(
    cart_item_id: int,
    session: AsyncSession = Depends(get_async_session),
    user_data: dict = Depends(verify_clerk_token),
):
    """
    Remove an item from the cart.

    - **cart_item_id**: Cart item ID to remove
    """
    user_id = user_data.get("sub")

    success = await cart_service.remove_cart_item(session, user_id, cart_item_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cart item {cart_item_id} not found",
        )

    return None


@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Clear cart",
    description="Remove all items from the cart",
)
async def clear_cart(
    session: AsyncSession = Depends(get_async_session),
    user_data: dict = Depends(verify_clerk_token),
):
    """
    Clear all items from the cart.

    This removes all items but keeps the cart itself.
    """
    user_id = user_data.get("sub")

    success = await cart_service.clear_cart(session, user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear cart",
        )

    return None
