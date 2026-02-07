import uuid
from sqlalchemy import Column, ForeignKey, Table, DateTime, Float
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.utils.db import Base


# Association table for many-to-many relationship between Supplier and Product
supplier_product = Table(
    "supplier_products",
    Base.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column(
        "supplier_id",
        UUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "product_id",
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "supply_price",
        Float,
        nullable=True,
        comment="Price at which supplier provides this product",
    ),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("last_supplied_date", DateTime, nullable=True),
)
