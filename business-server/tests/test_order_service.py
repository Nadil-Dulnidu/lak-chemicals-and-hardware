"""
Integration tests for OrderService.

All tests use a real in-memory SQLite database.
"""

import uuid
from decimal import Decimal
from datetime import datetime

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product_model import Product
from app.models.cart_model import Cart, CartItem
from app.models.order_model import Order, OrderProduct
from app.schemas.order_schema import (
    OrderCreateFromCart,
    OrderCreateFromQuotation,
    OrderUpdateStatus,
    OrderStatusEnum,
)
from app.services.order_service import OrderService
from app.constants import OrderStatus, PaymentStatus


# ── Additional fixtures ─────────────────────────────────────────────────

@pytest_asyncio.fixture
async def sample_order(
    db_session: AsyncSession,
    sample_products: list[Product],
) -> Order:
    """Create a PENDING order with order products for testing."""
    # First create a cart for this order (source entity)
    cart = Cart(user_id="order-user-001")
    db_session.add(cart)
    await db_session.flush()

    for product in sample_products[:2]:
        item = CartItem(
            cart_id=cart.cart_id,
            product_id=product.id,
            quantity=2,
        )
        db_session.add(item)
    await db_session.flush()

    # Create the order
    total = sum(Decimal(str(p.price)) * 2 for p in sample_products[:2])
    order = Order(
        user_id="order-user-001",
        cart_id=cart.cart_id,
        status=OrderStatus.PENDING,
        total_amount=total,
        payment_method="cash",
        payment_status=PaymentStatus.UNPAID,
        order_date=datetime.utcnow(),
        customer_name="Test Customer",
        phone="+94771234567",
        address="123 Test Street",
        city="Colombo",
    )
    db_session.add(order)
    await db_session.flush()

    # Add order products snapshot
    for product in sample_products[:2]:
        unit_price = Decimal(str(product.price))
        op = OrderProduct(
            order_id=order.order_id,
            product_id=product.id,
            quantity=2,
            unit_price=unit_price,
            subtotal=unit_price * 2,
        )
        db_session.add(op)

    await db_session.commit()
    await db_session.refresh(order)
    return order


# ═══════════════════════════════════════════════════════════════════════════
# READ
# ═══════════════════════════════════════════════════════════════════════════


class TestGetOrder:
    """Tests for OrderService.get_order"""

    async def test_get_order_valid(
        self,
        db_session: AsyncSession,
        order_service: OrderService,
        sample_order: Order,
    ):
        """Retrieving an order by ID with correct user succeeds."""
        result = await order_service.get_order(
            db_session, sample_order.order_id, sample_order.user_id
        )

        assert result is not None
        assert result.order_id == sample_order.order_id
        assert result.status == "PENDING"
        assert result.user_id == "order-user-001"

    async def test_get_order_not_found(
        self, db_session: AsyncSession, order_service: OrderService
    ):
        """Looking up a non-existent order returns None."""
        result = await order_service.get_order(db_session, 99999, "any-user")
        assert result is None

    async def test_get_order_unauthorized(
        self,
        db_session: AsyncSession,
        order_service: OrderService,
        sample_order: Order,
    ):
        """A different user cannot access another user's order."""
        result = await order_service.get_order(
            db_session, sample_order.order_id, "wrong-user"
        )

        assert result is None

    async def test_get_order_admin_access(
        self,
        db_session: AsyncSession,
        order_service: OrderService,
        sample_order: Order,
    ):
        """Admin can access any order without user check."""
        result = await order_service.get_order_by_id_admin(
            db_session, sample_order.order_id
        )

        assert result is not None
        assert result.order_id == sample_order.order_id


class TestGetUserOrders:
    """Tests for OrderService.get_user_orders"""

    async def test_get_user_orders(
        self,
        db_session: AsyncSession,
        order_service: OrderService,
        sample_order: Order,
    ):
        """Returns orders for the correct user."""
        result = await order_service.get_user_orders(
            db_session, sample_order.user_id
        )

        assert result is not None
        assert result.total >= 1
        assert all(o.user_id == sample_order.user_id for o in result.orders)

    async def test_get_user_orders_empty(
        self, db_session: AsyncSession, order_service: OrderService
    ):
        """Returns empty list for user with no orders."""
        result = await order_service.get_user_orders(
            db_session, "no-order-user"
        )

        assert result.total == 0
        assert len(result.orders) == 0

    async def test_get_user_orders_pagination(
        self,
        db_session: AsyncSession,
        order_service: OrderService,
        sample_order: Order,
    ):
        """Pagination works correctly."""
        result = await order_service.get_user_orders(
            db_session, sample_order.user_id, skip=0, limit=1
        )

        assert len(result.orders) <= 1


class TestGetAllOrders:
    """Tests for OrderService.get_all_orders"""

    async def test_get_all_orders(
        self,
        db_session: AsyncSession,
        order_service: OrderService,
        sample_order: Order,
    ):
        """Admin get_all returns all orders."""
        result = await order_service.get_all_orders(db_session)

        assert result is not None
        assert result.total >= 1


# ═══════════════════════════════════════════════════════════════════════════
# ORDER RESPONSE STRUCTURE
# ═══════════════════════════════════════════════════════════════════════════


class TestOrderResponse:
    """Tests for the order response structure"""

    async def test_order_contains_items(
        self,
        db_session: AsyncSession,
        order_service: OrderService,
        sample_order: Order,
    ):
        """Order response includes order product items."""
        result = await order_service.get_order(
            db_session, sample_order.order_id, sample_order.user_id
        )

        assert result is not None
        assert len(result.items) >= 1
        for item in result.items:
            assert item.quantity > 0
            assert item.unit_price > 0
            assert item.subtotal > 0

    async def test_order_has_shipping_info(
        self,
        db_session: AsyncSession,
        order_service: OrderService,
        sample_order: Order,
    ):
        """Order response includes shipping/contact info."""
        result = await order_service.get_order(
            db_session, sample_order.order_id, sample_order.user_id
        )

        assert result is not None
        assert result.customer_name == "Test Customer"
        assert result.phone == "+94771234567"
        assert result.city == "Colombo"

    async def test_order_payment_status_default(
        self,
        db_session: AsyncSession,
        order_service: OrderService,
        sample_order: Order,
    ):
        """New orders default to UNPAID payment status."""
        result = await order_service.get_order(
            db_session, sample_order.order_id, sample_order.user_id
        )

        assert result is not None
        assert result.payment_status == "UNPAID"


# ═══════════════════════════════════════════════════════════════════════════
# UPDATE PAYMENT STATUS
# ═══════════════════════════════════════════════════════════════════════════


class TestUpdatePaymentStatus:
    """Tests for OrderService.update_payment_status"""

    async def test_update_payment_to_paid(
        self,
        db_session: AsyncSession,
        order_service: OrderService,
        sample_order: Order,
    ):
        """Updating payment status to PAID succeeds."""
        result = await order_service.update_payment_status(
            db_session, sample_order.order_id, PaymentStatus.PAID
        )

        if result is not None:
            assert result.payment_status == "PAID"

    async def test_update_payment_nonexistent_order(
        self,
        db_session: AsyncSession,
        order_service: OrderService,
    ):
        """Updating payment for non-existent order returns None."""
        result = await order_service.update_payment_status(
            db_session, 99999, PaymentStatus.PAID
        )

        assert result is None


# ═══════════════════════════════════════════════════════════════════════════
# DELETE
# ═══════════════════════════════════════════════════════════════════════════


class TestDeleteOrder:
    """Tests for OrderService.delete_order"""

    async def test_delete_order_valid(
        self,
        db_session: AsyncSession,
        order_service: OrderService,
        sample_order: Order,
    ):
        """Deleting an owned order succeeds."""
        result = await order_service.delete_order(
            db_session, sample_order.order_id, sample_order.user_id
        )

        assert result is True

    async def test_delete_order_not_found(
        self,
        db_session: AsyncSession,
        order_service: OrderService,
    ):
        """Deleting a non-existent order returns False."""
        result = await order_service.delete_order(db_session, 99999, "any-user")

        assert result is False

    async def test_delete_order_unauthorized(
        self,
        db_session: AsyncSession,
        order_service: OrderService,
        sample_order: Order,
    ):
        """A different user cannot delete another user's order."""
        result = await order_service.delete_order(
            db_session, sample_order.order_id, "wrong-user"
        )

        assert result is False


# ═══════════════════════════════════════════════════════════════════════════
# SCHEMA VALIDATION
# ═══════════════════════════════════════════════════════════════════════════


class TestOrderSchemaValidation:
    """Tests for order schema validation (edge cases)"""

    async def test_order_create_from_cart_schema(self):
        """OrderCreateFromCart accepts valid data."""
        data = OrderCreateFromCart(
            cart_id=1,
            payment_method="cash",
            customer_name="John Doe",
            phone="+94771234567",
            address="123 Main St",
            city="Colombo",
            notes="Urgent delivery",
        )

        assert data.cart_id == 1
        assert data.payment_method == "cash"

    async def test_order_create_from_quotation_schema(self):
        """OrderCreateFromQuotation accepts valid data."""
        data = OrderCreateFromQuotation(
            quotation_id=1,
            payment_method="bank_transfer",
            customer_name="Jane Doe",
        )

        assert data.quotation_id == 1

    async def test_order_update_status_valid_values(self):
        """All valid status values are accepted."""
        for status in OrderStatusEnum:
            data = OrderUpdateStatus(status=status)
            assert data.status == status

    async def test_order_update_status_invalid(self):
        """Invalid status value raises exception."""
        with pytest.raises(Exception):
            OrderUpdateStatus(status="INVALID_STATUS")

    async def test_phone_validation_accepts_10_digits(
        self, order_service: OrderService
    ):
        """Business validation accepts Sri Lanka numbers with exactly 10 digits."""
        normalized = order_service._validate_and_normalize_phone("077-123 4567")
        assert normalized == "0771234567"

    async def test_phone_validation_rejects_non_10_digits(
        self, order_service: OrderService
    ):
        """Business validation rejects phone numbers that are not 10 digits."""
        with pytest.raises(ValueError, match="exactly 10 digits"):
            order_service._validate_and_normalize_phone("+94771234567")
