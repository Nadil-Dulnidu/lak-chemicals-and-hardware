from pydantic import BaseModel, Field


class PaymentIntentCreate(BaseModel):
    """Schema for creating a payment intent"""

    amount: int = Field(
        ..., gt=0, description="Amount in cents (e.g., 10000 = LKR 100.00)"
    )


class PaymentIntentResponse(BaseModel):
    """Schema for payment intent response"""

    client_secret: str = Field(..., description="Client secret for Stripe payment")
