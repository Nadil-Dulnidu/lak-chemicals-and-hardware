from pydantic import BaseModel, Field
from typing import List, Optional


class SuggestedProduct(BaseModel):

    product_id: str = Field(..., description="Unique identifier of the product.")

    name: str = Field(..., description="Product name.")

    category: Optional[str] = Field(None, description="Product category.")

    price: float = Field(..., description="Product price.")

    stock_qty: int = Field(..., description="Available stock quantity.")

    short_reason: str = Field(
        ...,
        description="Short explanation why this product is suitable for the user's requirement.",
    )


class ProductGroup(BaseModel):

    category: str = Field(..., description="Category of products grouped together.")

    purpose: str = Field(
        ..., description="Why this category is needed based on user requirements."
    )

    products: List[SuggestedProduct] = Field(
        ..., description="List of suggested products for this category."
    )


class ProductSuggestionAgentResponse(BaseModel):

    suggestions: List[ProductGroup] = Field(
        ..., description="Grouped product suggestions based on user requirements."
    )

    total_products_considered: int = Field(
        ...,
        description="Total number of products retrieved from the database before filtering.",
    )

    filtered_products_count: int = Field(
        ..., description="Number of products returned after filtering and ranking."
    )

    availability_status: str = Field(
        ...,
        description="Overall availability status: 'available', 'no_match', 'out_of_stock', 'not_sold'.",
    )

    message_to_user: str = Field(
        ...,
        description="Friendly message asking user if they want to proceed with purchasing or refine results.",
    )
