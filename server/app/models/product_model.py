import uuid

from sqlalchemy import Column, String, Text, DateTime, Float, Integer, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime
from app.constants import ProductCategory
from app.utils.db import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    brand = Column(String(255), nullable=False)
    category = Column(Enum(ProductCategory), nullable=False)
    price = Column(Float, nullable=False)
    stock_qty = Column(Integer, nullable=False)
    image_url = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
