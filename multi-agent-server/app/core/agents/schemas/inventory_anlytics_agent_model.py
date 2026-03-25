from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class InventorySummary(BaseModel):

    total_products: int = Field(
        ..., description="Total number of distinct products currently in the inventory."
    )

    total_stock_value: float = Field(
        ..., description="Total monetary value of all inventory items combined."
    )

    low_stock_count: int = Field(
        ..., description="Number of products that are below their reorder level."
    )

    out_of_stock_count: int = Field(
        ..., description="Number of products that are completely out of stock."
    )


class InventoryItem(BaseModel):

    product_id: str = Field(..., description="Unique identifier of the product.")

    product_name: str = Field(..., description="Name of the product.")

    category: str = Field(..., description="Category to which the product belongs.")

    current_stock: int = Field(
        ..., description="Current available stock quantity for the product."
    )

    reorder_level: int = Field(
        ...,
        description="Minimum stock threshold at which the product should be reordered.",
    )

    stock_value: float = Field(
        ..., description="Total monetary value of the current stock for this product."
    )

    status: str = Field(
        ...,
        description="Stock status of the product. Possible values: OK, LOW, OUT_OF_STOCK.",
    )


class CategoryInventorySummary(BaseModel):

    category: str = Field(..., description="Product category name.")

    total_products: int = Field(..., description="Number of products in this category.")

    total_stock_value: float = Field(
        ..., description="Total stock value for this category."
    )

    low_stock_count: int = Field(
        ..., description="Number of low stock products in this category."
    )


class InventoryInsight(BaseModel):

    critical_products: List[str] = Field(
        ...,
        description="List of product names that are either LOW or OUT_OF_STOCK and require immediate attention.",
    )

    highest_value_category: Optional[str] = Field(
        None, description="Category with the highest total stock value."
    )

    stock_health: str = Field(
        ...,
        description="Overall inventory health status. Possible values: healthy, moderate, critical.",
    )

    recommendation: str = Field(
        ...,
        description="Actionable recommendation for inventory management such as restocking, monitoring, or optimization.",
    )


class InventoryAnalyticsAgentResponse(BaseModel):

    report_type: str = Field(
        ..., description="Type of analytics report. Always 'INVENTORY' for this agent."
    )

    generated_at: datetime = Field(
        ..., description="Timestamp indicating when the inventory report was generated."
    )

    summary: InventorySummary = Field(
        ..., description="Overall summary of the inventory status."
    )

    items: List[InventoryItem] = Field(
        ..., description="Detailed inventory information for each product."
    )

    low_stock_items: List[InventoryItem] = Field(
        ...,
        description="List of products that are below reorder level or out of stock.",
    )

    category_summary: List[CategoryInventorySummary] = Field(
        ..., description="Aggregated inventory metrics grouped by category."
    )

    insights: InventoryInsight = Field(
        ...,
        description="AI-generated insights and recommendations based on inventory data.",
    )

    natural_language_summary: str = Field(
        ...,
        description="Human-readable explanation summarizing the overall inventory condition and key observations.",
    )
