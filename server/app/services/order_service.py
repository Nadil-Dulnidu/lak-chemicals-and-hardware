from typing import Optional, List
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.repository.order_repo import OrderRepository
from app.repository.quotation_repo import QuotationRepository
from app.repository.product_repo import ProductRepository
from app.constants import OrderStatus, QuotationStatus
from app.schemas.order_schema import (
    OrderCreate,
    OrderFromQuotation,
    OrderUpdateStatus,
    OrderResponse,
    OrderListResponse,
    OrderFilterParams,
    OrderItemResponse,
)
from app.config.logging import get_logger, create_owasp_log_context


class OrderService:
    """
    Service layer for Order business logic.
    Handles order creation, status management, and conversions.
    """

    def __init__(self):
        self.repo = OrderRepository()
        self.quotation_repo = QuotationRepository()
        self.product_repo = ProductRepository()
        self._logger = get_logger(__name__)

    async def create_order(
        self,
        session: AsyncSession,
        user_id: str,
        order_data: OrderCreate,
    ) -> Optional[OrderResponse]:
        """
        Create a new order directly.

        Args:
            session: Database session
            user_id: User ID
            order_data: Order data with items

        Returns:
            OrderResponse or None if creation fails
        """
        try:
            self._logger.info(
                f"Creating order for user: {user_id}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="create_order",
                    location="OrderService.create_order",
                ),
            )

            # Prepare order data
            order_dict = {
                "user_id": user_id,
                "items": [item.model_dump() for item in order_data.items],
                "payment_method": order_data.payment_method,
                "notes": order_data.notes,
            }

            # Create order
            order = await self.repo.create(session, order_dict)

            if order:
                self._logger.info(
                    f"Order created successfully: {order.order_id}",
                    extra=create_owasp_log_context(
                        user=user_id,
                        action="create_order_success",
                        location="OrderService.create_order",
                    ),
                )

                return await self._to_response(order)

            return None

        except ValueError as e:
            self._logger.error(
                f"Validation error creating order: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="create_order_validation_error",
                    location="OrderService.create_order",
                ),
            )
            raise

        except Exception as e:
            self._logger.error(
                f"Service error creating order: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="create_order_error",
                    location="OrderService.create_order",
                ),
            )
            raise

    async def create_order_from_quotation(
        self,
        session: AsyncSession,
        user_id: str,
        order_data: OrderFromQuotation,
    ) -> Optional[OrderResponse]:
        """
        Create order from approved quotation.

        Args:
            session: Database session
            user_id: User ID
            order_data: Order data with quotation_id

        Returns:
            OrderResponse or None if creation fails
        """
        try:
            self._logger.info(
                f"Creating order from quotation {order_data.quotation_id} for user: {user_id}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="create_order_from_quotation",
                    location="OrderService.create_order_from_quotation",
                ),
            )

            # Get quotation
            quotation = await self.quotation_repo.get_by_id(
                session, order_data.quotation_id
            )

            if not quotation:
                raise ValueError(f"Quotation not found: {order_data.quotation_id}")

            # Verify user owns this quotation
            if quotation.user_id != user_id:
                raise ValueError("Unauthorized access to quotation")

            # Verify quotation is approved
            if quotation.status != QuotationStatus.APPROVED:
                raise ValueError(
                    f"Quotation must be APPROVED. Current status: {quotation.status.value}"
                )

            # Convert quotation items to order items
            items = []
            for quotation_item in quotation.quotation_items:
                items.append(
                    {
                        "product_id": str(quotation_item.product_id),
                        "quantity": quotation_item.quantity,
                    }
                )

            # Prepare order data
            order_dict = {
                "user_id": user_id,
                "quotation_id": order_data.quotation_id,
                "items": items,
                "payment_method": order_data.payment_method,
                "notes": order_data.notes,
            }

            # Create order
            order = await self.repo.create(session, order_dict)

            if order:
                self._logger.info(
                    f"Order created from quotation: {order.order_id}",
                    extra=create_owasp_log_context(
                        user=user_id,
                        action="create_order_from_quotation_success",
                        location="OrderService.create_order_from_quotation",
                    ),
                )

                return await self._to_response(order)

            return None

        except ValueError as e:
            self._logger.error(
                f"Validation error creating order from quotation: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="create_order_from_quotation_validation_error",
                    location="OrderService.create_order_from_quotation",
                ),
            )
            raise

        except Exception as e:
            self._logger.error(
                f"Service error creating order from quotation: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="create_order_from_quotation_error",
                    location="OrderService.create_order_from_quotation",
                ),
            )
            raise

    async def get_order(
        self, session: AsyncSession, order_id: int, user_id: str
    ) -> Optional[OrderResponse]:
        """
        Get order by ID.

        Args:
            session: Database session
            order_id: Order ID
            user_id: User ID (for authorization)

        Returns:
            OrderResponse or None if not found
        """
        try:
            order = await self.repo.get_by_id(session, order_id)

            if not order:
                return None

            # Verify user owns this order
            if order.user_id != user_id:
                self._logger.warning(
                    f"Unauthorized access attempt to order {order_id} by user {user_id}",
                    extra=create_owasp_log_context(
                        user=user_id,
                        action="get_order_unauthorized",
                        location="OrderService.get_order",
                    ),
                )
                return None

            return await self._to_response(order)

        except Exception as e:
            self._logger.error(
                f"Service error getting order: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="get_order_error",
                    location="OrderService.get_order",
                ),
            )
            return None

    async def get_user_orders(
        self,
        session: AsyncSession,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> OrderListResponse:
        """
        Get all orders for a user.

        Args:
            session: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            OrderListResponse with orders
        """
        try:
            orders = await self.repo.get_user_orders(session, user_id, skip, limit)
            total = await self.repo.count_orders(session, user_id)

            order_responses = []
            for order in orders:
                response = await self._to_response(order)
                if response:
                    order_responses.append(response)

            return OrderListResponse(
                orders=order_responses,
                total=total,
                skip=skip,
                limit=limit,
                has_more=skip + len(orders) < total,
            )

        except Exception as e:
            self._logger.error(
                f"Service error getting user orders: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="get_user_orders_error",
                    location="OrderService.get_user_orders",
                ),
            )
            return OrderListResponse(
                orders=[], total=0, skip=skip, limit=limit, has_more=False
            )

    async def update_order_status(
        self,
        session: AsyncSession,
        order_id: int,
        status_data: OrderUpdateStatus,
        user_id: str,
    ) -> Optional[OrderResponse]:
        """
        Update order status.

        Args:
            session: Database session
            order_id: Order ID
            status_data: New status
            user_id: User ID (for logging)

        Returns:
            OrderResponse or None if update fails
        """
        try:
            # Convert string enum to OrderStatus
            status = OrderStatus[status_data.status.value]

            self._logger.info(
                f"Updating order {order_id} status to {status.value}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="update_order_status",
                    location="OrderService.update_order_status",
                ),
            )

            order = await self.repo.update_status(session, order_id, status, user_id)

            if order:
                self._logger.info(
                    f"Order status updated successfully: {order_id}",
                    extra=create_owasp_log_context(
                        user=user_id,
                        action="update_order_status_success",
                        location="OrderService.update_order_status",
                    ),
                )

                return await self._to_response(order)

            return None

        except ValueError as e:
            self._logger.error(
                f"Validation error updating order status: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="update_order_status_validation_error",
                    location="OrderService.update_order_status",
                ),
            )
            raise

        except Exception as e:
            self._logger.error(
                f"Service error updating order status: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="update_order_status_error",
                    location="OrderService.update_order_status",
                ),
            )
            raise

    async def filter_orders(
        self,
        session: AsyncSession,
        user_id: str,
        filter_params: OrderFilterParams,
    ) -> OrderListResponse:
        """
        Filter orders based on criteria.

        Args:
            session: Database session
            user_id: User ID
            filter_params: Filter parameters

        Returns:
            OrderListResponse with filtered orders
        """
        try:
            # Convert Pydantic model to dict for repository
            filters = filter_params.model_dump(
                exclude={"skip", "limit"}, exclude_unset=True
            )

            orders = await self.repo.filter_orders(
                session, user_id, filters, filter_params.skip, filter_params.limit
            )

            total = await self.repo.count_orders(session, user_id, filters)

            order_responses = []
            for order in orders:
                response = await self._to_response(order)
                if response:
                    order_responses.append(response)

            return OrderListResponse(
                orders=order_responses,
                total=total,
                skip=filter_params.skip,
                limit=filter_params.limit,
                has_more=filter_params.skip + len(orders) < total,
            )

        except Exception as e:
            self._logger.error(
                f"Service error filtering orders: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="filter_orders_error",
                    location="OrderService.filter_orders",
                ),
            )
            return OrderListResponse(
                orders=[],
                total=0,
                skip=filter_params.skip,
                limit=filter_params.limit,
                has_more=False,
            )

    async def delete_order(
        self, session: AsyncSession, order_id: int, user_id: str
    ) -> bool:
        """
        Delete an order.

        Args:
            session: Database session
            order_id: Order ID
            user_id: User ID (for authorization)

        Returns:
            True if successful
        """
        try:
            # Verify user owns this order
            order = await self.repo.get_by_id(session, order_id)

            if not order:
                return False

            if order.user_id != user_id:
                self._logger.warning(
                    f"Unauthorized delete attempt on order {order_id} by user {user_id}",
                    extra=create_owasp_log_context(
                        user=user_id,
                        action="delete_order_unauthorized",
                        location="OrderService.delete_order",
                    ),
                )
                return False

            self._logger.info(
                f"Deleting order: {order_id}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="delete_order",
                    location="OrderService.delete_order",
                ),
            )

            return await self.repo.delete(session, order_id)

        except ValueError as e:
            self._logger.error(
                f"Validation error deleting order: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="delete_order_validation_error",
                    location="OrderService.delete_order",
                ),
            )
            raise

        except Exception as e:
            self._logger.error(
                f"Service error deleting order: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="delete_order_error",
                    location="OrderService.delete_order",
                ),
            )
            return False

    async def _to_response(self, order) -> OrderResponse:
        """
        Convert Order model to OrderResponse schema.

        Args:
            order: Order model instance

        Returns:
            OrderResponse schema
        """
        # Build order items
        items = []
        for item in order.order_items:
            product = item.product
            items.append(
                OrderItemResponse(
                    order_item_id=item.order_item_id,
                    product_id=str(item.product_id),
                    product_name=product.name if product else None,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    subtotal=item.subtotal,
                )
            )

        return OrderResponse(
            order_id=order.order_id,
            user_id=order.user_id,
            quotation_id=order.quotation_id,
            status=order.status.value,
            total_amount=order.total_amount,
            payment_method=order.payment_method,
            order_date=order.order_date,
            completed_date=order.completed_date,
            cancelled_date=order.cancelled_date,
            notes=order.notes,
            items=items,
        )
