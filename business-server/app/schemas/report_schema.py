from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum


# ============= Report Type Enums =============


class ReportTypeEnum(str, Enum):
    """Report type enumeration for API validation"""

    SALES = "SALES"
    INVENTORY = "INVENTORY"
    PRODUCT_PERFORMANCE = "PRODUCT_PERFORMANCE"
    LOW_STOCK = "LOW_STOCK"


# ============= Report Configuration Schemas =============


class ReportCreate(BaseModel):
    """Schema for creating a new report configuration"""

    report_name: str = Field(
        ..., min_length=1, max_length=100, description="Report name"
    )
    report_type: ReportTypeEnum = Field(..., description="Type of report")
    parameters: Optional[Dict[str, Any]] = Field(
        None, description="Report parameters (date range, filters, etc.)"
    )
    description: Optional[str] = Field(
        None, max_length=500, description="Report description"
    )


class ReportUpdate(BaseModel):
    """Schema for updating report configuration"""

    report_name: Optional[str] = Field(
        None, min_length=1, max_length=100, description="Report name"
    )
    parameters: Optional[Dict[str, Any]] = Field(
        None, description="Updated report parameters"
    )
    description: Optional[str] = Field(
        None, max_length=500, description="Report description"
    )


class ReportResponse(BaseModel):
    """Schema for report configuration response"""

    report_id: int
    report_name: str
    report_type: str
    parameters: Optional[Dict[str, Any]] = None
    created_by: str
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    """Schema for paginated report list"""

    reports: List[ReportResponse]
    total: int
    skip: int
    limit: int
    has_more: bool


# ============= Report Generation Parameters =============


class SalesReportParams(BaseModel):
    """Parameters for generating sales report"""

    start_date: datetime = Field(..., description="Start date for report")
    end_date: datetime = Field(..., description="End date for report")
    product_id: Optional[str] = Field(None, description="Filter by product UUID")
    category: Optional[str] = Field(None, description="Filter by product category")
    group_by: Optional[str] = Field("day", description="Grouping: day, week, month")

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v, info):
        if v and info.data.get("start_date") and v <= info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v


class InventoryReportParams(BaseModel):
    """Parameters for generating inventory report"""

    category: Optional[str] = Field(None, description="Filter by product category")
    low_stock_only: bool = Field(False, description="Show only low stock products")


class ProductPerformanceParams(BaseModel):
    """Parameters for generating product performance report"""

    start_date: datetime = Field(..., description="Start date for report")
    end_date: datetime = Field(..., description="End date for report")
    category: Optional[str] = Field(None, description="Filter by product category")
    top_n: int = Field(10, ge=1, le=100, description="Top N products to show")

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v, info):
        if v and info.data.get("start_date") and v <= info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v


class LowStockReportParams(BaseModel):
    """Parameters for generating low stock report"""

    category: Optional[str] = Field(None, description="Filter by product category")
    threshold_percentage: int = Field(
        20, ge=0, le=100, description="Stock level threshold percentage"
    )


class RunReportParams(BaseModel):
    """Optional parameter overrides when running a saved report"""

    start_date: Optional[datetime] = Field(None, description="Override start date")
    end_date: Optional[datetime] = Field(None, description="Override end date")
    category: Optional[str] = Field(None, description="Override category filter")
    product_id: Optional[str] = Field(None, description="Override product filter")
    group_by: Optional[str] = Field(None, description="Override grouping")
    top_n: Optional[int] = Field(None, description="Override top N")
    threshold_percentage: Optional[int] = Field(None, description="Override threshold")
    low_stock_only: Optional[bool] = Field(None, description="Override low stock filter")

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v, info):
        if v and info.data.get("start_date") and v <= info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v


# ============= Report Data Schemas =============


class SalesReportItem(BaseModel):
    """Individual item in sales report"""

    period: str = Field(..., description="Time period (date, week, month)")
    total_sales: int = Field(..., description="Number of sales")
    total_revenue: Decimal = Field(..., description="Total revenue")
    total_quantity: int = Field(..., description="Total quantity sold")


class SalesReportData(BaseModel):
    """Complete sales report data"""

    report_type: str = "SALES"
    start_date: datetime
    end_date: datetime
    summary: Dict[str, Any] = Field(..., description="Overall summary statistics")
    items: List[SalesReportItem] = Field(..., description="Detailed breakdown")
    product_breakdown: Optional[List[Dict[str, Any]]] = Field(
        None, description="Product-wise breakdown"
    )
    category_breakdown: Optional[List[Dict[str, Any]]] = Field(
        None, description="Category-wise breakdown"
    )


class InventoryReportItem(BaseModel):
    """Individual item in inventory report"""

    product_id: str
    product_name: str
    category: str
    current_stock: int
    reorder_level: int
    stock_value: Decimal
    status: str = Field(..., description="OK, LOW, OUT_OF_STOCK")


class InventoryReportData(BaseModel):
    """Complete inventory report data"""

    report_type: str = "INVENTORY"
    generated_at: datetime
    summary: Dict[str, Any] = Field(..., description="Overall inventory summary")
    items: List[InventoryReportItem] = Field(
        ..., description="Product inventory details"
    )
    low_stock_items: List[InventoryReportItem] = Field(
        ..., description="Products below reorder level"
    )


class ProductPerformanceItem(BaseModel):
    """Individual item in product performance report"""

    product_id: str
    product_name: str
    category: str
    total_quantity_sold: int
    total_revenue: Decimal
    number_of_orders: int
    average_order_quantity: Decimal


class ProductPerformanceData(BaseModel):
    """Complete product performance report data"""

    report_type: str = "PRODUCT_PERFORMANCE"
    start_date: datetime
    end_date: datetime
    summary: Dict[str, Any] = Field(..., description="Overall performance summary")
    top_products: List[ProductPerformanceItem] = Field(
        ..., description="Top performing products"
    )
    category_performance: List[Dict[str, Any]] = Field(
        ..., description="Category-wise performance"
    )


class LowStockItem(BaseModel):
    """Individual item in low stock report"""

    product_id: str
    product_name: str
    category: str
    current_stock: int
    reorder_level: int
    stock_percentage: Decimal = Field(
        ..., description="Current stock as % of reorder level"
    )
    recommended_order_quantity: int


class LowStockReportData(BaseModel):
    """Complete low stock report data"""

    report_type: str = "LOW_STOCK"
    generated_at: datetime
    threshold_percentage: int
    summary: Dict[str, Any] = Field(..., description="Low stock summary")
    items: List[LowStockItem] = Field(..., description="Products requiring reorder")


# ============= Report Filter Parameters =============


class ReportFilterParams(BaseModel):
    """Schema for filtering saved reports"""

    report_type: Optional[ReportTypeEnum] = Field(
        None, description="Filter by report type"
    )
    created_by: Optional[str] = Field(None, description="Filter by creator")
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
