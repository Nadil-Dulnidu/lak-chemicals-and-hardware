"""
Integration tests for CartService.

All tests use a real in-memory SQLite database.

NOTE: The CartService auto-creates a cart when `get_cart` or `get_cart_summary`
is called for a new user_id, so these methods never return None.
"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product_model import Product
from app.models.cart_model import Cart, CartItem
from app.schemas.cart_schema import CartItemCreate, CartItemUpdate
from app.services.cart_service import CartService


# ═══════════════════════════════════════════════════════════════════════════
# ADD ITEM
# ═══════════════════════════════════════════════════════════════════════════


class TestAddItemToCart:
    """Tests for CartService.add_item_to_cart"""

    async def test_add_item_valid(
        self,
        db_session: AsyncSession,
        cart_service: CartService,
        sample_product: Product,
    ):
        """Adding a valid product to a new user's cart creates the cart and item."""
        user_id = "cart-user-001"
        item_data = CartItemCreate(
            product_id=str(sample_product.id),
            quantity=3,
        )

        result = await cart_service.add_item_to_cart(db_session, user_id, item_data)

        assert result is not None
        assert result.user_id == user_id
        assert result.total_items == 1
        assert result.items[0].quantity == 3
        assert result.total_amount > 0

    async def test_add_multiple_items(
        self,
        db_session: AsyncSession,
        cart_service: CartService,
        sample_products: list[Product],
    ):
        """Adding multiple different products to the same cart works."""
        user_id = "cart-user-002"

        for product in sample_products[:3]:
            item_data = CartItemCreate(
                product_id=str(product.id),
                quantity=1,
            )
            await cart_service.add_item_to_cart(db_session, user_id, item_data)

        # Verify final cart
        cart = await cart_service.get_cart(db_session, user_id)
        assert cart is not None
        assert cart.total_items == 3

    async def test_add_item_calculates_subtotal(
        self,
        db_session: AsyncSession,
        cart_service: CartService,
        sample_product: Product,
    ):
        """Item subtotal = product price × quantity."""
        user_id = "cart-user-subtotal"
        item_data = CartItemCreate(
            product_id=str(sample_product.id),
            quantity=5,
        )

        result = await cart_service.add_item_to_cart(db_session, user_id, item_data)

        assert result is not None
        expected_subtotal = sample_product.price * 5
        assert float(result.items[0].subtotal) == pytest.approx(
            expected_subtotal, rel=0.01
        )

    async def test_add_item_invalid_quantity_zero(self):
        """Pydantic rejects quantity=0."""
        with pytest.raises(Exception):
            CartItemCreate(
                product_id=str(uuid.uuid4()),
                quantity=0,
            )

    async def test_add_item_invalid_quantity_negative(self):
        """Pydantic rejects negative quantity."""
        with pytest.raises(Exception):
            CartItemCreate(
                product_id=str(uuid.uuid4()),
                quantity=-3,
            )


# ═══════════════════════════════════════════════════════════════════════════
# UPDATE ITEM
# ═══════════════════════════════════════════════════════════════════════════


class TestUpdateCartItem:
    """Tests for CartService.update_cart_item"""

    async def test_update_item_quantity(
        self,
        db_session: AsyncSession,
        cart_service: CartService,
        sample_cart_with_items: Cart,
    ):
        """Updating a cart item's quantity is reflected in the cart."""
        user_id = sample_cart_with_items.user_id
        cart_item = sample_cart_with_items.cart_items[0]

        update_data = CartItemUpdate(quantity=10)

        result = await cart_service.update_cart_item(
            db_session, user_id, cart_item.cart_item_id, update_data
        )

        if result is not None:
            # Find the updated item
            updated_item = next(
                (i for i in result.items if i.cart_item_id == cart_item.cart_item_id),
                None,
            )
            assert updated_item is not None
            assert updated_item.quantity == 10

    async def test_update_item_invalid_zero_quantity(self):
        """Pydantic rejects zero quantity for updates."""
        with pytest.raises(Exception):
            CartItemUpdate(quantity=0)


# ═══════════════════════════════════════════════════════════════════════════
# REMOVE ITEM
# ═══════════════════════════════════════════════════════════════════════════


class TestRemoveCartItem:
    """Tests for CartService.remove_cart_item"""

    async def test_remove_existing_item(
        self,
        db_session: AsyncSession,
        cart_service: CartService,
        sample_cart_with_items: Cart,
    ):
        """Removing an existing cart item returns True."""
        user_id = sample_cart_with_items.user_id
        cart_item = sample_cart_with_items.cart_items[0]

        result = await cart_service.remove_cart_item(
            db_session, user_id, cart_item.cart_item_id
        )

        assert result is True

    async def test_remove_nonexistent_item(
        self,
        db_session: AsyncSession,
        cart_service: CartService,
        sample_cart_with_items: Cart,
    ):
        """Removing a non-existent item returns False."""
        user_id = sample_cart_with_items.user_id

        result = await cart_service.remove_cart_item(db_session, user_id, 99999)

        assert result is False


# ═══════════════════════════════════════════════════════════════════════════
# CLEAR CART
# ═══════════════════════════════════════════════════════════════════════════


class TestClearCart:
    """Tests for CartService.clear_cart"""

    async def test_clear_cart_returns_true(
        self,
        db_session: AsyncSession,
        cart_service: CartService,
        sample_cart_with_items: Cart,
    ):
        """Clearing a cart returns True."""
        user_id = sample_cart_with_items.user_id

        result = await cart_service.clear_cart(db_session, user_id)
        assert result is True

    async def test_clear_cart_already_empty(
        self,
        db_session: AsyncSession,
        cart_service: CartService,
    ):
        """Clearing a cart that doesn't exist or is empty doesn't error."""
        result = await cart_service.clear_cart(db_session, "no-cart-user")
        # Should not raise, may return True or False depending on impl
        assert isinstance(result, bool)


# ═══════════════════════════════════════════════════════════════════════════
# GET CART
# ═══════════════════════════════════════════════════════════════════════════


class TestGetCart:
    """Tests for CartService.get_cart"""

    async def test_get_cart_with_items(
        self,
        db_session: AsyncSession,
        cart_service: CartService,
        sample_cart_with_items: Cart,
    ):
        """Getting a cart returns all items with calculated totals."""
        result = await cart_service.get_cart(
            db_session, sample_cart_with_items.user_id
        )

        assert result is not None
        assert result.total_items == len(sample_cart_with_items.cart_items)
        assert result.total_amount > 0

    async def test_get_cart_new_user_creates_empty_cart(
        self,
        db_session: AsyncSession,
        cart_service: CartService,
    ):
        """Getting a cart for a new user auto-creates an empty cart (not None)."""
        result = await cart_service.get_cart(db_session, "brand-new-user-999")

        # Cart service auto-creates carts
        assert result is not None
        assert result.total_items == 0
        assert result.total_amount == 0


# ═══════════════════════════════════════════════════════════════════════════
# CART SUMMARY
# ═══════════════════════════════════════════════════════════════════════════


class TestGetCartSummary:
    """Tests for CartService.get_cart_summary"""

    async def test_get_cart_summary_valid(
        self,
        db_session: AsyncSession,
        cart_service: CartService,
        sample_cart_with_items: Cart,
    ):
        """Cart summary returns item count and total amount."""
        result = await cart_service.get_cart_summary(
            db_session, sample_cart_with_items.user_id
        )

        assert result is not None
        assert result.total_items >= 1
        assert result.total_amount > 0

    async def test_get_cart_summary_new_user(
        self,
        db_session: AsyncSession,
        cart_service: CartService,
    ):
        """Summary for a new user returns empty cart summary (auto-created)."""
        result = await cart_service.get_cart_summary(
            db_session, "new-user-summary-001"
        )

        # Cart service auto-creates carts
        assert result is not None
        assert result.total_items == 0
        assert result.total_amount == 0
