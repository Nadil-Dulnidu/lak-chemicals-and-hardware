import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select, delete, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from app.models.order_model import Order, OrderItem
from app.models.sale_model import Sale
from app.models.product_model import Product
from app.models.Inventory_model import StockMovement
from app.constants import OrderStatus, MovementType
from app.config.logging import get_logger, create_owasp_log_context


class OrderRepository:
    """
    Singleton repository for Order CRUD operations.
    Handles order lifecycle, sales recording, and inventory synchronization.
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

    async def create(
        self, session: AsyncSession, order_data: Dict[str, Any]
    ) -> Optional[Order]:
        """
        Create a new order with items.

        Args:
            session: AsyncSession for database operations
            order_data: Dictionary containing order information
                - user_id: str
                - items: List[Dict] with product_id, quantity
                - quotation_id: Optional[int]
                - payment_method: Optional[str]
                - notes: Optional[str]

        Returns:
            Created Order object or None if creation fails
        """
        try:
            # Extract items from order_data
            items_data = order_data.pop("items", [])

            if not items_data:
                raise ValueError("At least one item is required")

            # Create order
            order = Order(
                user_id=order_data["user_id"],
                status=OrderStatus.PENDING,
                total_amount=Decimal("0.00"),
                payment_method=order_data.get("payment_method"),
                notes=order_data.get("notes"),
                customer_name=order_data.get("customer_name"),
                phone=order_data.get("phone"),
                address=order_data.get("address"),
                city=order_data.get("city"),
            )
            session.add(order)
            await session.flush()  # Get order_id

            # Create order items and calculate total
            total_amount = Decimal("0.00")

            for item_data in items_data:
                product_id = uuid.UUID(item_data["product_id"])
                quantity = item_data["quantity"]

                # Get product to get price and check stock
                product_result = await session.execute(
                    select(Product).where(Product.id == product_id)
                )
                product = product_result.scalar_one_or_none()

                if not product:
                    raise ValueError(f"Product not found: {product_id}")

                # Check stock availability
                if product.stock_qty < quantity:
                    raise ValueError(
                        f"Insufficient stock for product {product.name}. "
                        f"Available: {product.stock_qty}, Requested: {quantity}"
                    )

                # Calculate subtotal
                unit_price = Decimal(str(product.price))
                subtotal = unit_price * quantity

                # Create order item
                order_item = OrderItem(
                    order_id=order.order_id,
                    product_id=product_id,
                    quantity=quantity,
                    unit_price=unit_price,
                    subtotal=subtotal,
                )
                session.add(order_item)
                total_amount += subtotal

            # Update order total
            order.total_amount = total_amount

            await session.commit()

            # Re-fetch the order with eager loading to avoid lazy loading issues
            # This ensures product relationships are loaded within the async context
            result = await session.execute(
                select(Order)
                .where(Order.order_id == order.order_id)
                .options(
                    selectinload(Order.order_items).selectinload(OrderItem.product)
                )
            )
            order = result.scalar_one()

            self._logger.info(
                f"Order created: {order.order_id} for user {order.user_id}",
                extra=create_owasp_log_context(
                    user=order.user_id,
                    action="create_order_success",
                    location="OrderRepository.create",
                ),
            )

            return order

        except ValueError as e:
            await session.rollback()
            raise

        except SQLAlchemyError as e:
            await session.rollback()
            error_msg = f"Database error creating order: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="create_order_db_error",
                    location="OrderRepository.create",
                ),
            )
            return None

    async def get_by_id(self, session: AsyncSession, order_id: int) -> Optional[Order]:
        """
        Get order by ID with items.

        Args:
            session: AsyncSession for database operations
            order_id: Order ID

        Returns:
            Order object or None if not found
        """
        try:
            result = await session.execute(
                select(Order)
                .where(Order.order_id == order_id)
                .options(
                    selectinload(Order.order_items).selectinload(OrderItem.product)
                )
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
            error_msg = f"Database error retrieving order {order_id}: {str(e)}"
            self._logger.error(
                error_msg,
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
        """
        Get all orders for a user.

        Args:
            session: AsyncSession for database operations
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Order objects
        """
        try:
            query = (
                select(Order)
                .where(Order.user_id == user_id)
                .options(
                    selectinload(Order.order_items).selectinload(OrderItem.product)
                )
                .offset(skip)
                .limit(limit)
                .order_by(desc(Order.order_date))
            )

            result = await session.execute(query)
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
            error_msg = f"Database error retrieving user orders: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user=user_id,
                    action="get_user_orders_db_error",
                    location="OrderRepository.get_user_orders",
                ),
            )
            return []

    async def update_status(
        self, session: AsyncSession, order_id: int, status: OrderStatus, user_id: str
    ) -> Optional[Order]:
        """
        Update order status.
        Handles inventory updates and sales recording for COMPLETED status.

        Args:
            session: AsyncSession for database operations
            order_id: Order ID
            status: New status
            user_id: User ID for audit logging

        Returns:
            Updated Order or None if not found
        """
        try:
            result = await session.execute(
                select(Order)
                .where(Order.order_id == order_id)
                .options(
                    selectinload(Order.order_items).selectinload(OrderItem.product)
                )
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

            # Prevent status change if already completed or cancelled
            if old_status in [OrderStatus.COMPLETED, OrderStatus.CANCELLED]:
                raise ValueError(f"Cannot change status of {old_status.value} order")

            # Update status
            order.status = status

            # Handle COMPLETED status
            if status == OrderStatus.COMPLETED:
                order.completed_date = datetime.utcnow()

                # Update inventory and create sales records
                await self._process_order_completion(session, order, user_id)

            # Handle CANCELLED status
            elif status == OrderStatus.CANCELLED:
                order.cancelled_date = datetime.utcnow()

            await session.commit()
            await session.refresh(order)

            self._logger.info(
                f"Order status updated: {order_id} ({old_status.value} -> {status.value})",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="update_order_status_success",
                    location="OrderRepository.update_status",
                ),
            )

            return order

        except ValueError as e:
            await session.rollback()
            raise

        except SQLAlchemyError as e:
            await session.rollback()
            error_msg = f"Database error updating order status: {str(e)}"
            self._logger.error(
                error_msg,
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
        Process order completion: update inventory and create sales records.

        Args:
            session: AsyncSession for database operations
            order: Order object
            user_id: User ID for audit logging
        """
        for item in order.order_items:
            # Update product stock
            product_result = await session.execute(
                select(Product).where(Product.id == item.product_id)
            )
            product = product_result.scalar_one_or_none()

            if product:
                # Reduce stock
                product.stock_qty -= item.quantity

                # Create stock movement record
                stock_movement = StockMovement(
                    product_id=item.product_id,
                    movement_type=MovementType.OUT,
                    quantity=item.quantity,
                    reference=f"Order #{order.order_id}",
                    created_by=user_id,
                )
                session.add(stock_movement)

                # Create sales record
                sale = Sale(
                    order_id=order.order_id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    revenue=item.subtotal,
                    sale_date=datetime.utcnow(),
                )
                session.add(sale)

                self._logger.info(
                    f"Inventory updated and sale recorded for product {item.product_id}: -{item.quantity} units",
                    extra=create_owasp_log_context(
                        user=user_id,
                        action="process_order_completion",
                        location="OrderRepository._process_order_completion",
                    ),
                )

    async def filter_orders(
        self,
        session: AsyncSession,
        user_id: Optional[str],
        filters: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
    ) -> List[Order]:
        """
        Filter orders based on criteria.

        Args:
            session: AsyncSession for database operations
            user_id: User ID
            filters: Dictionary of filter criteria
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of filtered Order objects
        """
        try:
            query = select(Order)
            conditions = []

            if user_id:
                conditions.append(Order.user_id == user_id)

            # Status filter
            if "status" in filters and filters["status"]:
                status = filters["status"]
                if isinstance(status, str):
                    status = OrderStatus[status]
                conditions.append(Order.status == status)

            # Date range filter
            if "start_date" in filters and filters["start_date"]:
                conditions.append(Order.order_date >= filters["start_date"])

            if "end_date" in filters and filters["end_date"]:
                conditions.append(Order.order_date <= filters["end_date"])

            # Apply all conditions
            if conditions:
                query = query.where(and_(*conditions))

            # Apply pagination and ordering
            query = query.offset(skip).limit(limit).order_by(desc(Order.order_date))

            result = await session.execute(query)
            orders = result.scalars().all()

            self._logger.info(
                f"Filtered orders: {len(orders)} results (filters={filters})",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="filter_orders_success",
                    location="OrderRepository.filter_orders",
                ),
            )

            return list(orders)

        except SQLAlchemyError as e:
            error_msg = f"Database error filtering orders: {str(e)}"
            self._logger.error(
                error_msg,
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
        """
        Count total orders matching filters.

        Args:
            session: AsyncSession for database operations
            user_id: User ID
            filters: Optional filter criteria

        Returns:
            Total count of orders
        """
        try:
            query = select(func.count(Order.order_id))
            conditions = []

            if user_id:
                conditions.append(Order.user_id == user_id)

            if filters:
                if "status" in filters and filters["status"]:
                    status = filters["status"]
                    if isinstance(status, str):
                        status = OrderStatus[status]
                    conditions.append(Order.status == status)

                if "start_date" in filters and filters["start_date"]:
                    conditions.append(Order.order_date >= filters["start_date"])

                if "end_date" in filters and filters["end_date"]:
                    conditions.append(Order.order_date <= filters["end_date"])

            if conditions:
                query = query.where(and_(*conditions))

            result = await session.execute(query)
            count = result.scalar()

            return count or 0

        except SQLAlchemyError as e:
            error_msg = f"Database error counting orders: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user=user_id,
                    action="count_orders_db_error",
                    location="OrderRepository.count_orders",
                ),
            )
            return 0

    async def delete(self, session: AsyncSession, order_id: int) -> bool:
        """
        Delete an order (only if PENDING or CANCELLED).

        Args:
            session: AsyncSession for database operations
            order_id: Order ID to delete

        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            # Get order to check status
            result = await session.execute(
                select(Order).where(Order.order_id == order_id)
            )
            order = result.scalar_one_or_none()

            if not order:
                return False

            # Only allow deletion of PENDING or CANCELLED orders
            if order.status == OrderStatus.COMPLETED:
                raise ValueError("Cannot delete completed orders")

            stmt = delete(Order).where(Order.order_id == order_id)
            result = await session.execute(stmt)
            await session.commit()

            if result.rowcount == 0:
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

        except ValueError as e:
            await session.rollback()
            raise

        except SQLAlchemyError as e:
            await session.rollback()
            error_msg = f"Database error deleting order: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="delete_order_db_error",
                    location="OrderRepository.delete",
                ),
            )
            return False
