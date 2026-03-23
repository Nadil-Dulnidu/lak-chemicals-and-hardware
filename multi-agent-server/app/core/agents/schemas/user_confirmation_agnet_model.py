from pydantic import BaseModel, Field
from typing import List, Optional


class ConfirmationSelectedItem(BaseModel):
    product_id: Optional[str] = Field(
        None, description="Resolved product UUID if available."
    )
    product_name: Optional[str] = Field(
        None, description="Product name mentioned by the user."
    )
    reference: Optional[str] = Field(
        None, description="User reference like 'first item', 'second one'."
    )
    quantity: Optional[int] = Field(
        None, description="Quantity requested for this item."
    )


class UserConfirmationAgentResponse(BaseModel):

    confirmation_asked: bool = Field(
        ..., description="Whether the confirmation question has been asked."
    )

    is_user_answer_for_confirmation: bool = Field(
        ...,
        description="True if the current user message is answering the confirmation question.",
    )

    confirmed: Optional[bool] = Field(
        None, description="True = yes, False = no, None = not answered yet."
    )

    selection_mode: str = Field(
        ...,
        description="Selection mode: 'all', 'partial', 'single', 'one_each', 'none', 'unclear'.",
    )

    selected_items: List[ConfirmationSelectedItem] = Field(default_factory=list)

    apply_quantity_to_all: Optional[int] = Field(
        None, description="Quantity applied to all items if user says 'add 1 each'."
    )

    clarification_needed: bool = Field(
        ..., description="Whether clarification is still required."
    )

    clarification_question: Optional[str] = Field(
        None, description="Follow-up question if needed."
    )

    message_to_user: str = Field(..., description="Friendly response message.")
