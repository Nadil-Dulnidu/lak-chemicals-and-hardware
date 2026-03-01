from sqlalchemy import Column, String, Integer, Numeric, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.constants import OrderStatus, PaymentStatus
from app.utils.db import Base


class Order(Base):
    """
    Model for customer orders.
    An order can be sourced either from:
      - A Cart   (cart_id is set,       quotation_id is NULL)
      - A Quotation (quotation_id is set, cart_id is NULL)

    Both FKs are nullable — only one will be set per order.
    OrderItems table has been removed; item details are derived
    from the source entity (Cart or Quotation) at creation time
    and stored as a denormalised snapshot in the Sale records.
    """

    __tablename__ = "orders"

    order_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False, index=True)

    # ── Source entity (mutually exclusive, both nullable) ──────────────────
    cart_id = Column(
        Integer,
        ForeignKey("carts.cart_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Source cart (set when order is created from cart)",
    )
    quotation_id = Column(
        Integer,
        ForeignKey("quotations.quotation_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Source quotation (set when order is created from approved quotation)",
    )

    # ── Order state ────────────────────────────────────────────────────────
    status = Column(
        Enum(OrderStatus),
        nullable=False,
        default=OrderStatus.PENDING,
        index=True,
    )
    total_amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(String(50), nullable=True)
    payment_status = Column(
        Enum(PaymentStatus),
        nullable=False,
        default=PaymentStatus.UNPAID,
        server_default="UNPAID",
        index=True,
    )
    order_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_date = Column(DateTime, nullable=True)
    cancelled_date = Column(DateTime, nullable=True)
    notes = Column(String(500), nullable=True)

    # ── Shipping / contact snapshot ────────────────────────────────────────
    customer_name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    address = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)

    # ── Relationships ──────────────────────────────────────────────────────
    cart = relationship("Cart", lazy="selectin")
    quotation = relationship("Quotation", lazy="selectin")

    def __repr__(self):
        source = (
            f"cart={self.cart_id}" if self.cart_id else f"quotation={self.quotation_id}"
        )
        return (
            f"<Order(id={self.order_id}, user_id={self.user_id}, "
            f"status={self.status.value}, total={self.total_amount}, {source})>"
        )
