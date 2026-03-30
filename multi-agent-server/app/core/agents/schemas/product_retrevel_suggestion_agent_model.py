from pydantic import BaseModel, Field
from typing import List, Optional


from app.core.agents.constants import ProductRetrievalSuggestionAgentEnum


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


class ProductSuggestionAgentResponse(BaseModel):

    suggestions: List[SuggestedProduct] = Field(
        ..., description="List of suggested products based on user requirements."
    )

    total_products_considered: int = Field(
        ...,
        description="Total number of products retrieved from the database before filtering.",
    )

    filtered_products_count: int = Field(
        ..., description="Number of products returned after filtering and ranking."
    )

    availability_status: ProductRetrievalSuggestionAgentEnum = Field(
        ...,
        description="Overall availability status: 'AVAILABLE', 'NO_MATCH', 'OUT_OF_STOCK', 'NOT_SOLD'.",
    )

    message_to_user: str = Field(
        ...,
        description="Friendly message asking user if they want to proceed with purchasing or refine results.",
    )
