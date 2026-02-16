import uuid
from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.constants import MovementType
from app.utils.db import Base


class StockMovement(Base):
    """
    Model for tracking inventory stock movements (IN/OUT transactions).
    Records all stock changes for audit trail and inventory analysis.
    """

    __tablename__ = "stock_movements"

    movement_id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    movement_type = Column(Enum(MovementType), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    reference = Column(String(100), nullable=True, comment="Reference number or note")
    movement_date = Column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )
    created_by = Column(
        String(100), nullable=True, comment="User who created this movement"
    )

    # Relationship to Product
    product = relationship("Product", backref="stock_movements", lazy="selectin")

    def __repr__(self):
        return f"<StockMovement(id={self.movement_id}, product_id={self.product_id}, type={self.movement_type.value}, qty={self.quantity})>"
