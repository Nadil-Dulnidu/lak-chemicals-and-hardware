import uuid

from sqlalchemy import Column, String, Text, DateTime, Float, Integer, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.constants import ProductCategory
from app.utils.db import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    brand = Column(String(255), nullable=True)
    category = Column(Enum(ProductCategory), nullable=True)
    price = Column(Float, nullable=False)
    stock_qty = Column(Integer, nullable=False, default=0)
    reorder_level = Column(Integer, nullable=False, default=10)
    image_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Many-to-many relationship with Supplier
    suppliers = relationship(
        "Supplier",
        secondary="supplier_products",
        back_populates="products",
        lazy="selectin",
    )
