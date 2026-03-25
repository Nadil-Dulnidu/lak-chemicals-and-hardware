from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class MovementTypeEnum(str, Enum):
    """Movement type enumeration for API validation"""

    IN = "IN"
    OUT = "OUT"


class StockMovementBase(BaseModel):
    """Base stock movement schema with common fields"""

    product_id: str = Field(..., description="Product UUID")
    movement_type: MovementTypeEnum = Field(..., description="Movement type (IN/OUT)")
    quantity: int = Field(..., gt=0, description="Quantity moved (must be positive)")
    reference: Optional[str] = Field(
        None, max_length=100, description="Reference number or note"
    )

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError("Quantity must be greater than 0")
        return v


class StockMovementCreate(StockMovementBase):
    """Schema for creating a new stock movement"""

    movement_date: Optional[datetime] = Field(
        None, description="Movement date (defaults to now)"
    )

    @field_validator("movement_date")
    @classmethod
    def validate_movement_date(cls, v):
        if v and v > datetime.utcnow():
            raise ValueError("Movement date cannot be in the future")
        return v


class StockMovementResponse(BaseModel):
    """Schema for stock movement response"""

    movement_id: int = Field(..., description="Movement ID")
    product_id: str = Field(..., description="Product UUID")
    product_name: Optional[str] = Field(None, description="Product name")
    movement_type: str = Field(..., description="Movement type (IN/OUT)")
    quantity: int = Field(..., description="Quantity moved")
    reference: Optional[str] = Field(None, description="Reference number or note")
    movement_date: datetime = Field(..., description="Movement timestamp")
    created_by: Optional[str] = Field(
        None, description="User who created this movement"
    )

    class Config:
        from_attributes = True


class StockMovementListResponse(BaseModel):
    """Schema for paginated stock movement list response"""

    movements: List[StockMovementResponse]
    total: int
    skip: int
    limit: int
    has_more: bool


class StockMovementFilterParams(BaseModel):
    """Schema for stock movement filtering parameters"""

    product_id: Optional[str] = Field(None, description="Filter by product UUID")
    movement_type: Optional[MovementTypeEnum] = Field(
        None, description="Filter by movement type"
    )
    start_date: Optional[datetime] = Field(
        None, description="Filter movements from this date"
    )
    end_date: Optional[datetime] = Field(
        None, description="Filter movements until this date"
    )
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=500, description="Maximum records to return")

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v, info):
        if v and info.data.get("start_date") and v < info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v


class InventoryLevelResponse(BaseModel):
    """Schema for current inventory level response"""

    product_id: str
    product_name: str
    current_stock: int
    total_in: int
    total_out: int
    last_movement_date: Optional[datetime]


class ReorderAlertResponse(BaseModel):
    """Schema for reorder alert response"""

    product_id: str
    product_name: str
    current_stock: int
    reorder_threshold: int
    quantity_needed: int
    priority: str  # critical, high, medium, low


class StockSummaryResponse(BaseModel):
    """Schema for stock summary statistics"""

    total_products: int
    total_stock_value: float
    low_stock_count: int
    out_of_stock_count: int
    total_movements_today: int
    total_in_today: int
    total_out_today: int


class BulkStockMovementCreate(BaseModel):
    """Schema for creating multiple stock movements at once"""

    movements: List[StockMovementCreate] = Field(..., min_length=1, max_length=100)

    @field_validator("movements")
    @classmethod
    def validate_movements(cls, v):
        if len(v) == 0:
            raise ValueError("At least one movement is required")
        if len(v) > 100:
            raise ValueError("Maximum 100 movements allowed per bulk operation")
        return v


class StockAdjustmentRequest(BaseModel):
    """Schema for adjusting stock to a specific level"""

    product_id: str = Field(..., description="Product UUID")
    target_quantity: int = Field(..., ge=0, description="Target stock quantity")
    reference: Optional[str] = Field(
        None, max_length=100, description="Reason for adjustment"
    )

    @field_validator("target_quantity")
    @classmethod
    def validate_target_quantity(cls, v):
        if v < 0:
            raise ValueError("Target quantity cannot be negative")
        return v
