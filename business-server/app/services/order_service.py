from typing import Optional, List
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.repository.order_repo import OrderRepository
from app.constants import OrderStatus, PaymentStatus
from app.schemas.order_schema import (
    OrderCreateFromCart,
    OrderCreateFromQuotation,
    OrderUpdateStatus,
    OrderResponse,
    OrderProductResponse,
    OrderListResponse,
    OrderFilterParams,
)
from app.config.logging import get_logger, create_owasp_log_context


class OrderService:
    """
    Service layer for Order business logic.
    Orders can be created from a Cart or an approved Quotation.
    """

    def __init__(self):
        self.repo = OrderRepository()
        self._logger = get_logger(__name__)

    # ──────────────────────────────────────────────────────────────────────
    # CREATE
    # ──────────────────────────────────────────────────────────────────────

    async def create_order_from_cart(
        self,
        session: AsyncSession,
        user_id: str,
        order_data: OrderCreateFromCart,
    ) -> Optional[OrderResponse]:
        """
        Create a new order from the user's cart.

        Args:
            session   : Database session
            user_id   : Authenticated user ID
            order_data: OrderCreateFromCart payload

        Returns:
            OrderResponse or None if creation fails
        """
        try:
            self._logger.info(
                f"Creating order from cart {order_data.cart_id} for user {user_id}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="create_order_from_cart",
                    location="OrderService.create_order_from_cart",
                ),
            )

            normalized_phone = self._validate_and_normalize_phone(order_data.phone)

            order_dict = {
                "user_id": user_id,
                "cart_id": order_data.cart_id,
                "payment_method": order_data.payment_method,
                "notes": order_data.notes,
                "customer_name": order_data.customer_name,
                "phone": normalized_phone,
                "address": order_data.address,
                "city": order_data.city,
            }

            order = await self.repo.create_from_cart(session, order_dict)

            if order:
                self._logger.info(
                    f"Order {order.order_id} created from cart {order_data.cart_id}",
                    extra=create_owasp_log_context(
                        user=user_id,
                        action="create_order_from_cart_success",
                        location="OrderService.create_order_from_cart",
                    ),
                )
                return self._to_response(order)

            return None

        except ValueError:
            raise
        except Exception as e:
            self._logger.error(
                f"Service error creating order from cart: {e}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="create_order_from_cart_error",
                    location="OrderService.create_order_from_cart",
                ),
            )
            raise

    async def create_order_from_quotation(
        self,
        session: AsyncSession,
        user_id: str,
        order_data: OrderCreateFromQuotation,
    ) -> Optional[OrderResponse]:
        """
        Create a new order from an approved quotation.

        Args:
            session   : Database session
            user_id   : Authenticated user ID
            order_data: OrderCreateFromQuotation payload

        Returns:
            OrderResponse or None if creation fails
        """
        try:
            self._logger.info(
                f"Creating order from quotation {order_data.quotation_id} for user {user_id}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="create_order_from_quotation",
                    location="OrderService.create_order_from_quotation",
                ),
            )

            normalized_phone = self._validate_and_normalize_phone(order_data.phone)

            order_dict = {
                "user_id": user_id,
                "quotation_id": order_data.quotation_id,
                "payment_method": order_data.payment_method,
                "notes": order_data.notes,
                "customer_name": order_data.customer_name,
                "phone": normalized_phone,
                "address": order_data.address,
                "city": order_data.city,
            }

            order = await self.repo.create_from_quotation(session, order_dict)

            if order:
                self._logger.info(
                    f"Order {order.order_id} created from quotation {order_data.quotation_id}",
                    extra=create_owasp_log_context(
                        user=user_id,
                        action="create_order_from_quotation_success",
                        location="OrderService.create_order_from_quotation",
                    ),
                )
                return self._to_response(order)

            return None

        except ValueError:
            raise
        except Exception as e:
            self._logger.error(
                f"Service error creating order from quotation: {e}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="create_order_from_quotation_error",
                    location="OrderService.create_order_from_quotation",
                ),
            )
            raise

    # ──────────────────────────────────────────────────────────────────────
    # READ
    # ──────────────────────────────────────────────────────────────────────

    async def get_order(
        self, session: AsyncSession, order_id: int, user_id: str
    ) -> Optional[OrderResponse]:
        """Get order by ID (user-scoped)."""
        try:
            order = await self.repo.get_by_id(session, order_id)
            if not order:
                return None

            if order.user_id != user_id:
                self._logger.warning(
                    f"Unauthorized access to order {order_id} by user {user_id}",
                    extra=create_owasp_log_context(
                        user=user_id,
                        action="get_order_unauthorized",
                        location="OrderService.get_order",
                    ),
                )
                return None

            return self._to_response(order)

        except Exception as e:
            self._logger.error(
                f"Service error getting order: {e}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="get_order_error",
                    location="OrderService.get_order",
                ),
            )
            return None

    async def get_order_by_id_admin(
        self, session: AsyncSession, order_id: int
    ) -> Optional[OrderResponse]:
        """Get order by ID without user auth check (admin use)."""
        try:
            order = await self.repo.get_by_id(session, order_id)
            if not order:
                return None
            return self._to_response(order)
        except Exception as e:
            self._logger.error(
                f"Service error getting order (admin): {e}",
                extra=create_owasp_log_context(
                    user="admin",
                    action="get_order_admin_error",
                    location="OrderService.get_order_by_id_admin",
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
        """Get all orders for a user."""
        try:
            orders = await self.repo.get_user_orders(session, user_id, skip, limit)
            total = await self.repo.count_orders(session, user_id)

            return OrderListResponse(
                orders=[self._to_response(o) for o in orders],
                total=total,
                skip=skip,
                limit=limit,
                has_more=skip + len(orders) < total,
            )
        except Exception as e:
            self._logger.error(
                f"Service error getting user orders: {e}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="get_user_orders_error",
                    location="OrderService.get_user_orders",
                ),
            )
            return OrderListResponse(
                orders=[], total=0, skip=skip, limit=limit, has_more=False
            )

    async def get_all_orders(
        self,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
    ) -> OrderListResponse:
        """Get all orders (admin function)."""
        try:
            orders = await self.repo.filter_orders(session, None, {}, skip, limit)
            total = await self.repo.count_orders(session, None, {})

            return OrderListResponse(
                orders=[self._to_response(o) for o in orders],
                total=total,
                skip=skip,
                limit=limit,
                has_more=skip + len(orders) < total,
            )
        except Exception as e:
            self._logger.error(
                f"Service error getting all orders: {e}",
                extra=create_owasp_log_context(
                    user="admin",
                    action="get_all_orders_error",
                    location="OrderService.get_all_orders",
                ),
            )
            return OrderListResponse(
                orders=[], total=0, skip=skip, limit=limit, has_more=False
            )

    # ──────────────────────────────────────────────────────────────────────
    # UPDATE
    # ──────────────────────────────────────────────────────────────────────

    async def update_order_status(
        self,
        session: AsyncSession,
        order_id: int,
        status_data: OrderUpdateStatus,
        user_id: str,
    ) -> Optional[OrderResponse]:
        """Update order status."""
        try:
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
                return self._to_response(order)
            return None

        except ValueError:
            raise
        except Exception as e:
            self._logger.error(
                f"Service error updating order status: {e}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="update_order_status_error",
                    location="OrderService.update_order_status",
                ),
            )
            raise

    async def update_payment_status(
        self,
        session: AsyncSession,
        order_id: int,
        payment_status: PaymentStatus,
    ) -> Optional["OrderResponse"]:
        """Update payment status for an order."""
        try:
            order = await self.repo.update_payment_status(
                session, order_id, payment_status
            )
            if not order:
                return None
            return self._to_response(order)
        except Exception as e:
            self._logger.error(
                f"Service error updating payment status: {e}",
                extra=create_owasp_log_context(
                    user="system",
                    action="update_payment_status_error",
                    location="OrderService.update_payment_status",
                ),
            )
            return None

    async def filter_orders(
        self,
        session: AsyncSession,
        user_id: str,
        filter_params: OrderFilterParams,
    ) -> OrderListResponse:
        """Filter orders based on criteria."""
        try:
            filters = filter_params.model_dump(
                exclude={"skip", "limit"}, exclude_unset=True
            )

            orders = await self.repo.filter_orders(
                session, user_id, filters, filter_params.skip, filter_params.limit
            )
            total = await self.repo.count_orders(session, user_id, filters)

            return OrderListResponse(
                orders=[self._to_response(o) for o in orders],
                total=total,
                skip=filter_params.skip,
                limit=filter_params.limit,
                has_more=filter_params.skip + len(orders) < total,
            )
        except Exception as e:
            self._logger.error(
                f"Service error filtering orders: {e}",
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

    # ──────────────────────────────────────────────────────────────────────
    # DELETE
    # ──────────────────────────────────────────────────────────────────────

    async def delete_order(
        self, session: AsyncSession, order_id: int, user_id: str
    ) -> bool:
        """Delete an order (user-scoped, only PENDING/CANCELLED)."""
        try:
            order = await self.repo.get_by_id(session, order_id)
            if not order:
                return False

            if order.user_id != user_id:
                self._logger.warning(
                    f"Unauthorized delete attempt on order {order_id} by {user_id}",
                    extra=create_owasp_log_context(
                        user=user_id,
                        action="delete_order_unauthorized",
                        location="OrderService.delete_order",
                    ),
                )
                return False

            return await self.repo.delete(session, order_id)

        except ValueError:
            raise
        except Exception as e:
            self._logger.error(
                f"Service error deleting order: {e}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="delete_order_error",
                    location="OrderService.delete_order",
                ),
            )
            return False

    # ──────────────────────────────────────────────────────────────────────
    # INTERNAL HELPERS
    # ──────────────────────────────────────────────────────────────────────

    def _validate_and_normalize_phone(self, phone: Optional[str]) -> Optional[str]:
        """Validate Sri Lanka phone number format (exactly 10 digits)."""
        if phone is None:
            return None

        stripped_phone = phone.strip()
        if not stripped_phone:
            return None

        normalized_phone = "".join(ch for ch in stripped_phone if ch.isdigit())
        if len(normalized_phone) != 10:
            raise ValueError("Phone number must contain exactly 10 digits")

        return normalized_phone

    def _to_response(self, order) -> OrderResponse:
        """Convert Order ORM model → OrderResponse Pydantic schema."""
        # Map order_products to item responses
        items = []
        for op in order.order_products or []:
            product_name = None
            if op.product:
                product_name = op.product.name
            items.append(
                OrderProductResponse(
                    id=op.id,
                    product_id=str(op.product_id),
                    product_name=product_name,
                    quantity=op.quantity,
                    unit_price=op.unit_price,
                    subtotal=op.subtotal,
                )
            )

        return OrderResponse(
            order_id=order.order_id,
            user_id=order.user_id,
            status=order.status.value,
            total_amount=order.total_amount,
            payment_method=order.payment_method,
            payment_status=(
                order.payment_status.value if order.payment_status else "UNPAID"
            ),
            order_date=order.order_date,
            completed_date=order.completed_date,
            cancelled_date=order.cancelled_date,
            notes=order.notes,
            cart_id=order.cart_id,
            quotation_id=order.quotation_id,
            customer_name=order.customer_name,
            phone=order.phone,
            address=order.address,
            city=order.city,
            items=items,
        )
