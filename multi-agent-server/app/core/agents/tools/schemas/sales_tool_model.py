from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime


class SalesToolItem(BaseModel):
    """Individual item in sales report"""

    period: str = Field(..., description="Time period (date, week, month)")
    total_sales: int = Field(..., description="Number of sales")
    total_revenue: Decimal = Field(..., description="Total revenue")
    total_quantity: int = Field(..., description="Total quantity sold")


class SalesToolResponse(BaseModel):
    """Complete sales report data"""

    report_type: str = "SALES"
    start_date: datetime
    end_date: datetime
    summary: Dict[str, Any] = Field(..., description="Overall summary statistics")
    items: List[SalesToolItem] = Field(..., description="Detailed breakdown")
    product_breakdown: Optional[List[Dict[str, Any]]] = Field(
        None, description="Product-wise breakdown"
    )
    category_breakdown: Optional[List[Dict[str, Any]]] = Field(
        None, description="Category-wise breakdown"
    )


class SalesToolParams(BaseModel):
    """Parameters for generating sales report"""

    start_date: datetime = Field(..., description="Start date for report")
    end_date: datetime = Field(..., description="End date for report")
    product_id: Optional[str] = Field(None, description="Filter by product UUID")
    category: Optional[str] = Field(None, description="Filter by product category")
    group_by: Optional[str] = Field("day", description="Grouping: day, week, month")

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v, info):
        if v and info.data.get("start_date") and v < info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v
