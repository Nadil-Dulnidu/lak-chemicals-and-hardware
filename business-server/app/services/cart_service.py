from typing import Optional
import uuid
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.repository.cart_repo import CartRepository
from app.repository.product_repo import ProductRepository
from app.schemas.cart_schema import (
    CartItemCreate,
    CartItemUpdate,
    CartItemResponse,
    CartResponse,
    CartSummaryResponse,
)
from app.config.logging import get_logger, create_owasp_log_context


class CartService:
    """
    Service layer for Cart business logic.
    Handles validation, business rules, orchestration, and data transformation.
    """

    def __init__(self):
        self.repo = CartRepository()
        self.product_repo = ProductRepository()
        self._logger = get_logger(__name__)

    async def add_item_to_cart(
        self,
        session: AsyncSession,
        user_id: str,
        item_data: CartItemCreate,
    ) -> Optional[CartResponse]:
        """
        Add item to cart.

        Args:
            session: Database session
            user_id: User ID
            item_data: Cart item data

        Returns:
            CartResponse with updated cart
        """
        try:
            product_id = uuid.UUID(item_data.product_id)

            self._logger.info(
                f"Adding item to cart: product {product_id}, qty {item_data.quantity}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="add_item_to_cart",
                    location="CartService.add_item_to_cart",
                ),
            )

            # Add item to cart
            cart_item = await self.repo.add_item(
                session, user_id, product_id, item_data.quantity
            )

            if not cart_item:
                return None

            # Get updated cart
            return await self.get_cart(session, user_id)

        except ValueError as e:
            self._logger.error(
                f"Validation error adding item to cart: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="add_item_to_cart_validation_error",
                    location="CartService.add_item_to_cart",
                ),
            )
            raise

        except Exception as e:
            self._logger.error(
                f"Service error adding item to cart: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="add_item_to_cart_error",
                    location="CartService.add_item_to_cart",
                ),
            )
            raise

    async def update_cart_item(
        self,
        session: AsyncSession,
        user_id: str,
        cart_item_id: int,
        update_data: CartItemUpdate,
    ) -> Optional[CartResponse]:
        """
        Update cart item quantity.

        Args:
            session: Database session
            user_id: User ID
            cart_item_id: Cart item ID
            update_data: Update data

        Returns:
            CartResponse with updated cart
        """
        try:
            self._logger.info(
                f"Updating cart item: {cart_item_id}, new qty {update_data.quantity}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="update_cart_item",
                    location="CartService.update_cart_item",
                ),
            )

            cart_item = await self.repo.update_item_quantity(
                session, user_id, cart_item_id, update_data.quantity
            )

            if not cart_item:
                return None

            return await self.get_cart(session, user_id)

        except Exception as e:
            self._logger.error(
                f"Service error updating cart item: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="update_cart_item_error",
                    location="CartService.update_cart_item",
                ),
            )
            raise

    async def remove_cart_item(
        self, session: AsyncSession, user_id: str, cart_item_id: int
    ) -> bool:
        """
        Remove item from cart.

        Args:
            session: Database session
            user_id: User ID
            cart_item_id: Cart item ID

        Returns:
            True if successful
        """
        try:
            self._logger.info(
                f"Removing cart item: {cart_item_id}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="remove_cart_item",
                    location="CartService.remove_cart_item",
                ),
            )

            return await self.repo.remove_item(session, user_id, cart_item_id)

        except Exception as e:
            self._logger.error(
                f"Service error removing cart item: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="remove_cart_item_error",
                    location="CartService.remove_cart_item",
                ),
            )
            return False

    async def clear_cart(self, session: AsyncSession, user_id: str) -> bool:
        """
        Clear all items from cart.

        Args:
            session: Database session
            user_id: User ID

        Returns:
            True if successful
        """
        try:
            self._logger.info(
                f"Clearing cart for user: {user_id}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="clear_cart",
                    location="CartService.clear_cart",
                ),
            )

            return await self.repo.clear_cart(session, user_id)

        except Exception as e:
            self._logger.error(
                f"Service error clearing cart: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="clear_cart_error",
                    location="CartService.clear_cart",
                ),
            )
            return False

    async def get_cart(
        self, session: AsyncSession, user_id: str
    ) -> Optional[CartResponse]:
        """
        Get user's cart with all items and calculated totals.

        Args:
            session: Database session
            user_id: User ID

        Returns:
            CartResponse with cart details
        """
        try:
            cart = await self.repo.get_cart_with_items(session, user_id)

            if not cart:
                return None

            # Build cart response with product details and calculations
            cart_items = []
            total_amount = Decimal("0.00")

            for item in cart.cart_items:
                product = item.product
                if product:
                    subtotal = Decimal(str(product.price)) * item.quantity
                    total_amount += subtotal

                    cart_items.append(
                        CartItemResponse(
                            cart_item_id=item.cart_item_id,
                            product_id=str(item.product_id),
                            product_name=product.name,
                            product_price=Decimal(str(product.price)),
                            quantity=item.quantity,
                            subtotal=subtotal,
                        )
                    )

            return CartResponse(
                cart_id=cart.cart_id,
                user_id=cart.user_id,
                items=cart_items,
                total_items=len(cart_items),
                total_amount=total_amount,
            )

        except Exception as e:
            self._logger.error(
                f"Service error getting cart: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="get_cart_error",
                    location="CartService.get_cart",
                ),
            )
            return None

    async def get_cart_summary(
        self, session: AsyncSession, user_id: str
    ) -> Optional[CartSummaryResponse]:
        """
        Get cart summary (without item details).

        Args:
            session: Database session
            user_id: User ID

        Returns:
            CartSummaryResponse
        """
        try:
            cart_response = await self.get_cart(session, user_id)

            if not cart_response:
                return None

            return CartSummaryResponse(
                cart_id=cart_response.cart_id,
                user_id=cart_response.user_id,
                total_items=cart_response.total_items,
                total_amount=cart_response.total_amount,
            )

        except Exception as e:
            self._logger.error(
                f"Service error getting cart summary: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="get_cart_summary_error",
                    location="CartService.get_cart_summary",
                ),
            )
            return None
