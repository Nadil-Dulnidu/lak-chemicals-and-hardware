from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal


class InventoryToolParams(BaseModel):
    """Parameters for generating inventory report"""

    category: Optional[str] = Field(None, description="Filter by product category")
    low_stock_only: bool = Field(False, description="Show only low stock products")


class InventoryToolItem(BaseModel):
    """Individual item in inventory report"""

    product_id: str
    product_name: str
    category: str
    current_stock: int
    reorder_level: int
    stock_value: Decimal
    status: str = Field(..., description="OK, LOW, OUT_OF_STOCK")


class InventoryToolResponse(BaseModel):
    """Complete inventory report data"""

    report_type: str = "INVENTORY"
    generated_at: datetime
    summary: Dict[str, Any] = Field(..., description="Overall inventory summary")
    items: List[InventoryToolItem] = Field(..., description="Product inventory details")
    low_stock_items: List[InventoryToolItem] = Field(
        ..., description="Products below reorder level"
    )
