from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import enum


class ProductCategory(enum.Enum):
    """Product category enumeration for hardware and chemical products"""

    CHEMICALS = "chemicals"
    HARDWARE = "hardware"
    TOOLS = "tools"
    PAINTS = "paints"
    ELECTRICAL = "electrical"
    PLUMBING = "plumbing"
    BUILDING_MATERIALS = "building_materials"
    SAFETY_EQUIPMENT = "safety_equipment"
    OTHER = "other"


class ProductBase(BaseModel):
    """Base product schema with common fields"""

    name: str = Field(..., min_length=1, max_length=255, description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    brand: Optional[str] = Field(None, max_length=255, description="Product brand")
    category: Optional[ProductCategory] = Field(None, description="Product category")
    price: float = Field(..., gt=0, description="Product price (must be positive)")
    stock_qty: int = Field(
        ..., ge=0, description="Stock quantity (must be non-negative)"
    )
    reorder_level: int = Field(
        10, ge=0, description="Reorder level for low stock alerts"
    )
    image_url: Optional[str] = Field(
        None, max_length=500, description="Product image URL"
    )


class ProductResponse(ProductBase):
    """Schema for product response"""

    id: str = Field(..., description="Product UUID")
    created_at: datetime = Field(..., description="Creation timestamp")
    is_active: bool = Field(..., description="Active status")

    class Config:
        from_attributes = True


class ProductListToolResponse(BaseModel):
    """Schema for paginated product list response"""

    products: list[ProductResponse]
    total: int
    skip: int
    limit: int
    has_more: bool


class ProductListToolParams(BaseModel):
    """Schema for product list tool parameters"""

    skip: int = Field(0, ge=0, description="Number of items to skip")
    limit: int = Field(100, ge=1, le=1000, description="Number of items to return")
    include_inactive: bool = Field(False, description="Filter by active status")
