import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select, delete, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from app.models.order_model import Order, OrderProduct
from app.models.cart_model import Cart, CartItem
from app.models.quotation_model import Quotation, QuotationItem
from app.models.sale_model import Sale
from app.models.product_model import Product
from app.models.Inventory_model import StockMovement
from app.constants import OrderStatus, MovementType, PaymentStatus, QuotationStatus
from app.config.logging import get_logger, create_owasp_log_context


class OrderRepository:
    """
    Singleton repository for Order CRUD operations.
    Orders are created from a Cart or an approved Quotation.
    No OrderItems table — items are sourced from the origin entity.
    """

    _instance: Optional["OrderRepository"] = None
    _logger = None

    def __new__(cls):
        """Singleton pattern implementation"""
        if cls._instance is None:
            cls._instance = super(OrderRepository, cls).__new__(cls)
            cls._logger = get_logger(__name__)
            cls._logger.info(
                "OrderRepository singleton instance created",
                extra=create_owasp_log_context(
                    user="system",
                    action="repository_initialization",
                    location="OrderRepository.__new__",
                ),
            )
        return cls._instance

    # ──────────────────────────────────────────────────────────────────────
    # CREATE FROM CART
    # ──────────────────────────────────────────────────────────────────────

    async def create_from_cart(
        self, session: AsyncSession, order_data: Dict[str, Any]
    ) -> Optional[Order]:
        """
        Create an order from the user's cart.

        Validates stock for every cart item, calculates the total, then
        creates the Order row linked to the cart.  The cart itself is NOT
        cleared here — the service layer or a dedicated cart-clear step
        should handle that after a successful commit.

        Args:
            session   : AsyncSession
            order_data: {
                user_id, cart_id,
                payment_method?, notes?,
                customer_name?, phone?, address?, city?
            }

        Returns:
            Created Order or None on failure
        """
        try:
            cart_id = order_data["cart_id"]
            user_id = order_data["user_id"]

            # ── Load cart with items ──────────────────────────────────────
            cart_result = await session.execute(
                select(Cart)
                .where(Cart.cart_id == cart_id)
                .options(selectinload(Cart.cart_items).selectinload(CartItem.product))
            )
            cart = cart_result.scalar_one_or_none()

            if not cart:
                raise ValueError(f"Cart {cart_id} not found")

            if not cart.cart_items:
                raise ValueError("Cart is empty — cannot create order")

            # ── Validate stock & calculate total ──────────────────────────
            total_amount = Decimal("0.00")
            for cart_item in cart.cart_items:
                product = cart_item.product
                if not product:
                    raise ValueError(
                        f"Product not found for cart item {cart_item.cart_item_id}"
                    )
                if product.stock_qty < cart_item.quantity:
                    raise ValueError(
                        f"Insufficient stock for '{product.name}'. "
                        f"Available: {product.stock_qty}, Requested: {cart_item.quantity}"
                    )
                total_amount += Decimal(str(product.price)) * cart_item.quantity

            # ── Create Order ──────────────────────────────────────────────
            order = Order(
                user_id=user_id,
                cart_id=cart_id,
                quotation_id=None,
                status=OrderStatus.PENDING,
                total_amount=total_amount,
                payment_method=order_data.get("payment_method"),
                notes=order_data.get("notes"),
                customer_name=order_data.get("customer_name"),
                phone=order_data.get("phone"),
                address=order_data.get("address"),
                city=order_data.get("city"),
            )
            session.add(order)
            await session.flush()  # Get order_id before adding items

            # ── Snapshot items into order_products ─────────────────────────
            for cart_item in cart.cart_items:
                product = cart_item.product
                unit_price = Decimal(str(product.price))
                session.add(
                    OrderProduct(
                        order_id=order.order_id,
                        product_id=cart_item.product_id,
                        quantity=cart_item.quantity,
                        unit_price=unit_price,
                        subtotal=unit_price * cart_item.quantity,
                    )
                )

            await session.commit()
            await session.refresh(order)

            self._logger.info(
                f"Order {order.order_id} created from cart {cart_id} for user {user_id}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="create_order_from_cart_success",
                    location="OrderRepository.create_from_cart",
                ),
            )
            return order

        except ValueError:
            await session.rollback()
            raise

        except SQLAlchemyError as e:
            await session.rollback()
            self._logger.error(
                f"DB error creating order from cart: {e}",
                extra=create_owasp_log_context(
                    user="system",
                    action="create_order_from_cart_db_error",
                    location="OrderRepository.create_from_cart",
                ),
            )
            return None

    # ──────────────────────────────────────────────────────────────────────
    # CREATE FROM QUOTATION
    # ──────────────────────────────────────────────────────────────────────

    async def create_from_quotation(
        self, session: AsyncSession, order_data: Dict[str, Any]
    ) -> Optional[Order]:
        """
        Create an order from an APPROVED quotation.

        Validates that the quotation is approved, checks stock for every
        quotation item, then creates the Order row linked to the quotation.

        Args:
            session   : AsyncSession
            order_data: {
                user_id, quotation_id,
                payment_method?, notes?,
                customer_name?, phone?, address?, city?
            }

        Returns:
            Created Order or None on failure
        """
        try:
            quotation_id = order_data["quotation_id"]
            user_id = order_data["user_id"]

            # ── Load quotation with items ─────────────────────────────────
            quot_result = await session.execute(
                select(Quotation)
                .where(Quotation.quotation_id == quotation_id)
                .options(
                    selectinload(Quotation.quotation_items).selectinload(
                        QuotationItem.product
                    )
                )
            )
            quotation = quot_result.scalar_one_or_none()

            if not quotation:
                raise ValueError(f"Quotation {quotation_id} not found")

            if quotation.status != QuotationStatus.APPROVED:
                raise ValueError(
                    f"Quotation {quotation_id} is not approved "
                    f"(current status: {quotation.status.value})"
                )

            if not quotation.quotation_items:
                raise ValueError("Quotation has no items — cannot create order")

            # ── Validate stock ────────────────────────────────────────────
            for q_item in quotation.quotation_items:
                product = q_item.product
                if not product:
                    raise ValueError(
                        f"Product not found for quotation item {q_item.quotation_item_id}"
                    )
                if product.stock_qty < q_item.quantity:
                    raise ValueError(
                        f"Insufficient stock for '{product.name}'. "
                        f"Available: {product.stock_qty}, Requested: {q_item.quantity}"
                    )

            # Use quotation total (already includes discount)
            total_amount = Decimal(str(quotation.total_amount))

            # ── Create Order ──────────────────────────────────────────────
            order = Order(
                user_id=user_id,
                cart_id=None,
                quotation_id=quotation_id,
                status=OrderStatus.PENDING,
                total_amount=total_amount,
                payment_method=order_data.get("payment_method"),
                notes=order_data.get("notes") or quotation.notes,
                customer_name=order_data.get("customer_name"),
                phone=order_data.get("phone"),
                address=order_data.get("address"),
                city=order_data.get("city"),
            )
            session.add(order)
            await session.flush()  # Get order_id before adding items

            # ── Snapshot items into order_products ─────────────────────────
            for q_item in quotation.quotation_items:
                session.add(
                    OrderProduct(
                        order_id=order.order_id,
                        product_id=q_item.product_id,
                        quantity=q_item.quantity,
                        unit_price=q_item.unit_price,
                        subtotal=q_item.subtotal,
                    )
                )

            await session.commit()
            await session.refresh(order)

            self._logger.info(
                f"Order {order.order_id} created from quotation {quotation_id} for user {user_id}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="create_order_from_quotation_success",
                    location="OrderRepository.create_from_quotation",
                ),
            )
            return order

        except ValueError:
            await session.rollback()
            raise

        except SQLAlchemyError as e:
            await session.rollback()
            self._logger.error(
                f"DB error creating order from quotation: {e}",
                extra=create_owasp_log_context(
                    user="system",
                    action="create_order_from_quotation_db_error",
                    location="OrderRepository.create_from_quotation",
                ),
            )
            return None

    # ──────────────────────────────────────────────────────────────────────
    # READ
    # ──────────────────────────────────────────────────────────────────────

    async def get_by_id(self, session: AsyncSession, order_id: int) -> Optional[Order]:
        """Get order by ID (with source entity eager-loaded)."""
        try:
            result = await session.execute(
                select(Order).where(Order.order_id == order_id)
            )
            order = result.scalar_one_or_none()

            if order:
                self._logger.info(
                    f"Order retrieved: {order_id}",
                    extra=create_owasp_log_context(
                        user="system",
                        action="get_order_by_id_success",
                        location="OrderRepository.get_by_id",
                    ),
                )
            return order

        except SQLAlchemyError as e:
            self._logger.error(
                f"DB error retrieving order {order_id}: {e}",
                extra=create_owasp_log_context(
                    user="system",
                    action="get_order_by_id_db_error",
                    location="OrderRepository.get_by_id",
                ),
            )
            return None

    async def get_user_orders(
        self, session: AsyncSession, user_id: str, skip: int = 0, limit: int = 100
    ) -> List[Order]:
        """Get all orders for a user, newest first."""
        try:
            result = await session.execute(
                select(Order)
                .where(Order.user_id == user_id)
                .offset(skip)
                .limit(limit)
                .order_by(desc(Order.order_date))
            )
            orders = result.scalars().all()

            self._logger.info(
                f"Retrieved {len(orders)} orders for user {user_id}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="get_user_orders_success",
                    location="OrderRepository.get_user_orders",
                ),
            )
            return list(orders)

        except SQLAlchemyError as e:
            self._logger.error(
                f"DB error retrieving user orders: {e}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="get_user_orders_db_error",
                    location="OrderRepository.get_user_orders",
                ),
            )
            return []

    # ──────────────────────────────────────────────────────────────────────
    # STATUS UPDATE
    # ──────────────────────────────────────────────────────────────────────

    async def update_status(
        self, session: AsyncSession, order_id: int, status: OrderStatus, user_id: str
    ) -> Optional[Order]:
        """
        Update order status.
        On SHIPPED: marks the order as shipped.
        On DELIVERED: deducts stock and records sales from the source entity.
        """
        try:
            result = await session.execute(
                select(Order).where(Order.order_id == order_id)
            )
            order = result.scalar_one_or_none()

            if not order:
                self._logger.warning(
                    f"Order not found for status update: {order_id}",
                    extra=create_owasp_log_context(
                        user=user_id,
                        action="update_order_status_not_found",
                        location="OrderRepository.update_status",
                    ),
                )
                return None

            old_status = order.status
            if old_status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
                raise ValueError(f"Cannot change status of {old_status.value} order")

            order.status = status

            if status == OrderStatus.SHIPPED:
                pass  # Awaiting delivery — no stock changes yet

            elif status == OrderStatus.DELIVERED:
                order.completed_date = order.completed_date or datetime.utcnow()
                await self._process_order_completion(session, order, user_id)

            elif status == OrderStatus.CANCELLED:
                order.cancelled_date = datetime.utcnow()

            await session.commit()
            await session.refresh(order)

            self._logger.info(
                f"Order status updated: {order_id} ({old_status.value} → {status.value})",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="update_order_status_success",
                    location="OrderRepository.update_status",
                ),
            )
            return order

        except ValueError:
            await session.rollback()
            raise

        except SQLAlchemyError as e:
            await session.rollback()
            self._logger.error(
                f"DB error updating order status: {e}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="update_order_status_db_error",
                    location="OrderRepository.update_status",
                ),
            )
            return None

    async def _process_order_completion(
        self, session: AsyncSession, order: Order, user_id: str
    ) -> None:
        """
        On completion: deduct stock and record sales for every item
        in the order_products junction table.
        """
        # ── Read items from order_products (always available) ──────────────
        if not order.order_products:
            self._logger.warning(
                f"Order {order.order_id} has no order_products — skipping completion processing",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="process_order_completion_no_items",
                    location="OrderRepository._process_order_completion",
                ),
            )
            return

        for op in order.order_products:
            # Load the product to update stock
            product = op.product
            if not product:
                product_result = await session.execute(
                    select(Product).where(Product.id == op.product_id)
                )
                product = product_result.scalar_one_or_none()

            if not product:
                self._logger.warning(
                    f"Product {op.product_id} not found — skipping stock deduction",
                    extra=create_owasp_log_context(
                        user=user_id,
                        action="process_order_completion_product_missing",
                        location="OrderRepository._process_order_completion",
                    ),
                )
                continue

            # Deduct stock
            product.stock_qty -= op.quantity

            # Record stock movement
            session.add(
                StockMovement(
                    product_id=op.product_id,
                    movement_type=MovementType.OUT,
                    quantity=op.quantity,
                    reference=f"Order #{order.order_id}",
                    created_by=user_id,
                )
            )

            # Record sale
            session.add(
                Sale(
                    order_id=order.order_id,
                    product_id=op.product_id,
                    quantity=op.quantity,
                    revenue=op.subtotal,
                    sale_date=datetime.utcnow(),
                )
            )

            self._logger.info(
                f"Stock updated & sale recorded — product {op.product_id}: "
                f"-{op.quantity} units",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="process_order_completion",
                    location="OrderRepository._process_order_completion",
                ),
            )

    # ──────────────────────────────────────────────────────────────────────
    # FILTER / COUNT
    # ──────────────────────────────────────────────────────────────────────

    async def filter_orders(
        self,
        session: AsyncSession,
        user_id: Optional[str],
        filters: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
    ) -> List[Order]:
        """Filter orders by user/status/date range."""
        try:
            query = select(Order)
            conditions = []

            if user_id:
                conditions.append(Order.user_id == user_id)
            if filters.get("status"):
                status = filters["status"]
                if isinstance(status, str):
                    status = OrderStatus[status]
                conditions.append(Order.status == status)
            if filters.get("start_date"):
                conditions.append(Order.order_date >= filters["start_date"])
            if filters.get("end_date"):
                conditions.append(Order.order_date <= filters["end_date"])

            if conditions:
                query = query.where(and_(*conditions))

            query = query.offset(skip).limit(limit).order_by(desc(Order.order_date))
            result = await session.execute(query)
            orders = result.scalars().all()

            self._logger.info(
                f"Filtered orders: {len(orders)} results",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="filter_orders_success",
                    location="OrderRepository.filter_orders",
                ),
            )
            return list(orders)

        except SQLAlchemyError as e:
            self._logger.error(
                f"DB error filtering orders: {e}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="filter_orders_db_error",
                    location="OrderRepository.filter_orders",
                ),
            )
            return []

    async def count_orders(
        self,
        session: AsyncSession,
        user_id: Optional[str],
        filters: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Count orders matching the given filters."""
        try:
            query = select(func.count(Order.order_id))
            conditions = []

            if user_id:
                conditions.append(Order.user_id == user_id)

            if filters:
                if filters.get("status"):
                    status = filters["status"]
                    if isinstance(status, str):
                        status = OrderStatus[status]
                    conditions.append(Order.status == status)
                if filters.get("start_date"):
                    conditions.append(Order.order_date >= filters["start_date"])
                if filters.get("end_date"):
                    conditions.append(Order.order_date <= filters["end_date"])

            if conditions:
                query = query.where(and_(*conditions))

            result = await session.execute(query)
            return result.scalar() or 0

        except SQLAlchemyError as e:
            self._logger.error(
                f"DB error counting orders: {e}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="count_orders_db_error",
                    location="OrderRepository.count_orders",
                ),
            )
            return 0

    # ──────────────────────────────────────────────────────────────────────
    # DELETE
    # ──────────────────────────────────────────────────────────────────────

    async def delete(self, session: AsyncSession, order_id: int) -> bool:
        """Delete an order (only PENDING or CANCELLED allowed)."""
        try:
            result = await session.execute(
                select(Order).where(Order.order_id == order_id)
            )
            order = result.scalar_one_or_none()

            if not order:
                return False

            if order.status in [OrderStatus.DELIVERED]:
                raise ValueError("Cannot delete completed orders")

            stmt = delete(Order).where(Order.order_id == order_id)
            del_result = await session.execute(stmt)
            await session.commit()

            if del_result.rowcount == 0:
                return False

            self._logger.info(
                f"Order deleted: {order_id}",
                extra=create_owasp_log_context(
                    user="system",
                    action="delete_order_success",
                    location="OrderRepository.delete",
                ),
            )
            return True

        except ValueError:
            await session.rollback()
            raise

        except SQLAlchemyError as e:
            await session.rollback()
            self._logger.error(
                f"DB error deleting order: {e}",
                extra=create_owasp_log_context(
                    user="system",
                    action="delete_order_db_error",
                    location="OrderRepository.delete",
                ),
            )
            return False

    # ──────────────────────────────────────────────────────────────────────
    # PAYMENT STATUS
    # ──────────────────────────────────────────────────────────────────────

    async def update_payment_status(
        self, session: AsyncSession, order_id: int, payment_status: PaymentStatus
    ) -> Optional[Order]:
        """Update payment status for an order."""
        try:
            result = await session.execute(
                select(Order).where(Order.order_id == order_id)
            )
            order = result.scalar_one_or_none()

            if not order:
                return None

            order.payment_status = payment_status
            await session.commit()
            await session.refresh(order)

            self._logger.info(
                f"Payment status updated for order {order_id}: {payment_status.value}",
                extra=create_owasp_log_context(
                    user="system",
                    action="update_payment_status_success",
                    location="OrderRepository.update_payment_status",
                ),
            )
            return order

        except SQLAlchemyError as e:
            await session.rollback()
            self._logger.error(
                f"DB error updating payment status: {e}",
                extra=create_owasp_log_context(
                    user="system",
                    action="update_payment_status_db_error",
                    location="OrderRepository.update_payment_status",
                ),
            )
            return None
