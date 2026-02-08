from sqlalchemy import Column, String, Integer, Numeric, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.constants import OrderStatus
from app.utils.db import Base


class Order(Base):
    """
    Model for customer orders.
    Stores order information including status, total amount, payment details, and shipping info.
    """

    __tablename__ = "orders"

    order_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False, index=True)
    status = Column(
        Enum(OrderStatus),
        nullable=False,
        default=OrderStatus.PENDING,
        index=True,
    )
    total_amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(String(50), nullable=True)
    order_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_date = Column(DateTime, nullable=True)
    cancelled_date = Column(DateTime, nullable=True)
    notes = Column(String(500), nullable=True)

    # Shipping Information
    customer_name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    address = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)

    # Relationships
    order_items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self):
        return f"<Order(id={self.order_id}, user_id={self.user_id}, status={self.status.value}, total={self.total_amount})>"


class OrderItem(Base):
    """
    Model for individual items in an order.
    Links order to products with quantity and pricing information.
    """

    __tablename__ = "order_items"

    order_item_id = Column(Integer, primary_key=True, autoincrement=True)
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
    unit_price = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)

    # Relationships
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", lazy="selectin")

    def __repr__(self):
        return f"<OrderItem(id={self.order_item_id}, order_id={self.order_id}, product_id={self.product_id}, qty={self.quantity})>"
