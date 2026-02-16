from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum


# ============= Order Schemas =============


class OrderStatusEnum(str, Enum):
    """Order status enumeration for API validation"""

    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class OrderItemBase(BaseModel):
    """Base order item schema"""

    product_id: str = Field(..., description="Product UUID")
    quantity: int = Field(..., gt=0, description="Quantity (must be positive)")

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError("Quantity must be greater than 0")
        return v


class OrderItemCreate(OrderItemBase):
    """Schema for creating order item"""

    pass


class OrderItemResponse(BaseModel):
    """Schema for order item response"""

    order_item_id: int
    product_id: str
    product_name: Optional[str] = None
    quantity: int
    unit_price: Decimal
    subtotal: Decimal

    class Config:
        from_attributes = True


class OrderCreate(BaseModel):
    """Schema for creating an order directly"""

    items: List[OrderItemCreate] = Field(..., min_length=1, description="List of items")
    payment_method: Optional[str] = Field(
        None, max_length=50, description="Payment method"
    )
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")

    # Shipping Information
    customer_name: Optional[str] = Field(
        None, max_length=100, description="Customer full name"
    )
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    address: Optional[str] = Field(None, max_length=255, description="Shipping address")
    city: Optional[str] = Field(None, max_length=100, description="City")

    @field_validator("items")
    @classmethod
    def validate_items(cls, v):
        if len(v) == 0:
            raise ValueError("At least one item is required")
        return v


class OrderUpdateStatus(BaseModel):
    """Schema for updating order status"""

    status: OrderStatusEnum = Field(..., description="New status")


class OrderResponse(BaseModel):
    """Schema for order response"""

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
    items: List[OrderItemResponse]

    # Shipping Information
    customer_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None

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
    total_items: int
    order_date: datetime
    completed_date: Optional[datetime] = None


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
