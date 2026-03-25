from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from decimal import Decimal


class AddToCartParams(BaseModel):
    """Base cart item schema"""

    product_id: str = Field(..., description="Product UUID")
    quantity: int = Field(..., gt=0, description="Quantity (must be positive)")

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError("Quantity must be greater than 0")
        return v


class AddToCartParamsList(BaseModel):
    """List of cart items to add"""

    items: List[AddToCartParams]
    user_id: str = Field(..., description="User ID")


class CartItemResponse(BaseModel):
    """Schema for cart item response with product details"""

    cart_item_id: int
    product_id: str
    product_name: Optional[str] = None
    product_price: Optional[Decimal] = None
    quantity: int
    subtotal: Optional[Decimal] = None

    class Config:
        from_attributes = True


class AddToCartResponse(BaseModel):
    """Schema for cart response"""

    cart_id: int
    user_id: str
    items: List[CartItemResponse]
    total_items: int
    total_amount: Decimal

    class Config:
        from_attributes = True
