"""
Shared pytest fixtures for service-layer integration tests.

Uses a REAL SQLite async database (in-memory) to avoid needing PostgreSQL
in CI / local dev.  SQLAlchemy's async dialect makes the services behave
exactly as they do in production (minus Postgres-specific SQL).

Key design decisions
--------------------
* Every test gets its own transaction that is **rolled back** at the end,
  so tests are fully isolated and the DB stays clean.
* Fixtures create lightweight seed data (products, carts, suppliers, etc.)
  that individual tests can rely on.
* `pytest-asyncio` with `mode = "auto"` means every `async def test_…`
  is collected automatically.
"""

import asyncio
import uuid
from datetime import datetime
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)

# ── Project imports ──────────────────────────────────────────────────────
from app.utils.db import Base

# Import ALL models so Base.metadata knows every table
from app.models.product_model import Product  # noqa: F401
from app.models.supplier_model import Supplier  # noqa: F401
from app.models.supplier_product import supplier_product  # noqa: F401
from app.models.cart_model import Cart, CartItem  # noqa: F401
from app.models.order_model import Order, OrderProduct  # noqa: F401
from app.models.quotation_model import Quotation, QuotationItem  # noqa: F401
from app.models.Inventory_model import StockMovement  # noqa: F401
from app.models.sale_model import Sale  # noqa: F401
from app.models.report_model import Report  # noqa: F401

# Import services
from app.services.product_service import ProductService
from app.services.cart_service import CartService
from app.services.supplier_service import SupplierService
from app.services.inventory_service import InventoryService
from app.services.quotation_service import QuotationService
from app.services.order_service import OrderService
from app.services.report_service import ReportService

# Import schemas
from app.schemas.product_schema import ProductCreate
from app.schemas.supplier_schema import SupplierCreate
from app.schemas.cart_schema import CartItemCreate
from app.constants import ProductCategory, MovementType, QuotationStatus, ReportType

# ── SQLite async engine (in-memory) ─────────────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def engine():
    """Create a test engine that lives for the whole session."""
    _engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        # SQLite doesn't support pool_size, but connect_args are needed
        connect_args={"check_same_thread": False},
    )

    # Create all tables once
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield _engine

    # Teardown
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await _engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    """
    Provide a transactional database session for each test.

    Uses a nested transaction (SAVEPOINT) strategy:
    1. Open an outer connection + transaction.
    2. Bind the session to that connection.
    3. After each test, roll back the outer transaction — all changes vanish.
    """
    async with engine.connect() as connection:
        transaction = await connection.begin()

        session_factory = async_sessionmaker(
            bind=connection,
            expire_on_commit=False,
            class_=AsyncSession,
        )
        session = session_factory()

        # Restart nested transactions automatically after each commit
        @event.listens_for(session.sync_session, "after_transaction_end")
        def _restart_savepoint(sess, trans):
            if trans.nested and not trans._parent.nested:
                sess.begin_nested()

        yield session

        await session.close()
        await transaction.rollback()


# ── Service fixtures ─────────────────────────────────────────────────────

@pytest.fixture
def product_service():
    return ProductService()


@pytest.fixture
def cart_service():
    return CartService()


@pytest.fixture
def supplier_service():
    return SupplierService()


@pytest.fixture
def inventory_service():
    return InventoryService()


@pytest.fixture
def quotation_service():
    return QuotationService()


@pytest.fixture
def order_service():
    return OrderService()


@pytest.fixture
def report_service():
    return ReportService()


# ── Test data fixtures ───────────────────────────────────────────────────

@pytest_asyncio.fixture
async def sample_product(db_session: AsyncSession) -> Product:
    """Create a single product for tests that need one."""
    product = Product(
        id=uuid.uuid4(),
        name="Test Cement 50kg",
        description="Premium Portland cement for construction",
        brand="LafargeHolcim",
        category=ProductCategory.BUILDING_MATERIALS,
        price=1250.00,
        stock_qty=100,
        reorder_level=10,
        is_active=True,
        created_at=datetime.utcnow(),
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)
    return product


@pytest_asyncio.fixture
async def sample_products(db_session: AsyncSession) -> list[Product]:
    """Create several products covering different categories."""
    products_data = [
        {
            "name": "White Paint 4L",
            "description": "Interior emulsion paint",
            "brand": "Dulux",
            "category": ProductCategory.PAINTS,
            "price": 3500.00,
            "stock_qty": 50,
            "reorder_level": 10,
        },
        {
            "name": "PVC Pipe 1/2 inch",
            "description": "Half-inch PVC pipe for plumbing",
            "brand": "National",
            "category": ProductCategory.PLUMBING,
            "price": 180.00,
            "stock_qty": 200,
            "reorder_level": 20,
        },
        {
            "name": "Screwdriver Set",
            "description": "6-piece professional screwdriver set",
            "brand": "Stanley",
            "category": ProductCategory.TOOLS,
            "price": 2200.00,
            "stock_qty": 30,
            "reorder_level": 5,
        },
        {
            "name": "Electrical Wire 10m",
            "description": "2.5mm copper electrical wire",
            "brand": "Kelani",
            "category": ProductCategory.ELECTRICAL,
            "price": 850.00,
            "stock_qty": 3,  # Low stock
            "reorder_level": 10,
        },
        {
            "name": "Safety Helmet",
            "description": "Hard hat for construction",
            "brand": "3M",
            "category": ProductCategory.SAFETY_EQUIPMENT,
            "price": 1500.00,
            "stock_qty": 0,  # Out of stock
            "reorder_level": 5,
        },
    ]

    products = []
    for data in products_data:
        product = Product(
            id=uuid.uuid4(),
            is_active=True,
            created_at=datetime.utcnow(),
            **data,
        )
        db_session.add(product)
        products.append(product)

    await db_session.commit()
    for p in products:
        await db_session.refresh(p)
    return products


@pytest_asyncio.fixture
async def sample_supplier(db_session: AsyncSession) -> Supplier:
    """Create a single supplier for tests."""
    supplier = Supplier(
        id=uuid.uuid4(),
        name="Lanka Hardware Pvt Ltd",
        contact_person="Mahinda Perera",
        contact_number="+94-77-1234567",
        email="mahinda@lankahardware.lk",
        address="123 Galle Road, Colombo 03",
        is_active=True,
        created_at=datetime.utcnow(),
    )
    db_session.add(supplier)
    await db_session.commit()
    await db_session.refresh(supplier)
    return supplier


@pytest_asyncio.fixture
async def sample_cart_with_items(
    db_session: AsyncSession, sample_products: list[Product]
) -> Cart:
    """Create a cart with items for a test user."""
    cart = Cart(user_id="test-user-001")
    db_session.add(cart)
    await db_session.flush()

    # Add first two products to cart
    for i, product in enumerate(sample_products[:2]):
        item = CartItem(
            cart_id=cart.cart_id,
            product_id=product.id,
            quantity=i + 1,  # 1 and 2
        )
        db_session.add(item)

    await db_session.commit()
    await db_session.refresh(cart)
    return cart


@pytest_asyncio.fixture
async def sample_report(db_session: AsyncSession) -> Report:
    """Create a saved report configuration."""
    import json

    report = Report(
        report_name="Monthly Sales Report",
        report_type=ReportType.SALES,
        parameters=json.dumps({
            "start_date": "2026-01-01",
            "end_date": "2026-01-31",
            "group_by": "day",
        }),
        created_by="admin-user",
        description="Sales for January 2026",
    )
    db_session.add(report)
    await db_session.commit()
    await db_session.refresh(report)
    return report


@pytest_asyncio.fixture
async def sample_sales_data(
    db_session: AsyncSession, sample_products: list[Product]
) -> list[Sale]:
    """Create sale records linked to sample products (and a dummy order)."""
    from app.models.order_model import Order
    from app.constants import OrderStatus, PaymentStatus

    # Create a minimal order first (sales need an order_id FK)
    order = Order(
        user_id="test-user-sales",
        total_amount=10000.00,
        status=OrderStatus.COMPLETED,
        payment_status=PaymentStatus.PAID,
        address="123 Test Lane",
        city="Colombo",
    )
    db_session.add(order)
    await db_session.flush()  # get order_id

    sales = []
    for i, product in enumerate(sample_products[:3]):
        sale = Sale(
            order_id=order.order_id,
            product_id=product.id,
            quantity=(i + 1) * 5,
            revenue=Decimal(str(product.price)) * (i + 1) * 5,
            sale_date=datetime(2026, 1, 15, 10, 0, 0),
        )
        db_session.add(sale)
        sales.append(sale)

    await db_session.commit()
    for s in sales:
        await db_session.refresh(s)
    return sales
