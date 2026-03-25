from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal


class ProductPerformanceToolParams(BaseModel):
    """Parameters for generating product performance report"""

    start_date: datetime = Field(..., description="Start date for report")
    end_date: datetime = Field(..., description="End date for report")
    category: Optional[str] = Field(None, description="Filter by product category")
    top_n: int = Field(10, ge=1, le=100, description="Top N products to show")

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v, info):
        if v and info.data.get("start_date") and v < info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v


class ProductPerformanceToolItem(BaseModel):
    """Individual item in product performance report"""

    product_id: str
    product_name: str
    category: str
    total_quantity_sold: int
    total_revenue: Decimal
    number_of_orders: int
    average_order_quantity: Decimal


class ProductPerformanceToolResponse(BaseModel):
    """Complete product performance report data"""

    report_type: str = "PRODUCT_PERFORMANCE"
    start_date: datetime
    end_date: datetime
    summary: Dict[str, Any] = Field(..., description="Overall performance summary")
    top_products: List[ProductPerformanceToolItem] = Field(
        ..., description="Top performing products"
    )
    category_performance: List[Dict[str, Any]] = Field(
        ..., description="Category-wise performance"
    )
