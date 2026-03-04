from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum


# ============= Enums =============


class OrderStatusEnum(str, Enum):
    """Order status enumeration for API validation"""

    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


# ============= Order Create Schemas =============


class OrderCreateFromCart(BaseModel):
    """
    Schema for creating an order from the user's cart.
    All cart items are automatically pulled from the cart.
    """

    cart_id: int = Field(..., description="Cart ID to convert into an order")
    payment_method: Optional[str] = Field(
        None, max_length=50, description="Payment method"
    )
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")

    # Shipping / contact information
    customer_name: Optional[str] = Field(
        None, max_length=100, description="Customer full name"
    )
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    address: Optional[str] = Field(None, max_length=255, description="Shipping address")
    city: Optional[str] = Field(None, max_length=100, description="City")


class OrderCreateFromQuotation(BaseModel):
    """
    Schema for creating an order from an approved quotation.
    All quotation items are automatically pulled from the quotation.
    """

    quotation_id: int = Field(
        ..., description="Approved Quotation ID to convert into an order"
    )
    payment_method: Optional[str] = Field(
        None, max_length=50, description="Payment method"
    )
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")

    # Shipping / contact information
    customer_name: Optional[str] = Field(
        None, max_length=100, description="Customer full name"
    )
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    address: Optional[str] = Field(None, max_length=255, description="Shipping address")
    city: Optional[str] = Field(None, max_length=100, description="City")


# ============= Order Update Schemas =============


class OrderUpdateStatus(BaseModel):
    """Schema for updating order status"""

    status: OrderStatusEnum = Field(..., description="New status")


# ============= Order Response Schemas =============


class OrderProductResponse(BaseModel):
    """Schema for order product item in response"""

    id: int
    product_id: str
    product_name: Optional[str] = None
    quantity: int
    unit_price: Decimal
    subtotal: Decimal

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    """
    Schema for order response.
    Includes source reference (cart_id or quotation_id) and
    a snapshot of ordered items via the order_products junction table.
    """

    order_id: int
    user_id: str
    status: str
    total_amount: Decimal
    payment_method: Optional[str] = None
    payment_status: str = "UNPAID"
    order_date: datetime
    completed_date: Optional[datetime] = None
    cancelled_date: Optional[datetime] = None
    notes: Optional[str] = None

    # Source entity references (one will be set, the other None)
    cart_id: Optional[int] = None
    quotation_id: Optional[int] = None

    # Shipping / contact snapshot
    customer_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None

    # Order items snapshot
    items: List[OrderProductResponse] = []

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    """Schema for paginated order list"""

    orders: List[OrderResponse]
    total: int
    skip: int
    limit: int
    has_more: bool


class OrderFilterParams(BaseModel):
    """Schema for order filtering parameters"""

    status: Optional[OrderStatusEnum] = Field(None, description="Filter by status")
    start_date: Optional[datetime] = Field(None, description="Filter from this date")
    end_date: Optional[datetime] = Field(None, description="Filter until this date")
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=500, description="Maximum records to return")

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v, info):
        if v and info.data.get("start_date") and v < info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v


class OrderSummaryResponse(BaseModel):
    """Schema for order summary"""

    order_id: int
    user_id: str
    status: str
    total_amount: Decimal
    order_date: datetime
    completed_date: Optional[datetime] = None
    cart_id: Optional[int] = None
    quotation_id: Optional[int] = None


# ============= Sales Schemas =============


class SaleResponse(BaseModel):
    """Schema for sale record response"""

    sale_id: int
    order_id: int
    product_id: str
    product_name: Optional[str] = None
    quantity: int
    revenue: Decimal
    sale_date: datetime

    class Config:
        from_attributes = True


class SalesListResponse(BaseModel):
    """Schema for paginated sales list"""

    sales: List[SaleResponse]
    total: int
    skip: int
    limit: int
    has_more: bool


class SalesFilterParams(BaseModel):
    """Schema for sales filtering parameters"""

    product_id: Optional[str] = Field(None, description="Filter by product UUID")
    start_date: Optional[datetime] = Field(None, description="Filter from this date")
    end_date: Optional[datetime] = Field(None, description="Filter until this date")
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=500, description="Maximum records to return")

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v, info):
        if v and info.data.get("start_date") and v < info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v


class SalesSummaryResponse(BaseModel):
    """Schema for sales summary/analytics"""

    total_sales: int
    total_revenue: Decimal
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
