from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.utils.db import Base


class Sale(Base):
    """
    Model for sales records.
    One record per product sold, created when order is completed.
    Used for analytics, reporting, and AI forecasting.
    """

    __tablename__ = "sales"

    sale_id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(
        Integer,
        ForeignKey("orders.order_id", ondelete="CASCADE"),
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
    revenue = Column(Numeric(10, 2), nullable=False)
    sale_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    order = relationship("Order", lazy="selectin")
    product = relationship("Product", lazy="selectin")

    def __repr__(self):
        return f"<Sale(id={self.sale_id}, order_id={self.order_id}, product_id={self.product_id}, revenue={self.revenue})>"
