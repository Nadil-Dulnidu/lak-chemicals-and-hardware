from sqlalchemy import Column, String, Integer, Numeric, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.constants import QuotationStatus
from app.utils.db import Base


class Quotation(Base):
    """
    Model for quotation requests.
    Stores quotation information including status and total amount.
    """

    __tablename__ = "quotations"

    quotation_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False, index=True)
    status = Column(
        Enum(QuotationStatus),
        nullable=False,
        default=QuotationStatus.PENDING,
        index=True,
    )
    total_amount = Column(Numeric(10, 2), nullable=False, default=0.00)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(String(500), nullable=True)

    # Relationship to QuotationItem
    quotation_items = relationship(
        "QuotationItem",
        back_populates="quotation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self):
        return f"<Quotation(id={self.quotation_id}, user_id={self.user_id}, status={self.status.value}, total={self.total_amount})>"


class QuotationItem(Base):
    """
    Model for individual items in a quotation.
    Links quotation to products with quantity and pricing information.
    """

    __tablename__ = "quotation_items"

    quotation_item_id = Column(Integer, primary_key=True, autoincrement=True)
    quotation_id = Column(
        Integer,
        ForeignKey("quotations.quotation_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id = Column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)

    # Relationships
    quotation = relationship("Quotation", back_populates="quotation_items")
    product = relationship("Product", lazy="selectin")

    def __repr__(self):
        return f"<QuotationItem(id={self.quotation_item_id}, quotation_id={self.quotation_id}, product_id={self.product_id}, qty={self.quantity}, subtotal={self.subtotal})>"
