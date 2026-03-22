"""
Integration tests for ProductService.

All tests hit a real (in-memory SQLite) database — no mocks.
Each test is isolated via transaction rollback (see conftest.py).
"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product_model import Product
from app.schemas.product_schema import ProductCreate, ProductUpdate
from app.services.product_service import ProductService
from app.constants import ProductCategory


# ═══════════════════════════════════════════════════════════════════════════
# CREATE
# ═══════════════════════════════════════════════════════════════════════════


class TestCreateProduct:
    """Tests for ProductService.create_product"""

    async def test_create_product_valid(
        self, db_session: AsyncSession, product_service: ProductService
    ):
        """Creating a product with valid data returns a ProductResponse."""
        data = ProductCreate(
            name="Hammer 500g",
            description="Claw hammer for general use",
            brand="Stanley",
            category=ProductCategory.TOOLS,
            price=1200.00,
            stock_qty=25,
            reorder_level=5,
            image_url="https://example.com/hammer.jpg",
        )

        result = await product_service.create_product(db_session, data, user_id="admin")

        assert result is not None
        assert result.name == "Hammer 500g"
        assert result.brand == "Stanley"
        assert result.price == 1200.00
        assert result.stock_qty == 25
        assert result.is_active is True
        assert result.id is not None  # UUID was assigned

    async def test_create_product_all_fields(
        self, db_session: AsyncSession, product_service: ProductService
    ):
        """Creating a product with all fields succeeds."""
        data = ProductCreate(
            name="Premium Nail Box",
            description="100-piece galvanized nails",
            brand="Builder's Choice",
            category=ProductCategory.BUILDING_MATERIALS,
            price=150.00,
            stock_qty=500,
            reorder_level=20,
            image_url="https://example.com/nails.jpg",
        )

        result = await product_service.create_product(db_session, data)

        assert result is not None
        assert result.name == "Premium Nail Box"
        assert result.description == "100-piece galvanized nails"
        assert result.brand == "Builder's Choice"

    async def test_create_product_zero_stock(
        self, db_session: AsyncSession, product_service: ProductService
    ):
        """A product with zero stock should still be created successfully."""
        data = ProductCreate(
            name="Coming Soon Product",
            description="Not yet available",
            brand="Future Brand",
            category=ProductCategory.TOOLS,
            price=999.99,
            stock_qty=0,
            reorder_level=5,
            image_url="https://example.com/soon.jpg",
        )

        result = await product_service.create_product(db_session, data)

        assert result is not None
        assert result.stock_qty == 0

    async def test_create_product_invalid_price_negative(self):
        """Pydantic rejects a negative price at schema level."""
        with pytest.raises(Exception):
            ProductCreate(
                name="Bad Product",
                description="Invalid",
                brand="Test",
                category=ProductCategory.TOOLS,
                price=-100.00,
                stock_qty=10,
                image_url="https://example.com/bad.jpg",
            )

    async def test_create_product_invalid_price_zero(self):
        """Pydantic rejects price = 0 because of gt=0 constraint."""
        with pytest.raises(Exception):
            ProductCreate(
                name="Free Product",
                description="Invalid",
                brand="Test",
                category=ProductCategory.TOOLS,
                price=0,
                stock_qty=10,
                image_url="https://example.com/free.jpg",
            )

    async def test_create_product_invalid_stock_negative(self):
        """Pydantic rejects negative stock quantity."""
        with pytest.raises(Exception):
            ProductCreate(
                name="Negative Stock",
                description="Invalid",
                brand="Test",
                category=ProductCategory.TOOLS,
                price=100.00,
                stock_qty=-5,
                image_url="https://example.com/neg.jpg",
            )

    async def test_create_product_empty_name(self):
        """Pydantic rejects an empty product name."""
        with pytest.raises(Exception):
            ProductCreate(
                name="",
                description="Invalid",
                brand="Test",
                category=ProductCategory.TOOLS,
                price=100.00,
                stock_qty=10,
                image_url="https://example.com/empty.jpg",
            )

    async def test_create_product_price_is_rounded(
        self, db_session: AsyncSession, product_service: ProductService
    ):
        """Price is rounded to 2 decimal places by the validator."""
        data = ProductCreate(
            name="Precision Price Product",
            description="Test rounding",
            brand="Test",
            category=ProductCategory.TOOLS,
            price=99.999,
            stock_qty=10,
            image_url="https://example.com/precise.jpg",
        )

        # The Pydantic validator rounds it
        assert data.price == 100.00

    async def test_create_product_all_categories(
        self, db_session: AsyncSession, product_service: ProductService
    ):
        """Products can be created with every valid category."""
        for i, category in enumerate(ProductCategory):
            data = ProductCreate(
                name=f"Category Test {category.value} {i}",
                description=f"Testing {category.value} category",
                brand="CatBrand",
                price=100.00,
                stock_qty=10,
                category=category,
                reorder_level=5,
                image_url=f"https://example.com/cat_{i}.jpg",
            )
            result = await product_service.create_product(db_session, data)
            assert result is not None
            # category in ProductResponse is the ProductCategory enum
            assert result.category == category


# ═══════════════════════════════════════════════════════════════════════════
# READ
# ═══════════════════════════════════════════════════════════════════════════


class TestGetProduct:
    """Tests for ProductService.get_product"""

    async def test_get_product_valid(
        self,
        db_session: AsyncSession,
        product_service: ProductService,
        sample_product: Product,
    ):
        """Retrieving a product by its UUID returns the correct data."""
        result = await product_service.get_product(db_session, sample_product.id)

        assert result is not None
        assert result.id == str(sample_product.id)
        assert result.name == sample_product.name
        assert result.price == sample_product.price

    async def test_get_product_not_found(
        self, db_session: AsyncSession, product_service: ProductService
    ):
        """Looking up a non-existent UUID returns None."""
        fake_id = uuid.uuid4()
        result = await product_service.get_product(db_session, fake_id)

        assert result is None


class TestGetAllProducts:
    """Tests for ProductService.get_all_products"""

    async def test_get_all_products_returns_list(
        self,
        db_session: AsyncSession,
        product_service: ProductService,
        sample_products: list[Product],
    ):
        """Returns a ProductListResponse with the created products."""
        result = await product_service.get_all_products(db_session)

        assert result is not None
        assert result.total == len(sample_products)
        assert len(result.products) == len(sample_products)

    async def test_get_all_products_empty(
        self, db_session: AsyncSession, product_service: ProductService
    ):
        """Returns an empty list when no products exist."""
        result = await product_service.get_all_products(db_session)

        assert result is not None
        assert result.total == 0
        assert len(result.products) == 0

    async def test_get_all_products_pagination(
        self,
        db_session: AsyncSession,
        product_service: ProductService,
        sample_products: list[Product],
    ):
        """Pagination skip/limit works correctly."""
        result = await product_service.get_all_products(
            db_session, skip=0, limit=2
        )
        assert len(result.products) == 2
        assert result.has_more is True

        result2 = await product_service.get_all_products(
            db_session, skip=2, limit=2
        )
        assert len(result2.products) == 2

    async def test_get_all_products_large_skip(
        self,
        db_session: AsyncSession,
        product_service: ProductService,
        sample_products: list[Product],
    ):
        """Skip larger than total returns empty list."""
        result = await product_service.get_all_products(
            db_session, skip=1000, limit=100
        )
        assert len(result.products) == 0


# ═══════════════════════════════════════════════════════════════════════════
# SEARCH & FILTER
# ═══════════════════════════════════════════════════════════════════════════


class TestSearchProducts:
    """Tests for ProductService.search_products"""

    async def test_search_products_by_name(
        self,
        db_session: AsyncSession,
        product_service: ProductService,
        sample_products: list[Product],
    ):
        """Searching by partial name returns matching products."""
        result = await product_service.search_products(db_session, "Paint")

        assert result is not None
        assert result.total >= 1
        assert any("Paint" in p.name for p in result.products)

    async def test_search_products_no_results(
        self,
        db_session: AsyncSession,
        product_service: ProductService,
        sample_products: list[Product],
    ):
        """Searching for a non-existent term returns empty list."""
        result = await product_service.search_products(
            db_session, "xyznonexistent1234"
        )

        assert result.total == 0

    async def test_search_products_empty_term(
        self,
        db_session: AsyncSession,
        product_service: ProductService,
        sample_products: list[Product],
    ):
        """Searching with empty string may return all products."""
        result = await product_service.search_products(db_session, "")

        # Implementation-dependent: should not error
        assert result is not None


class TestGetProductsByCategory:
    """Tests for ProductService.get_products_by_category"""

    async def test_get_by_valid_category(
        self,
        db_session: AsyncSession,
        product_service: ProductService,
        sample_products: list[Product],
    ):
        """Returns products in the requested category."""
        result = await product_service.get_products_by_category(
            db_session, "tools"
        )

        assert result.total >= 1
        for p in result.products:
            # category is a ProductCategory enum in ProductResponse
            assert p.category == ProductCategory.TOOLS

    async def test_get_by_invalid_category(
        self,
        db_session: AsyncSession,
        product_service: ProductService,
    ):
        """Invalid category string returns empty list (no error)."""
        result = await product_service.get_products_by_category(
            db_session, "nonexistent_category"
        )

        assert result.total == 0


# ═══════════════════════════════════════════════════════════════════════════
# LOW STOCK ALERTS
# ═══════════════════════════════════════════════════════════════════════════


class TestLowStockAlerts:
    """Tests for ProductService.get_low_stock_alerts"""

    async def test_low_stock_returns_alerts(
        self,
        db_session: AsyncSession,
        product_service: ProductService,
        sample_products: list[Product],
    ):
        """Products below threshold appear in low stock alerts."""
        result = await product_service.get_low_stock_alerts(
            db_session, threshold=10
        )

        assert len(result) >= 2  # Electrical Wire (3) + Safety Helmet (0)

    async def test_low_stock_priority_critical(
        self,
        db_session: AsyncSession,
        product_service: ProductService,
        sample_products: list[Product],
    ):
        """Out-of-stock products have 'critical' priority."""
        result = await product_service.get_low_stock_alerts(
            db_session, threshold=10
        )

        critical_alerts = [a for a in result if a.priority == "critical"]
        assert len(critical_alerts) >= 1  # Safety Helmet (stock=0)

    async def test_low_stock_priority_high(
        self,
        db_session: AsyncSession,
        product_service: ProductService,
        sample_products: list[Product],
    ):
        """Products with stock < 5 have 'high' priority."""
        result = await product_service.get_low_stock_alerts(
            db_session, threshold=10
        )

        high_alerts = [a for a in result if a.priority == "high"]
        assert len(high_alerts) >= 1  # Electrical Wire (stock=3)

    async def test_low_stock_restock_needed(
        self,
        db_session: AsyncSession,
        product_service: ProductService,
        sample_products: list[Product],
    ):
        """restock_needed = threshold - current stock."""
        threshold = 10
        result = await product_service.get_low_stock_alerts(
            db_session, threshold=threshold
        )

        for alert in result:
            assert alert.restock_needed == max(0, threshold - alert.stock_qty)

    async def test_low_stock_high_threshold(
        self,
        db_session: AsyncSession,
        product_service: ProductService,
        sample_products: list[Product],
    ):
        """A very high threshold flags most products."""
        result = await product_service.get_low_stock_alerts(
            db_session, threshold=10000
        )

        assert len(result) == len(sample_products)

    async def test_low_stock_zero_threshold(
        self,
        db_session: AsyncSession,
        product_service: ProductService,
        sample_products: list[Product],
    ):
        """A zero threshold catches products with stock_qty <= 0
        (the repo uses max_stock<=threshold filter)."""
        result = await product_service.get_low_stock_alerts(
            db_session, threshold=0
        )

        # Only products with stock_qty == 0 (Safety Helmet)
        assert len(result) >= 1
        for alert in result:
            assert alert.stock_qty == 0


# ═══════════════════════════════════════════════════════════════════════════
# UPDATE
# ═══════════════════════════════════════════════════════════════════════════


class TestUpdateProduct:
    """Tests for ProductService.update_product"""

    async def test_update_product_name(
        self,
        db_session: AsyncSession,
        product_service: ProductService,
        sample_product: Product,
    ):
        """Updating the name returns updated data."""
        update_data = ProductUpdate(name="Updated Cement Premium")

        result = await product_service.update_product(
            db_session, sample_product.id, update_data
        )

        assert result is not None
        assert result.name == "Updated Cement Premium"
        # Other fields unchanged
        assert result.price == sample_product.price

    async def test_update_product_price(
        self,
        db_session: AsyncSession,
        product_service: ProductService,
        sample_product: Product,
    ):
        """Updating the price persists correctly."""
        update_data = ProductUpdate(price=1500.00)

        result = await product_service.update_product(
            db_session, sample_product.id, update_data
        )

        assert result is not None
        assert result.price == 1500.00

    async def test_update_product_stock(
        self,
        db_session: AsyncSession,
        product_service: ProductService,
        sample_product: Product,
    ):
        """Updating stock quantity works correctly."""
        update_data = ProductUpdate(stock_qty=50)

        result = await product_service.update_product(
            db_session, sample_product.id, update_data
        )

        assert result is not None
        assert result.stock_qty == 50

    async def test_update_product_multiple_fields(
        self,
        db_session: AsyncSession,
        product_service: ProductService,
        sample_product: Product,
    ):
        """Updating multiple fields at once works."""
        update_data = ProductUpdate(
            name="Multi-Update Product",
            price=2000.00,
            stock_qty=75,
            brand="NewBrand",
        )

        result = await product_service.update_product(
            db_session, sample_product.id, update_data
        )

        assert result.name == "Multi-Update Product"
        assert result.price == 2000.00
        assert result.stock_qty == 75
        assert result.brand == "NewBrand"

    async def test_update_product_not_found(
        self, db_session: AsyncSession, product_service: ProductService
    ):
        """Updating a non-existent product returns None."""
        update_data = ProductUpdate(name="Ghost Product")
        fake_id = uuid.uuid4()

        result = await product_service.update_product(
            db_session, fake_id, update_data
        )

        assert result is None

    async def test_update_product_deactivate(
        self,
        db_session: AsyncSession,
        product_service: ProductService,
        sample_product: Product,
    ):
        """Soft-deactivation via is_active=False."""
        update_data = ProductUpdate(is_active=False)

        result = await product_service.update_product(
            db_session, sample_product.id, update_data
        )

        assert result is not None
        assert result.is_active is False

    async def test_update_product_category_change(
        self,
        db_session: AsyncSession,
        product_service: ProductService,
        sample_product: Product,
    ):
        """Category can be changed."""
        update_data = ProductUpdate(category=ProductCategory.CHEMICALS)

        result = await product_service.update_product(
            db_session, sample_product.id, update_data
        )

        assert result is not None
        # ProductResponse.category is a ProductCategory enum
        assert result.category == ProductCategory.CHEMICALS


# ═══════════════════════════════════════════════════════════════════════════
# DELETE
# ═══════════════════════════════════════════════════════════════════════════


class TestDeleteProduct:
    """Tests for ProductService.delete_product"""

    async def test_soft_delete_product(
        self,
        db_session: AsyncSession,
        product_service: ProductService,
        sample_product: Product,
    ):
        """Soft delete marks product as inactive."""
        result = await product_service.delete_product(
            db_session, sample_product.id, soft=True
        )

        assert result is True

        # Product should still exist but be inactive
        product = await product_service.get_product(db_session, sample_product.id)
        if product:
            assert product.is_active is False

    async def test_hard_delete_product(
        self,
        db_session: AsyncSession,
        product_service: ProductService,
        sample_product: Product,
    ):
        """Hard delete removes the product entirely."""
        result = await product_service.delete_product(
            db_session, sample_product.id, soft=False
        )

        assert result is True

        # Product should no longer be retrievable
        product = await product_service.get_product(db_session, sample_product.id)
        assert product is None

    async def test_delete_product_not_found(
        self, db_session: AsyncSession, product_service: ProductService
    ):
        """Deleting a non-existent product returns False."""
        fake_id = uuid.uuid4()
        result = await product_service.delete_product(db_session, fake_id)

        assert result is False
