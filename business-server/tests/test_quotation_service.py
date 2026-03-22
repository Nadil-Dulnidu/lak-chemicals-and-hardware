"""
Integration tests for QuotationService.

All tests use a real in-memory SQLite database.
"""

import uuid
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product_model import Product
from app.models.cart_model import Cart
from app.models.quotation_model import Quotation, QuotationItem
from app.schemas.quotation_schema import (
    QuotationCreate,
    QuotationItemCreate,
    QuotationFromCart,
    QuotationUpdateStatus,
    QuotationStatusEnum,
)
from app.services.quotation_service import QuotationService
from app.constants import QuotationStatus


# ── Additional fixtures ─────────────────────────────────────────────────

@pytest_asyncio.fixture
async def sample_quotation(
    db_session: AsyncSession,
    sample_products: list[Product],
) -> Quotation:
    """Create a PENDING quotation with 2 items for testing."""
    quotation = Quotation(
        user_id="quotation-user-001",
        status=QuotationStatus.PENDING,
        total_amount=Decimal("0.00"),
        notes="Test quotation",
    )
    db_session.add(quotation)
    await db_session.flush()

    total = Decimal("0.00")
    for product in sample_products[:2]:
        unit_price = Decimal(str(product.price))
        qty = 2
        subtotal = unit_price * qty
        total += subtotal

        item = QuotationItem(
            quotation_id=quotation.quotation_id,
            product_id=product.id,
            quantity=qty,
            unit_price=unit_price,
            subtotal=subtotal,
        )
        db_session.add(item)

    quotation.total_amount = total
    await db_session.commit()
    await db_session.refresh(quotation)
    return quotation


# ═══════════════════════════════════════════════════════════════════════════
# CREATE
# ═══════════════════════════════════════════════════════════════════════════


class TestCreateQuotation:
    """Tests for QuotationService.create_quotation"""

    async def test_create_quotation_valid(
        self,
        db_session: AsyncSession,
        quotation_service: QuotationService,
        sample_products: list[Product],
    ):
        """Creating a quotation with valid items succeeds."""
        data = QuotationCreate(
            items=[
                QuotationItemCreate(
                    product_id=str(sample_products[0].id),
                    quantity=5,
                ),
                QuotationItemCreate(
                    product_id=str(sample_products[1].id),
                    quantity=3,
                ),
            ],
            notes="Bulk purchase inquiry",
        )

        result = await quotation_service.create_quotation(
            db_session, "quotation-user-002", data
        )

        assert result is not None
        assert result.status == "PENDING"
        assert len(result.items) == 2
        assert result.notes == "Bulk purchase inquiry"

    async def test_create_quotation_single_item(
        self,
        db_session: AsyncSession,
        quotation_service: QuotationService,
        sample_product: Product,
    ):
        """Quotation with a single item succeeds."""
        data = QuotationCreate(
            items=[
                QuotationItemCreate(
                    product_id=str(sample_product.id),
                    quantity=10,
                ),
            ],
        )

        result = await quotation_service.create_quotation(
            db_session, "single-item-user", data
        )

        assert result is not None
        assert len(result.items) == 1

    async def test_create_quotation_no_items_raises(self):
        """Pydantic rejects a quotation with no items."""
        with pytest.raises(Exception):
            QuotationCreate(items=[])

    async def test_create_quotation_item_zero_quantity(self):
        """Pydantic rejects items with zero quantity."""
        with pytest.raises(Exception):
            QuotationItemCreate(
                product_id=str(uuid.uuid4()),
                quantity=0,
            )


class TestCreateQuotationFromCart:
    """Tests for QuotationService.create_quotation_from_cart"""

    async def test_create_from_cart_valid(
        self,
        db_session: AsyncSession,
        quotation_service: QuotationService,
        sample_cart_with_items: Cart,
    ):
        """Creating a quotation from an existing cart succeeds."""
        user_id = sample_cart_with_items.user_id
        data = QuotationFromCart(notes="From cart")

        result = await quotation_service.create_quotation_from_cart(
            db_session, user_id, data
        )

        assert result is not None
        assert result.status == "PENDING"
        assert len(result.items) >= 1

    async def test_create_from_empty_cart_raises(
        self,
        db_session: AsyncSession,
        quotation_service: QuotationService,
    ):
        """Creating a quotation from an empty/nonexistent cart raises ValueError."""
        data = QuotationFromCart(notes="Empty cart test")

        with pytest.raises(ValueError, match="Cart is empty"):
            await quotation_service.create_quotation_from_cart(
                db_session, "user-with-no-cart", data
            )


# ═══════════════════════════════════════════════════════════════════════════
# READ
# ═══════════════════════════════════════════════════════════════════════════


class TestGetQuotation:
    """Tests for QuotationService.get_quotation"""

    async def test_get_quotation_valid(
        self,
        db_session: AsyncSession,
        quotation_service: QuotationService,
        sample_quotation: Quotation,
    ):
        """Retrieving a quotation by ID returns correct data."""
        result = await quotation_service.get_quotation(
            db_session,
            sample_quotation.quotation_id,
            sample_quotation.user_id,
        )

        assert result is not None
        assert result.quotation_id == sample_quotation.quotation_id
        assert result.status == "PENDING"

    async def test_get_quotation_not_found(
        self,
        db_session: AsyncSession,
        quotation_service: QuotationService,
    ):
        """Retrieving a non-existent quotation returns None."""
        result = await quotation_service.get_quotation(
            db_session, 99999, "any-user"
        )

        assert result is None

    async def test_get_quotation_unauthorized_user(
        self,
        db_session: AsyncSession,
        quotation_service: QuotationService,
        sample_quotation: Quotation,
    ):
        """A different user cannot access another user's quotation."""
        result = await quotation_service.get_quotation(
            db_session,
            sample_quotation.quotation_id,
            "wrong-user-999",
        )

        assert result is None


class TestGetUserQuotations:
    """Tests for QuotationService.get_user_quotations"""

    async def test_get_user_quotations(
        self,
        db_session: AsyncSession,
        quotation_service: QuotationService,
        sample_quotation: Quotation,
    ):
        """Returns quotations for the correct user."""
        result = await quotation_service.get_user_quotations(
            db_session, sample_quotation.user_id
        )

        assert result is not None
        assert result.total >= 1

    async def test_get_user_quotations_empty(
        self,
        db_session: AsyncSession,
        quotation_service: QuotationService,
    ):
        """Returns empty list for a user with no quotations."""
        result = await quotation_service.get_user_quotations(
            db_session, "no-quotation-user"
        )

        assert result.total == 0


# ═══════════════════════════════════════════════════════════════════════════
# UPDATE STATUS
# ═══════════════════════════════════════════════════════════════════════════


class TestUpdateQuotationStatus:
    """Tests for QuotationService.update_quotation_status"""

    async def test_approve_quotation(
        self,
        db_session: AsyncSession,
        quotation_service: QuotationService,
        sample_quotation: Quotation,
    ):
        """Approving a PENDING quotation succeeds."""
        status_data = QuotationUpdateStatus(
            status=QuotationStatusEnum.APPROVED,
            discount_amount=Decimal("50.00"),
        )

        result = await quotation_service.update_quotation_status(
            db_session,
            sample_quotation.quotation_id,
            status_data,
            user_id="admin",
        )

        assert result is not None
        assert result.status == "APPROVED"

    async def test_reject_quotation(
        self,
        db_session: AsyncSession,
        quotation_service: QuotationService,
        sample_quotation: Quotation,
    ):
        """Rejecting a PENDING quotation succeeds."""
        status_data = QuotationUpdateStatus(
            status=QuotationStatusEnum.REJECTED,
        )

        result = await quotation_service.update_quotation_status(
            db_session,
            sample_quotation.quotation_id,
            status_data,
            user_id="admin",
        )

        assert result is not None
        assert result.status == "REJECTED"

    async def test_update_nonexistent_quotation(
        self,
        db_session: AsyncSession,
        quotation_service: QuotationService,
    ):
        """Updating status of a non-existent quotation returns None."""
        status_data = QuotationUpdateStatus(
            status=QuotationStatusEnum.APPROVED,
        )

        result = await quotation_service.update_quotation_status(
            db_session, 99999, status_data, user_id="admin"
        )

        assert result is None


# ═══════════════════════════════════════════════════════════════════════════
# DELETE
# ═══════════════════════════════════════════════════════════════════════════


class TestDeleteQuotation:
    """Tests for QuotationService.delete_quotation"""

    async def test_delete_quotation_valid(
        self,
        db_session: AsyncSession,
        quotation_service: QuotationService,
        sample_quotation: Quotation,
    ):
        """Deleting an owned quotation succeeds."""
        result = await quotation_service.delete_quotation(
            db_session,
            sample_quotation.quotation_id,
            sample_quotation.user_id,
        )

        assert result is True

    async def test_delete_quotation_not_found(
        self,
        db_session: AsyncSession,
        quotation_service: QuotationService,
    ):
        """Deleting a non-existent quotation returns False."""
        result = await quotation_service.delete_quotation(
            db_session, 99999, "any-user"
        )

        assert result is False

    async def test_delete_quotation_unauthorized(
        self,
        db_session: AsyncSession,
        quotation_service: QuotationService,
        sample_quotation: Quotation,
    ):
        """A different user cannot delete another user's quotation."""
        result = await quotation_service.delete_quotation(
            db_session,
            sample_quotation.quotation_id,
            "hacker-user-999",
        )

        assert result is False


# ═══════════════════════════════════════════════════════════════════════════
# BUSINESS RULES
# ═══════════════════════════════════════════════════════════════════════════


class TestQuotationBusinessRules:
    """Tests for quotation business logic"""

    async def test_create_order_from_unapproved_quotation_raises(
        self,
        db_session: AsyncSession,
        quotation_service: QuotationService,
        sample_quotation: Quotation,
    ):
        """Cannot create an order from a PENDING quotation."""
        from app.schemas.quotation_schema import OrderFromQuotation

        order_data = OrderFromQuotation(
            payment_method="cash",
            customer_name="Test Customer",
        )

        with pytest.raises(ValueError, match="APPROVED"):
            await quotation_service.create_order_from_quotation(
                db_session,
                sample_quotation.quotation_id,
                order_data,
                user_id="test-user",
            )

    async def test_create_order_from_nonexistent_quotation_raises(
        self,
        db_session: AsyncSession,
        quotation_service: QuotationService,
    ):
        """Cannot create an order from a quotation that doesn't exist."""
        from app.schemas.quotation_schema import OrderFromQuotation

        order_data = OrderFromQuotation(payment_method="cash")

        with pytest.raises(ValueError, match="not found"):
            await quotation_service.create_order_from_quotation(
                db_session, 99999, order_data, user_id="test-user"
            )
