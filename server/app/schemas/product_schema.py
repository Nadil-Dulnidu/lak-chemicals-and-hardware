from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from app.constants.enums import ProductCategory as ProductCategoryEnum
from fastapi import UploadFile, File


class ProductBase(BaseModel):
    """Base product schema with common fields"""

    name: str = Field(..., min_length=1, max_length=255, description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    brand: Optional[str] = Field(None, max_length=255, description="Product brand")
    category: Optional[ProductCategoryEnum] = Field(
        None, description="Product category"
    )
    price: float = Field(..., gt=0, description="Product price (must be positive)")
    stock_qty: int = Field(
        ..., ge=0, description="Stock quantity (must be non-negative)"
    )
    image_url: Optional[str] = Field(
        None, max_length=255, description="Product image URL"
    )


class ProductCreate(ProductBase):
    """Schema for creating a new product"""

    @field_validator("price")
    @classmethod
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError("Price must be greater than 0")
        return round(v, 2)

    @field_validator("stock_qty")
    @classmethod
    def validate_stock(cls, v):
        if v < 0:
            raise ValueError("Stock quantity cannot be negative")
        return v


class ProductUpdate(BaseModel):
    """Schema for updating a product (all fields optional)"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    brand: Optional[str] = Field(None, max_length=255)
    category: Optional[ProductCategoryEnum] = None
    price: Optional[float] = Field(None, gt=0)
    stock_qty: Optional[int] = Field(None, ge=0)
    image_url: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None

    @field_validator("price")
    @classmethod
    def validate_price(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Price must be greater than 0")
        return round(v, 2) if v is not None else v

    @field_validator("stock_qty")
    @classmethod
    def validate_stock(cls, v):
        if v is not None and v < 0:
            raise ValueError("Stock quantity cannot be negative")
        return v


class ProductResponse(ProductBase):
    """Schema for product response"""

    id: str = Field(..., description="Product UUID")
    created_at: datetime = Field(..., description="Creation timestamp")
    is_active: bool = Field(..., description="Active status")

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Schema for paginated product list response"""

    products: list[ProductResponse]
    total: int
    skip: int
    limit: int
    has_more: bool


class ProductFilterParams(BaseModel):
    """Schema for product filtering parameters"""

    category: Optional[list[ProductCategoryEnum]] = Field(
        None, description="Filter by categories"
    )
    brand: Optional[str] = Field(None, description="Filter by brand")
    min_price: Optional[float] = Field(None, ge=0, description="Minimum price")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum price")
    min_stock: Optional[int] = Field(None, ge=0, description="Minimum stock quantity")
    max_stock: Optional[int] = Field(None, ge=0, description="Maximum stock quantity")
    is_active: Optional[bool] = Field(True, description="Filter by active status")
    search: Optional[str] = Field(None, description="Search in name/description")
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=500, description="Maximum records to return")


class LowStockAlert(ProductResponse):
    """Schema for low stock alert response"""

    restock_needed: int = Field(..., description="Quantity needed to reach threshold")
    priority: str = Field(..., description="Alert priority (high/medium/low)")
