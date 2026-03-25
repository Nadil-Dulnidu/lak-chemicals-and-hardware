import stripe
import os
from typing import Optional

from app.schemas.payment_schema import PaymentIntentCreate, PaymentIntentResponse
from app.config.logging import get_logger, create_owasp_log_context


def get_config_value(*keys, default=None):
    from app.config.config_loader import get_config_value as _get_config_value

    return _get_config_value(*keys, default=default)


class PaymentService:
    """
    Service layer for Stripe payment processing.
    Handles payment intent creation and management.
    """

    def __init__(self):
        self._logger = get_logger(__name__)
        # Set Stripe API key from environment variable
        stripe.api_key = get_config_value("stripe", "secret_key")

        if not stripe.api_key:
            self._logger.warning(
                "STRIPE_SECRET_KEY not found in environment variables",
                extra=create_owasp_log_context(
                    user="system",
                    action="stripe_init_warning",
                    location="PaymentService.__init__",
                ),
            )

    async def create_payment_intent(
        self, payment_data: PaymentIntentCreate, user_id: str = "guest"
    ) -> Optional[PaymentIntentResponse]:
        """
        Create a Stripe payment intent.

        Args:
            payment_data: Payment intent data with amount
            user_id: User ID for logging (optional)

        Returns:
            PaymentIntentResponse with client_secret or None if creation fails
        """
        try:
            self._logger.info(
                f"Creating payment intent for amount: {payment_data.amount}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="create_payment_intent",
                    location="PaymentService.create_payment_intent",
                ),
            )

            # Create payment intent with Stripe
            intent = stripe.PaymentIntent.create(
                amount=payment_data.amount,
                currency="lkr",  # Sri Lankan Rupee
            )

            self._logger.info(
                f"Payment intent created successfully: {intent.id}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="create_payment_intent_success",
                    location="PaymentService.create_payment_intent",
                ),
            )

            return PaymentIntentResponse(client_secret=intent.client_secret)

        except stripe.error.StripeError as e:
            self._logger.error(
                f"Stripe error creating payment intent: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="create_payment_intent_stripe_error",
                    location="PaymentService.create_payment_intent",
                ),
            )
            raise ValueError(f"Stripe error: {str(e)}")

        except Exception as e:
            self._logger.error(
                f"Service error creating payment intent: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="create_payment_intent_error",
                    location="PaymentService.create_payment_intent",
                ),
            )
            return None
