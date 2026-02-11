from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
import stripe

from app.services.payment_service import PaymentService
from app.services.order_service import OrderService
from app.utils.db import get_async_session
from app.config.logging import get_logger, create_owasp_log_context


def get_config_value(*keys, default=None):
    """Lazy import to avoid circular dependency"""
    from app.config.config_loader import get_config_value as _get_config_value

    return _get_config_value(*keys, default=default)


logger = get_logger(__name__)

router = APIRouter(prefix="/payments", tags=["Payments"])

# Initialize services
payment_service = PaymentService()
order_service = OrderService()

# Frontend base URL for redirect
FRONTEND_URL = get_config_value("stripe", "frontend_url")


@router.post(
    "/create-payment-session/{order_id}",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create Stripe Checkout Session",
    description="Create a Stripe Checkout Session for an order with line items in LKR",
)
async def create_payment_session(
    order_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Create a Stripe Checkout Session for an order.

    - **order_id**: The ID of the order to create a payment session for.

    This endpoint will:
    - Fetch the order and its items from the database
    - Create Stripe line items for each product in the order
    - Set currency to LKR (Sri Lankan Rupees)
    - Set success and cancel redirect URLs

    Returns:
    - **checkout_url**: The Stripe Checkout URL to redirect the user to
    - **session_id**: The Stripe Session ID for reference
    """
    try:
        # Fetch the order using the admin method (no user_id filter)
        order = await order_service.get_order_by_id_admin(session, order_id)

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order {order_id} not found",
            )

        # Build Stripe line items from order items
        line_items = []
        for item in order.items:
            line_items.append(
                {
                    "price_data": {
                        "currency": "lkr",
                        "product_data": {
                            "name": item.product_name or f"Product {item.product_id}",
                        },
                        "unit_amount": int(
                            float(item.unit_price) * 100
                        ),  # Convert to cents
                    },
                    "quantity": item.quantity,
                }
            )

        # Create Stripe Checkout Session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            success_url=f"{FRONTEND_URL}/payment/success?order_id={order_id}&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{FRONTEND_URL}/payment/cancel?order_id={order_id}",
            metadata={
                "order_id": str(order_id),
            },
        )

        logger.info(
            f"Stripe Checkout Session created for order {order_id}: {checkout_session.id}",
            extra=create_owasp_log_context(
                user="system",
                action="create_payment_session_success",
                location="stripe_router.create_payment_session",
            ),
        )

        return {
            "checkout_url": checkout_session.url,
            "session_id": checkout_session.id,
        }

    except HTTPException:
        raise

    except stripe.error.StripeError as e:
        logger.error(
            f"Stripe error creating checkout session: {str(e)}",
            extra=create_owasp_log_context(
                user="system",
                action="create_payment_session_stripe_error",
                location="stripe_router.create_payment_session",
            ),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stripe error: {str(e)}",
        )

    except Exception as e:
        logger.error(
            f"Error creating payment session: {str(e)}",
            extra=create_owasp_log_context(
                user="system",
                action="create_payment_session_error",
                location="stripe_router.create_payment_session",
            ),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating payment session: {str(e)}",
        )
