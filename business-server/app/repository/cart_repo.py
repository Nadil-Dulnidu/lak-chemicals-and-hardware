import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.models.cart_model import Cart, CartItem
from app.models.product_model import Product
from app.config.logging import get_logger, create_owasp_log_context


class CartRepository:
    """
    Singleton repository for Cart CRUD operations.
    Implements comprehensive logging and error handling for production use.
    """

    _instance: Optional["CartRepository"] = None
    _logger = None

    def __new__(cls):
        """Singleton pattern implementation"""
        if cls._instance is None:
            cls._instance = super(CartRepository, cls).__new__(cls)
            cls._logger = get_logger(__name__)
            cls._logger.info(
                "CartRepository singleton instance created",
                extra=create_owasp_log_context(
                    user="system",
                    action="repository_initialization",
                    location="CartRepository.__new__",
                ),
            )
        return cls._instance

    async def get_or_create_cart(
        self, session: AsyncSession, user_id: str
    ) -> Optional[Cart]:
        """
        Get user's cart or create one if it doesn't exist.

        Args:
            session: AsyncSession for database operations
            user_id: User ID

        Returns:
            Cart object
        """
        try:
            # Try to get existing cart
            result = await session.execute(select(Cart).where(Cart.user_id == user_id))
            cart = result.scalar_one_or_none()

            if cart:
                self._logger.info(
                    f"Cart retrieved for user: {user_id}",
                    extra=create_owasp_log_context(
                        user=user_id,
                        action="get_cart_success",
                        location="CartRepository.get_or_create_cart",
                    ),
                )
                return cart

            # Create new cart
            cart = Cart(user_id=user_id)
            session.add(cart)
            await session.commit()
            await session.refresh(cart)

            self._logger.info(
                f"Cart created for user: {user_id}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="create_cart_success",
                    location="CartRepository.get_or_create_cart",
                ),
            )

            return cart

        except SQLAlchemyError as e:
            await session.rollback()
            error_msg = f"Database error getting/creating cart: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user=user_id,
                    action="get_or_create_cart_db_error",
                    location="CartRepository.get_or_create_cart",
                ),
            )
            return None

    async def add_item(
        self, session: AsyncSession, user_id: str, product_id: uuid.UUID, quantity: int
    ) -> Optional[CartItem]:
        """
        Add item to cart or update quantity if already exists.

        Args:
            session: AsyncSession for database operations
            user_id: User ID
            product_id: Product UUID
            quantity: Quantity to add

        Returns:
            CartItem object or None if operation fails
        """
        try:
            # Get or create cart
            cart = await self.get_or_create_cart(session, user_id)
            if not cart:
                return None

            # Check if product exists
            product_result = await session.execute(
                select(Product).where(Product.id == product_id)
            )
            product = product_result.scalar_one_or_none()

            if not product:
                error_msg = f"Product not found: {product_id}"
                self._logger.error(
                    error_msg,
                    extra=create_owasp_log_context(
                        user=user_id,
                        action="add_cart_item_product_not_found",
                        location="CartRepository.add_item",
                    ),
                )
                raise ValueError(error_msg)

            # Check if item already in cart
            existing_item_result = await session.execute(
                select(CartItem).where(
                    and_(
                        CartItem.cart_id == cart.cart_id,
                        CartItem.product_id == product_id,
                    )
                )
            )
            existing_item = existing_item_result.scalar_one_or_none()

            if existing_item:
                # Update quantity
                existing_item.quantity += quantity
                await session.commit()
                await session.refresh(existing_item)

                self._logger.info(
                    f"Cart item quantity updated: {existing_item.cart_item_id} (new qty: {existing_item.quantity})",
                    extra=create_owasp_log_context(
                        user=user_id,
                        action="update_cart_item_quantity",
                        location="CartRepository.add_item",
                    ),
                )

                return existing_item

            # Create new cart item
            cart_item = CartItem(
                cart_id=cart.cart_id, product_id=product_id, quantity=quantity
            )
            session.add(cart_item)
            await session.commit()
            await session.refresh(cart_item)

            self._logger.info(
                f"Item added to cart: {cart_item.cart_item_id}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="add_cart_item_success",
                    location="CartRepository.add_item",
                ),
            )

            return cart_item

        except ValueError as e:
            await session.rollback()
            raise

        except SQLAlchemyError as e:
            await session.rollback()
            error_msg = f"Database error adding item to cart: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user=user_id,
                    action="add_cart_item_db_error",
                    location="CartRepository.add_item",
                ),
            )
            return None

    async def update_item_quantity(
        self, session: AsyncSession, user_id: str, cart_item_id: int, quantity: int
    ) -> Optional[CartItem]:
        """
        Update cart item quantity.

        Args:
            session: AsyncSession for database operations
            user_id: User ID
            cart_item_id: Cart item ID
            quantity: New quantity

        Returns:
            Updated CartItem or None if not found
        """
        try:
            # Get cart
            cart = await self.get_or_create_cart(session, user_id)
            if not cart:
                return None

            # Get cart item
            result = await session.execute(
                select(CartItem).where(
                    and_(
                        CartItem.cart_item_id == cart_item_id,
                        CartItem.cart_id == cart.cart_id,
                    )
                )
            )
            cart_item = result.scalar_one_or_none()

            if not cart_item:
                self._logger.warning(
                    f"Cart item not found: {cart_item_id}",
                    extra=create_owasp_log_context(
                        user=user_id,
                        action="update_cart_item_not_found",
                        location="CartRepository.update_item_quantity",
                    ),
                )
                return None

            # Update quantity
            cart_item.quantity = quantity
            await session.commit()
            await session.refresh(cart_item)

            self._logger.info(
                f"Cart item quantity updated: {cart_item_id} (new qty: {quantity})",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="update_cart_item_success",
                    location="CartRepository.update_item_quantity",
                ),
            )

            return cart_item

        except SQLAlchemyError as e:
            await session.rollback()
            error_msg = f"Database error updating cart item: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user=user_id,
                    action="update_cart_item_db_error",
                    location="CartRepository.update_item_quantity",
                ),
            )
            return None

    async def remove_item(
        self, session: AsyncSession, user_id: str, cart_item_id: int
    ) -> bool:
        """
        Remove item from cart.

        Args:
            session: AsyncSession for database operations
            user_id: User ID
            cart_item_id: Cart item ID to remove

        Returns:
            True if removal was successful, False otherwise
        """
        try:
            # Get cart
            cart = await self.get_or_create_cart(session, user_id)
            if not cart:
                return False

            # Delete cart item
            stmt = delete(CartItem).where(
                and_(
                    CartItem.cart_item_id == cart_item_id,
                    CartItem.cart_id == cart.cart_id,
                )
            )
            result = await session.execute(stmt)
            await session.commit()

            if result.rowcount == 0:
                self._logger.warning(
                    f"Cart item not found for removal: {cart_item_id}",
                    extra=create_owasp_log_context(
                        user=user_id,
                        action="remove_cart_item_not_found",
                        location="CartRepository.remove_item",
                    ),
                )
                return False

            self._logger.info(
                f"Item removed from cart: {cart_item_id}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="remove_cart_item_success",
                    location="CartRepository.remove_item",
                ),
            )

            return True

        except SQLAlchemyError as e:
            await session.rollback()
            error_msg = f"Database error removing cart item: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user=user_id,
                    action="remove_cart_item_db_error",
                    location="CartRepository.remove_item",
                ),
            )
            return False

    async def clear_cart(self, session: AsyncSession, user_id: str) -> bool:
        """
        Clear all items from cart.

        Args:
            session: AsyncSession for database operations
            user_id: User ID

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get cart
            cart = await self.get_or_create_cart(session, user_id)
            if not cart:
                return False

            # Delete all cart items
            stmt = delete(CartItem).where(CartItem.cart_id == cart.cart_id)
            await session.execute(stmt)
            await session.commit()

            self._logger.info(
                f"Cart cleared for user: {user_id}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="clear_cart_success",
                    location="CartRepository.clear_cart",
                ),
            )

            return True

        except SQLAlchemyError as e:
            await session.rollback()
            error_msg = f"Database error clearing cart: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user=user_id,
                    action="clear_cart_db_error",
                    location="CartRepository.clear_cart",
                ),
            )
            return False

    async def get_cart_with_items(
        self, session: AsyncSession, user_id: str
    ) -> Optional[Cart]:
        """
        Get cart with all items and product details.

        Args:
            session: AsyncSession for database operations
            user_id: User ID

        Returns:
            Cart object with items or None
        """
        try:
            cart = await self.get_or_create_cart(session, user_id)
            return cart

        except Exception as e:
            error_msg = f"Error getting cart with items: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user=user_id,
                    action="get_cart_with_items_error",
                    location="CartRepository.get_cart_with_items",
                ),
            )
            return None
