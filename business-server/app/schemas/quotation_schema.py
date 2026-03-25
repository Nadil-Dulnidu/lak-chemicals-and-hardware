from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum


# ============= Quotation Schemas =============


class QuotationStatusEnum(str, Enum):
    """Quotation status enumeration for API validation"""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class QuotationItemBase(BaseModel):
    """Base quotation item schema"""

    product_id: str = Field(..., description="Product UUID")
    quantity: int = Field(..., gt=0, description="Quantity (must be positive)")

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError("Quantity must be greater than 0")
        return v


class QuotationItemCreate(QuotationItemBase):
    """Schema for creating quotation item"""

    pass


class QuotationItemResponse(BaseModel):
    """Schema for quotation item response"""

    quotation_item_id: int
    product_id: str
    product_name: Optional[str] = None
    quantity: int
    unit_price: Decimal
    subtotal: Decimal

    class Config:
        from_attributes = True


class QuotationCreate(BaseModel):
    """Schema for creating a quotation"""

    items: List[QuotationItemCreate] = Field(
        ..., min_length=1, description="List of items"
    )
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")

    @field_validator("items")
    @classmethod
    def validate_items(cls, v):
        if len(v) == 0:
            raise ValueError("At least one item is required")
        return v


class QuotationFromCart(BaseModel):
    """Schema for creating quotation from cart"""

    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")


class QuotationUpdateStatus(BaseModel):
    """Schema for updating quotation status"""

    status: QuotationStatusEnum = Field(..., description="New status")
    discount_amount: Optional[Decimal] = Field(
        None, ge=0, description="Discount amount (if approved)"
    )


class QuotationResponse(BaseModel):
    """Schema for quotation response"""

    quotation_id: int
    user_id: str
    status: str
    total_amount: Decimal
    discount_amount: Decimal = Field(default=0.00)
    created_at: datetime
    updated_at: Optional[datetime] = None
    notes: Optional[str] = None
    items: List[QuotationItemResponse]

    class Config:
        from_attributes = True


class QuotationListResponse(BaseModel):
    """Schema for paginated quotation list"""

    quotations: List[QuotationResponse]
    total: int
    skip: int
    limit: int
    has_more: bool


class QuotationFilterParams(BaseModel):
    """Schema for quotation filtering parameters"""

    status: Optional[QuotationStatusEnum] = Field(None, description="Filter by status")
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


class QuotationSummaryResponse(BaseModel):
    """Schema for quotation summary"""

    quotation_id: int
    user_id: str
    status: str
    total_amount: Decimal
    total_items: int
    created_at: datetime


class OrderFromQuotation(BaseModel):
    """Schema for creating order from quotation"""

    payment_method: Optional[str] = Field(None, description="Payment method")
    customer_name: Optional[str] = Field(None, description="Customer name")
    phone: Optional[str] = Field(None, description="Phone number")
    address: Optional[str] = Field(None, description="Shipping address")
    city: Optional[str] = Field(None, description="City")
    notes: Optional[str] = Field(None, description="Additional notes")
