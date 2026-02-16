import uuid

from sqlalchemy import Column, String, Text, DateTime, Float, Integer, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.utils.db import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    contact_person = Column(String(255), nullable=True)
    contact_number = Column(String(50), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    address = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_purchase_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    # Many-to-many relationship with Product
    products = relationship(
        "Product",
        secondary="supplier_products",
        back_populates="suppliers",
        lazy="selectin",
    )
