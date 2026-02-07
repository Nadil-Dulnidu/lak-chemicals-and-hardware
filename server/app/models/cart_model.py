from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.utils.db import Base


class Cart(Base):
    """
    Model for shopping cart.
    Each user has one cart that contains multiple cart items.
    """

    __tablename__ = "carts"

    cart_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False, unique=True, index=True)

    # Relationship to CartItem
    cart_items = relationship(
        "CartItem",
        back_populates="cart",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self):
        return f"<Cart(id={self.cart_id}, user_id={self.user_id}, items={len(self.cart_items)})>"


class CartItem(Base):
    """
    Model for individual items in a shopping cart.
    Links cart to products with quantity information.
    """

    __tablename__ = "cart_items"

    cart_item_id = Column(Integer, primary_key=True, autoincrement=True)
    cart_id = Column(
        Integer,
        ForeignKey("carts.cart_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id = Column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quantity = Column(Integer, nullable=False, default=1)

    # Relationships
    cart = relationship("Cart", back_populates="cart_items")
    product = relationship("Product", lazy="selectin")

    def __repr__(self):
        return f"<CartItem(id={self.cart_item_id}, cart_id={self.cart_id}, product_id={self.product_id}, qty={self.quantity})>"
