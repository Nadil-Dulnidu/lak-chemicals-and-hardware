"""
Integration tests for InventoryService.

All tests use a real in-memory SQLite database.
"""

import uuid
from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product_model import Product
from app.schemas.inventory_schema import (
    StockMovementCreate,
    StockAdjustmentRequest,
    MovementTypeEnum,
)
from app.services.inventory_service import InventoryService
from app.services.product_service import ProductService


# ═══════════════════════════════════════════════════════════════════════════
# RECORD STOCK MOVEMENT (Unified)
# ═══════════════════════════════════════════════════════════════════════════


class TestRecordStockMovement:
    """Tests for InventoryService.record_stock_movement"""

    async def test_record_stock_in(
        self,
        db_session: AsyncSession,
        inventory_service: InventoryService,
        sample_product: Product,
    ):
        """Recording a stock IN movement succeeds."""
        movement_data = StockMovementCreate(
            product_id=str(sample_product.id),
            movement_type=MovementTypeEnum.IN,
            quantity=50,
            reference="Purchase Order PO-001",
        )

        result = await inventory_service.record_stock_movement(
            db_session, movement_data, user_id="admin"
        )

        assert result is not None
        assert result.movement_type == "IN"
        assert result.quantity == 50
        assert result.reference == "Purchase Order PO-001"
        assert result.product_id == str(sample_product.id)

    async def test_record_stock_out(
        self,
        db_session: AsyncSession,
        inventory_service: InventoryService,
        sample_product: Product,
    ):
        """Recording a stock OUT movement succeeds."""
        movement_data = StockMovementCreate(
            product_id=str(sample_product.id),
            movement_type=MovementTypeEnum.OUT,
            quantity=10,
            reference="Sale #12345",
        )

        result = await inventory_service.record_stock_movement(
            db_session, movement_data, user_id="admin"
        )

        assert result is not None
        assert result.movement_type == "OUT"
        assert result.quantity == 10

    async def test_record_movement_invalid_quantity_zero(self):
        """Pydantic rejects quantity=0."""
        with pytest.raises(Exception):
            StockMovementCreate(
                product_id=str(uuid.uuid4()),
                movement_type=MovementTypeEnum.IN,
                quantity=0,
            )

    async def test_record_movement_invalid_quantity_negative(self):
        """Pydantic rejects negative quantity."""
        with pytest.raises(Exception):
            StockMovementCreate(
                product_id=str(uuid.uuid4()),
                movement_type=MovementTypeEnum.IN,
                quantity=-5,
            )


# ═══════════════════════════════════════════════════════════════════════════
# RECORD STOCK IN (Dedicated)
# ═══════════════════════════════════════════════════════════════════════════


class TestRecordStockIn:
    """Tests for InventoryService.record_stock_in"""

    async def test_stock_in_valid(
        self,
        db_session: AsyncSession,
        inventory_service: InventoryService,
        sample_product: Product,
    ):
        """Stock-in with correct type succeeds."""
        movement_data = StockMovementCreate(
            product_id=str(sample_product.id),
            movement_type=MovementTypeEnum.IN,
            quantity=25,
            reference="Restock",
        )

        result = await inventory_service.record_stock_in(
            db_session, movement_data, user_id="admin"
        )

        assert result is not None
        assert result.movement_type == "IN"
        assert result.quantity == 25

    async def test_stock_in_wrong_type_raises(
        self,
        db_session: AsyncSession,
        inventory_service: InventoryService,
        sample_product: Product,
    ):
        """Calling stock_in with movement_type=OUT raises ValueError."""
        movement_data = StockMovementCreate(
            product_id=str(sample_product.id),
            movement_type=MovementTypeEnum.OUT,
            quantity=10,
        )

        with pytest.raises(ValueError, match="Movement type must be IN"):
            await inventory_service.record_stock_in(
                db_session, movement_data, user_id="admin"
            )


# ═══════════════════════════════════════════════════════════════════════════
# RECORD STOCK OUT (Dedicated)
# ═══════════════════════════════════════════════════════════════════════════


class TestRecordStockOut:
    """Tests for InventoryService.record_stock_out"""

    async def test_stock_out_valid(
        self,
        db_session: AsyncSession,
        inventory_service: InventoryService,
        sample_product: Product,
    ):
        """Stock-out with correct type succeeds when stock is sufficient."""
        movement_data = StockMovementCreate(
            product_id=str(sample_product.id),
            movement_type=MovementTypeEnum.OUT,
            quantity=5,
            reference="Manual deduction",
        )

        result = await inventory_service.record_stock_out(
            db_session, movement_data, user_id="admin"
        )

        assert result is not None
        assert result.movement_type == "OUT"

    async def test_stock_out_wrong_type_raises(
        self,
        db_session: AsyncSession,
        inventory_service: InventoryService,
        sample_product: Product,
    ):
        """Calling stock_out with movement_type=IN raises ValueError."""
        movement_data = StockMovementCreate(
            product_id=str(sample_product.id),
            movement_type=MovementTypeEnum.IN,
            quantity=10,
        )

        with pytest.raises(ValueError, match="Movement type must be OUT"):
            await inventory_service.record_stock_out(
                db_session, movement_data, user_id="admin"
            )


# ═══════════════════════════════════════════════════════════════════════════
# GET MOVEMENT
# ═══════════════════════════════════════════════════════════════════════════


class TestGetMovement:
    """Tests for InventoryService.get_movement"""

    async def test_get_movement_valid(
        self,
        db_session: AsyncSession,
        inventory_service: InventoryService,
        sample_product: Product,
    ):
        """Retrieving an existing movement returns correct data."""
        # Create a movement first
        movement_data = StockMovementCreate(
            product_id=str(sample_product.id),
            movement_type=MovementTypeEnum.IN,
            quantity=10,
        )
        created = await inventory_service.record_stock_movement(
            db_session, movement_data
        )

        # Now retrieve it
        if created:
            result = await inventory_service.get_movement(
                db_session, created.movement_id
            )
            assert result is not None
            assert result.movement_id == created.movement_id

    async def test_get_movement_not_found(
        self, db_session: AsyncSession, inventory_service: InventoryService
    ):
        """Retrieving a non-existent movement returns None."""
        result = await inventory_service.get_movement(db_session, 99999)
        assert result is None


# ═══════════════════════════════════════════════════════════════════════════
# GET ALL MOVEMENTS
# ═══════════════════════════════════════════════════════════════════════════


class TestGetAllMovements:
    """Tests for InventoryService.get_all_movements"""

    async def test_get_all_movements_after_recording(
        self,
        db_session: AsyncSession,
        inventory_service: InventoryService,
        sample_product: Product,
    ):
        """After recording movements, get_all returns them."""
        # Record a few movements
        for i in range(3):
            movement_data = StockMovementCreate(
                product_id=str(sample_product.id),
                movement_type=MovementTypeEnum.IN,
                quantity=10 + i,
                reference=f"Batch {i}",
            )
            await inventory_service.record_stock_movement(db_session, movement_data)

        result = await inventory_service.get_all_movements(db_session)


        assert result is not None
        assert result.total >= 3

    async def test_get_all_movements_empty(
        self, db_session: AsyncSession, inventory_service: InventoryService
    ):
        """Returns empty list when no movements exist."""
        result = await inventory_service.get_all_movements(db_session)

        assert result.total == 0
        assert len(result.movements) == 0


# ═══════════════════════════════════════════════════════════════════════════
# DELETE MOVEMENT
# ═══════════════════════════════════════════════════════════════════════════


class TestDeleteMovement:
    """Tests for InventoryService.delete_movement"""

    async def test_delete_movement_valid(
        self,
        db_session: AsyncSession,
        inventory_service: InventoryService,
        sample_product: Product,
    ):
        """Deleting an existing movement returns True."""
        # Create a movement
        movement_data = StockMovementCreate(
            product_id=str(sample_product.id),
            movement_type=MovementTypeEnum.IN,
            quantity=10,
        )
        created = await inventory_service.record_stock_movement(
            db_session, movement_data
        )

        if created:
            result = await inventory_service.delete_movement(
                db_session, created.movement_id
            )
            assert result is True

    async def test_delete_movement_not_found(
        self, db_session: AsyncSession, inventory_service: InventoryService
    ):
        """Deleting a non-existent movement returns False."""
        result = await inventory_service.delete_movement(db_session, 99999)
        assert result is False


# ═══════════════════════════════════════════════════════════════════════════
# STOCK ADJUSTMENT
# ═══════════════════════════════════════════════════════════════════════════


class TestAdjustStock:
    """Tests for InventoryService.adjust_stock"""

    async def test_adjust_stock_increase(
        self,
        db_session: AsyncSession,
        inventory_service: InventoryService,
        sample_product: Product,
    ):
        """Adjusting stock upward creates an IN movement."""
        adjustment = StockAdjustmentRequest(
            product_id=str(sample_product.id),
            target_quantity=sample_product.stock_qty + 50,
            reference="Stock count adjustment",
        )

        result = await inventory_service.adjust_stock(
            db_session, adjustment, user_id="admin"
        )

        assert result is not None
        assert result.movement_type == "IN"
        assert result.quantity == 50

    async def test_adjust_stock_decrease(
        self,
        db_session: AsyncSession,
        inventory_service: InventoryService,
        sample_product: Product,
    ):
        """Adjusting stock downward creates an OUT movement."""
        adjustment = StockAdjustmentRequest(
            product_id=str(sample_product.id),
            target_quantity=sample_product.stock_qty - 20,
            reference="Damaged goods write-off",
        )

        result = await inventory_service.adjust_stock(
            db_session, adjustment, user_id="admin"
        )

        assert result is not None
        assert result.movement_type == "OUT"
        assert result.quantity == 20

    async def test_adjust_stock_no_change(
        self,
        db_session: AsyncSession,
        inventory_service: InventoryService,
        sample_product: Product,
    ):
        """Adjusting to the same quantity returns None (no movement)."""
        adjustment = StockAdjustmentRequest(
            product_id=str(sample_product.id),
            target_quantity=sample_product.stock_qty,
        )

        result = await inventory_service.adjust_stock(
            db_session, adjustment, user_id="admin"
        )

        assert result is None

    async def test_adjust_stock_invalid_product(
        self,
        db_session: AsyncSession,
        inventory_service: InventoryService,
    ):
        """Adjusting stock for a non-existent product raises ValueError."""
        adjustment = StockAdjustmentRequest(
            product_id=str(uuid.uuid4()),
            target_quantity=100,
        )

        with pytest.raises(ValueError, match="Product not found"):
            await inventory_service.adjust_stock(db_session, adjustment)

    async def test_adjust_stock_negative_target(self):
        """Pydantic rejects negative target quantity."""
        with pytest.raises(Exception):
            StockAdjustmentRequest(
                product_id=str(uuid.uuid4()),
                target_quantity=-10,
            )
