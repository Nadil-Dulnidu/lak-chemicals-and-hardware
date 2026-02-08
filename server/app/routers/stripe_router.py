from fastapi import APIRouter, HTTPException, status

from app.services.payment_service import PaymentService
from app.schemas.payment_schema import PaymentIntentCreate, PaymentIntentResponse

router = APIRouter(prefix="/payments", tags=["Payments"])

# Initialize service
payment_service = PaymentService()


@router.post(
    "/create-payment-intent",
    response_model=PaymentIntentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Stripe payment intent",
    description="Create a payment intent for processing payments via Stripe",
)
async def create_payment_intent(
    payment_data: PaymentIntentCreate,
    # user_id: str = Depends(get_current_user)  # Add authentication later
):
    """
    Create a Stripe payment intent.

    - **amount**: Amount in cents (e.g., 10000 = LKR 100.00)

    Returns:
    - **client_secret**: Secret to be used on the client side to complete payment

    Example:
    ```json
    {
      "amount": 10000
    }
    ```

    Response:
    ```json
    {
      "client_secret": "pi_xxx_secret_xxx"
    }
    ```
    """
    user_id = "guest"  # Replace with actual user_id from authentication

    try:
        payment_intent = await payment_service.create_payment_intent(
            payment_data, user_id
        )

        if not payment_intent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create payment intent",
            )

        return payment_intent

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating payment intent: {str(e)}",
        )
