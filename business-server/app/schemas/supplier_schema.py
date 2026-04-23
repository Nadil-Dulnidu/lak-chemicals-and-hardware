from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import Optional, List
from datetime import datetime
import uuid


def _validate_and_normalize_contact_number(contact_number: str) -> str:
    """Validate Sri Lanka phone number format (exactly 10 digits)."""
    cleaned = "".join(ch for ch in contact_number.strip() if ch.isdigit())
    if len(cleaned) != 10:
        raise ValueError("Contact number must contain exactly 10 digits")
    return cleaned


class SupplierBase(BaseModel):
    """Base supplier schema with common fields"""

    name: str = Field(..., min_length=1, max_length=255, description="Supplier name")
    contact_person: Optional[str] = Field(
        None, max_length=255, description="Contact person name"
    )
    contact_number: str = Field(
        ..., min_length=1, max_length=50, description="Contact phone number"
    )
    email: EmailStr = Field(..., description="Supplier email address")
    address: Optional[str] = Field(None, description="Supplier address")


class SupplierCreate(SupplierBase):
    """Schema for creating a new supplier"""

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        return v.lower().strip()

    @field_validator("contact_number")
    @classmethod
    def validate_contact_number(cls, v):
        return _validate_and_normalize_contact_number(v)


class SupplierUpdate(BaseModel):
    """Schema for updating a supplier (all fields optional)"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    contact_person: Optional[str] = Field(None, max_length=255)
    contact_number: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if v is not None:
            return v.lower().strip()
        return v

    @field_validator("contact_number")
    @classmethod
    def validate_contact_number(cls, v):
        if v is None:
            return v
        return _validate_and_normalize_contact_number(v)


class SupplierResponse(SupplierBase):
    """Schema for supplier response"""

    id: str = Field(..., description="Supplier UUID")
    created_at: datetime = Field(..., description="Creation timestamp")
    last_purchase_date: Optional[datetime] = Field(
        None, description="Last purchase date"
    )
    is_active: bool = Field(..., description="Active status")

    class Config:
        from_attributes = True


class SupplierWithProductsResponse(SupplierResponse):
    """Schema for supplier response with associated products"""

    product_count: int = Field(..., description="Number of products supplied")
    product_ids: List[str] = Field(
        default_factory=list, description="List of product UUIDs"
    )


class SupplierListResponse(BaseModel):
    """Schema for paginated supplier list response"""

    suppliers: List[SupplierResponse]
    total: int
    skip: int
    limit: int
    has_more: bool


class SupplierFilterParams(BaseModel):
    """Schema for supplier filtering parameters"""

    is_active: Optional[bool] = Field(True, description="Filter by active status")
    search: Optional[str] = Field(
        None, description="Search in name, email, contact person"
    )
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=500, description="Maximum records to return")


class SupplierProductLink(BaseModel):
    """Schema for linking supplier to product"""

    product_id: str = Field(..., description="Product UUID to link")
    supply_price: Optional[float] = Field(
        None, gt=0, description="Price at which supplier provides this product"
    )

    @field_validator("supply_price")
    @classmethod
    def validate_supply_price(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Supply price must be greater than 0")
        return round(v, 2) if v is not None else v


class SupplierProductUnlink(BaseModel):
    """Schema for unlinking supplier from product"""

    product_id: str = Field(..., description="Product UUID to unlink")


class SupplierProductResponse(BaseModel):
    """Schema for supplier-product relationship response"""

    supplier_id: str
    product_id: str
    supply_price: Optional[float]
    created_at: datetime
    last_supplied_date: Optional[datetime]


class ProductSupplierInfo(BaseModel):
    """Schema for product information with supplier details"""

    product_id: str
    product_name: str
    supply_price: Optional[float]
    last_supplied_date: Optional[datetime]


class SupplierDetailResponse(SupplierResponse):
    """Detailed supplier response with products"""

    products: List[ProductSupplierInfo] = Field(default_factory=list)
