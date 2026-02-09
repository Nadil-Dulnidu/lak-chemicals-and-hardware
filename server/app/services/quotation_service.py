from typing import Optional, List
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.repository.quotation_repo import QuotationRepository
from app.repository.cart_repo import CartRepository
from app.repository.product_repo import ProductRepository
from app.constants import QuotationStatus
from app.schemas.quotation_schema import (
    QuotationCreate,
    QuotationFromCart,
    QuotationUpdateStatus,
    QuotationResponse,
    QuotationListResponse,
    QuotationFilterParams,
    QuotationItemResponse,
)
from app.config.logging import get_logger, create_owasp_log_context


class QuotationService:
    """
    Service layer for Quotation business logic.
    Handles validation, business rules, orchestration, and data transformation.
    """

    def __init__(self):
        self.repo = QuotationRepository()
        self.cart_repo = CartRepository()
        self.product_repo = ProductRepository()
        self._logger = get_logger(__name__)

    async def create_quotation(
        self,
        session: AsyncSession,
        user_id: str,
        quotation_data: QuotationCreate,
    ) -> Optional[QuotationResponse]:
        """
        Create a new quotation.

        Args:
            session: Database session
            user_id: User ID
            quotation_data: Quotation data with items

        Returns:
            QuotationResponse or None if creation fails
        """
        try:
            self._logger.info(
                f"Creating quotation for user: {user_id}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="create_quotation",
                    location="QuotationService.create_quotation",
                ),
            )

            # Prepare quotation data
            quotation_dict = {
                "user_id": user_id,
                "items": [item.model_dump() for item in quotation_data.items],
                "notes": quotation_data.notes,
            }

            # Create quotation
            quotation = await self.repo.create(session, quotation_dict)

            if quotation:
                self._logger.info(
                    f"Quotation created successfully: {quotation.quotation_id}",
                    extra=create_owasp_log_context(
                        user=user_id,
                        action="create_quotation_success",
                        location="QuotationService.create_quotation",
                    ),
                )

                return await self._to_response(quotation)

            return None

        except ValueError as e:
            self._logger.error(
                f"Validation error creating quotation: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="create_quotation_validation_error",
                    location="QuotationService.create_quotation",
                ),
            )
            raise

        except Exception as e:
            self._logger.error(
                f"Service error creating quotation: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="create_quotation_error",
                    location="QuotationService.create_quotation",
                ),
            )
            raise

    async def create_quotation_from_cart(
        self,
        session: AsyncSession,
        user_id: str,
        quotation_data: QuotationFromCart,
    ) -> Optional[QuotationResponse]:
        """
        Create quotation from user's cart.

        Args:
            session: Database session
            user_id: User ID
            quotation_data: Quotation data (notes only)

        Returns:
            QuotationResponse or None if creation fails
        """
        try:
            self._logger.info(
                f"Creating quotation from cart for user: {user_id}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="create_quotation_from_cart",
                    location="QuotationService.create_quotation_from_cart",
                ),
            )

            # Get cart
            cart = await self.cart_repo.get_cart_with_items(session, user_id)

            if not cart or not cart.cart_items:
                raise ValueError("Cart is empty")

            # Convert cart items to quotation items
            items = []
            for cart_item in cart.cart_items:
                items.append(
                    {
                        "product_id": str(cart_item.product_id),
                        "quantity": cart_item.quantity,
                    }
                )

            # Prepare quotation data
            quotation_dict = {
                "user_id": user_id,
                "items": items,
                "notes": quotation_data.notes,
            }

            # Create quotation
            quotation = await self.repo.create(session, quotation_dict)

            if quotation:
                # Clear cart after successful quotation creation
                await self.cart_repo.clear_cart(session, user_id)

                self._logger.info(
                    f"Quotation created from cart: {quotation.quotation_id}",
                    extra=create_owasp_log_context(
                        user=user_id,
                        action="create_quotation_from_cart_success",
                        location="QuotationService.create_quotation_from_cart",
                    ),
                )

                return await self._to_response(quotation)

            return None

        except ValueError as e:
            self._logger.error(
                f"Validation error creating quotation from cart: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="create_quotation_from_cart_validation_error",
                    location="QuotationService.create_quotation_from_cart",
                ),
            )
            raise

        except Exception as e:
            self._logger.error(
                f"Service error creating quotation from cart: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="create_quotation_from_cart_error",
                    location="QuotationService.create_quotation_from_cart",
                ),
            )
            raise

    async def get_quotation(
        self, session: AsyncSession, quotation_id: int, user_id: str
    ) -> Optional[QuotationResponse]:
        """
        Get quotation by ID.

        Args:
            session: Database session
            quotation_id: Quotation ID
            user_id: User ID (for authorization)

        Returns:
            QuotationResponse or None if not found
        """
        try:
            quotation = await self.repo.get_by_id(session, quotation_id)

            if not quotation:
                return None

            # Verify user owns this quotation
            if quotation.user_id != user_id:
                self._logger.warning(
                    f"Unauthorized access attempt to quotation {quotation_id} by user {user_id}",
                    extra=create_owasp_log_context(
                        user=user_id,
                        action="get_quotation_unauthorized",
                        location="QuotationService.get_quotation",
                    ),
                )
                return None

            return await self._to_response(quotation)

        except Exception as e:
            self._logger.error(
                f"Service error getting quotation: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="get_quotation_error",
                    location="QuotationService.get_quotation",
                ),
            )
            return None

    async def get_user_quotations(
        self,
        session: AsyncSession,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> QuotationListResponse:
        """
        Get all quotations for a user.

        Args:
            session: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            QuotationListResponse with quotations
        """
        try:
            quotations = await self.repo.get_user_quotations(
                session, user_id, skip, limit
            )
            total = await self.repo.count_quotations(session, user_id)

            quotation_responses = []
            for quotation in quotations:
                response = await self._to_response(quotation)
                if response:
                    quotation_responses.append(response)

            return QuotationListResponse(
                quotations=quotation_responses,
                total=total,
                skip=skip,
                limit=limit,
                has_more=skip + len(quotations) < total,
            )

        except Exception as e:
            self._logger.error(
                f"Service error getting user quotations: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="get_user_quotations_error",
                    location="QuotationService.get_user_quotations",
                ),
            )
            return QuotationListResponse(
                quotations=[], total=0, skip=skip, limit=limit, has_more=False
            )

    async def get_all_quotations(
        self,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
    ) -> QuotationListResponse:
        """
        Get all quotations (admin function).

        Args:
            session: Database session
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            QuotationListResponse with all quotations
        """
        try:
            # Pass None as user_id to get all quotations
            quotations = await self.repo.filter_quotations(
                session, None, {}, skip, limit
            )
            total = await self.repo.count_quotations(session, None, {})

            quotation_responses = []
            for quotation in quotations:
                response = await self._to_response(quotation)
                if response:
                    quotation_responses.append(response)

            return QuotationListResponse(
                quotations=quotation_responses,
                total=total,
                skip=skip,
                limit=limit,
                has_more=skip + len(quotations) < total,
            )

        except Exception as e:
            self._logger.error(
                f"Service error getting all quotations: {str(e)}",
                extra=create_owasp_log_context(
                    user="admin",
                    action="get_all_quotations_error",
                    location="QuotationService.get_all_quotations",
                ),
            )
            return QuotationListResponse(
                quotations=[], total=0, skip=skip, limit=limit, has_more=False
            )

    async def update_quotation_status(
        self,
        session: AsyncSession,
        quotation_id: int,
        status_data: QuotationUpdateStatus,
        user_id: str,
    ) -> Optional[QuotationResponse]:
        """
        Update quotation status.

        Args:
            session: Database session
            quotation_id: Quotation ID
            status_data: New status
            user_id: User ID (for logging)

        Returns:
            QuotationResponse or None if update fails
        """
        try:
            # Convert string enum to QuotationStatus
            status = QuotationStatus[status_data.status.value]

            self._logger.info(
                f"Updating quotation {quotation_id} status to {status.value}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="update_quotation_status",
                    location="QuotationService.update_quotation_status",
                ),
            )

            quotation = await self.repo.update_status(session, quotation_id, status)

            if quotation:
                self._logger.info(
                    f"Quotation status updated successfully: {quotation_id}",
                    extra=create_owasp_log_context(
                        user=user_id,
                        action="update_quotation_status_success",
                        location="QuotationService.update_quotation_status",
                    ),
                )

                return await self._to_response(quotation)

            return None

        except Exception as e:
            self._logger.error(
                f"Service error updating quotation status: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="update_quotation_status_error",
                    location="QuotationService.update_quotation_status",
                ),
            )
            raise

    async def filter_quotations(
        self,
        session: AsyncSession,
        user_id: str,
        filter_params: QuotationFilterParams,
    ) -> QuotationListResponse:
        """
        Filter quotations based on criteria.

        Args:
            session: Database session
            user_id: User ID
            filter_params: Filter parameters

        Returns:
            QuotationListResponse with filtered quotations
        """
        try:
            # Convert Pydantic model to dict for repository
            filters = filter_params.model_dump(
                exclude={"skip", "limit"}, exclude_unset=True
            )

            quotations = await self.repo.filter_quotations(
                session, user_id, filters, filter_params.skip, filter_params.limit
            )

            total = await self.repo.count_quotations(session, user_id, filters)

            quotation_responses = []
            for quotation in quotations:
                response = await self._to_response(quotation)
                if response:
                    quotation_responses.append(response)

            return QuotationListResponse(
                quotations=quotation_responses,
                total=total,
                skip=filter_params.skip,
                limit=filter_params.limit,
                has_more=filter_params.skip + len(quotations) < total,
            )

        except Exception as e:
            self._logger.error(
                f"Service error filtering quotations: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="filter_quotations_error",
                    location="QuotationService.filter_quotations",
                ),
            )
            return QuotationListResponse(
                quotations=[],
                total=0,
                skip=filter_params.skip,
                limit=filter_params.limit,
                has_more=False,
            )

    async def delete_quotation(
        self, session: AsyncSession, quotation_id: int, user_id: str
    ) -> bool:
        """
        Delete a quotation.

        Args:
            session: Database session
            quotation_id: Quotation ID
            user_id: User ID (for authorization)

        Returns:
            True if successful
        """
        try:
            # Verify user owns this quotation
            quotation = await self.repo.get_by_id(session, quotation_id)

            if not quotation:
                return False

            if quotation.user_id != user_id:
                self._logger.warning(
                    f"Unauthorized delete attempt on quotation {quotation_id} by user {user_id}",
                    extra=create_owasp_log_context(
                        user=user_id,
                        action="delete_quotation_unauthorized",
                        location="QuotationService.delete_quotation",
                    ),
                )
                return False

            self._logger.info(
                f"Deleting quotation: {quotation_id}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="delete_quotation",
                    location="QuotationService.delete_quotation",
                ),
            )

            return await self.repo.delete(session, quotation_id)

        except Exception as e:
            self._logger.error(
                f"Service error deleting quotation: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="delete_quotation_error",
                    location="QuotationService.delete_quotation",
                ),
            )
            return False

    async def _to_response(self, quotation) -> QuotationResponse:
        """
        Convert Quotation model to QuotationResponse schema.

        Args:
            quotation: Quotation model instance

        Returns:
            QuotationResponse schema
        """
        # Build quotation items
        items = []
        for item in quotation.quotation_items:
            product = item.product
            items.append(
                QuotationItemResponse(
                    quotation_item_id=item.quotation_item_id,
                    product_id=str(item.product_id),
                    product_name=product.name if product else None,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    subtotal=item.subtotal,
                )
            )

        return QuotationResponse(
            quotation_id=quotation.quotation_id,
            user_id=quotation.user_id,
            status=quotation.status.value,
            total_amount=quotation.total_amount,
            created_at=quotation.created_at,
            updated_at=quotation.updated_at,
            notes=quotation.notes,
            items=items,
        )
