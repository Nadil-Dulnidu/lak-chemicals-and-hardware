from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal


class ProductToAdd(BaseModel):
    product_id: str = Field(..., description="Product UUID to be added to the cart.")
    quantity: int = Field(1, gt=0, description="Quantity of the product to add.")


class CartAgentResponse(BaseModel):
    products_to_add: List[ProductToAdd] = Field(
        default_factory=list,
        description="List of products selected to be added to the cart in a single batch.",
    )

    cart_updated: bool = Field(
        ..., description="Indicates whether the cart was successfully updated."
    )

    total_items: Optional[int] = Field(
        None,
        description="Total number of items currently in the cart after the update.",
    )

    total_amount: Optional[Decimal] = Field(
        None, description="Total cart value after the update."
    )

    message_to_user: str = Field(
        ..., description="User-friendly response message describing the cart result."
    )
