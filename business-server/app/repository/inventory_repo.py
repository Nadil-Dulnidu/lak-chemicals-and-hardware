import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, delete, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.models.Inventory_model import StockMovement
from app.models.product_model import Product
from app.constants import MovementType
from app.config.logging import get_logger, create_owasp_log_context


class InventoryRepository:
    """
    Singleton repository for Inventory/Stock Movement CRUD operations.
    Implements comprehensive logging and error handling for production use.
    """

    _instance: Optional["InventoryRepository"] = None
    _logger = None

    def __new__(cls):
        """Singleton pattern implementation"""
        if cls._instance is None:
            cls._instance = super(InventoryRepository, cls).__new__(cls)
            cls._logger = get_logger(__name__)
            cls._logger.info(
                "InventoryRepository singleton instance created",
                extra=create_owasp_log_context(
                    user="system",
                    action="repository_initialization",
                    location="InventoryRepository.__new__",
                ),
            )
        return cls._instance

    async def create_movement(
        self, session: AsyncSession, movement_data: Dict[str, Any]
    ) -> Optional[StockMovement]:
        """
        Create a new stock movement and update product stock quantity.

        Args:
            session: AsyncSession for database operations
            movement_data: Dictionary containing movement information

        Returns:
            Created StockMovement object or None if creation fails
        """
        try:
            # Validate required fields
            required_fields = ["product_id", "movement_type", "quantity"]
            missing_fields = [
                field for field in required_fields if field not in movement_data
            ]

            if missing_fields:
                error_msg = f"Missing required fields: {', '.join(missing_fields)}"
                self._logger.error(
                    error_msg,
                    extra=create_owasp_log_context(
                        user="system",
                        action="create_movement_validation_failed",
                        location="InventoryRepository.create_movement",
                    ),
                )
                raise ValueError(error_msg)

            # Convert product_id to UUID if it's a string
            if isinstance(movement_data["product_id"], str):
                movement_data["product_id"] = uuid.UUID(movement_data["product_id"])

            # Convert movement_type string to enum if needed
            if isinstance(movement_data["movement_type"], str):
                movement_data["movement_type"] = MovementType[
                    movement_data["movement_type"]
                ]

            # Verify product exists
            product_result = await session.execute(
                select(Product).where(Product.id == movement_data["product_id"])
            )
            product = product_result.scalar_one_or_none()

            if not product:
                error_msg = f"Product not found: {movement_data['product_id']}"
                self._logger.error(
                    error_msg,
                    extra=create_owasp_log_context(
                        user="system",
                        action="create_movement_product_not_found",
                        location="InventoryRepository.create_movement",
                    ),
                )
                raise ValueError(error_msg)

            # For OUT movements, check if sufficient stock
            if movement_data["movement_type"] == MovementType.OUT:
                if product.stock_qty < movement_data["quantity"]:
                    error_msg = f"Insufficient stock. Available: {product.stock_qty}, Requested: {movement_data['quantity']}"
                    self._logger.warning(
                        error_msg,
                        extra=create_owasp_log_context(
                            user="system",
                            action="create_movement_insufficient_stock",
                            location="InventoryRepository.create_movement",
                        ),
                    )
                    raise ValueError(error_msg)

            # Create movement record
            movement = StockMovement(**movement_data)
            session.add(movement)

            # Update product stock quantity
            if movement_data["movement_type"] == MovementType.IN:
                product.stock_qty += movement_data["quantity"]
            else:  # OUT
                product.stock_qty -= movement_data["quantity"]

            await session.commit()
            await session.refresh(movement)

            self._logger.info(
                f"Stock movement created: {movement.movement_id} - {movement.movement_type.value} {movement.quantity} units for product {movement.product_id}",
                extra=create_owasp_log_context(
                    user="system",
                    action="create_movement_success",
                    location="InventoryRepository.create_movement",
                ),
            )

            return movement

        except ValueError as e:
            await session.rollback()
            raise

        except SQLAlchemyError as e:
            await session.rollback()
            error_msg = f"Database error while creating movement: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="create_movement_db_error",
                    location="InventoryRepository.create_movement",
                ),
            )
            return None

        except Exception as e:
            await session.rollback()
            error_msg = f"Unexpected error while creating movement: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="create_movement_unexpected_error",
                    location="InventoryRepository.create_movement",
                ),
            )
            return None

    async def get_by_id(
        self, session: AsyncSession, movement_id: int
    ) -> Optional[StockMovement]:
        """
        Retrieve a stock movement by its ID.

        Args:
            session: AsyncSession for database operations
            movement_id: ID of the movement

        Returns:
            StockMovement object or None if not found
        """
        try:
            result = await session.execute(
                select(StockMovement).where(StockMovement.movement_id == movement_id)
            )
            movement = result.scalar_one_or_none()

            if movement:
                self._logger.info(
                    f"Movement retrieved: {movement_id}",
                    extra=create_owasp_log_context(
                        user="system",
                        action="get_movement_by_id_success",
                        location="InventoryRepository.get_by_id",
                    ),
                )

            return movement

        except SQLAlchemyError as e:
            error_msg = (
                f"Database error while retrieving movement {movement_id}: {str(e)}"
            )
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="get_movement_by_id_db_error",
                    location="InventoryRepository.get_by_id",
                ),
            )
            return None

    async def get_all(
        self, session: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[StockMovement]:
        """
        Retrieve all stock movements with pagination.

        Args:
            session: AsyncSession for database operations
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of StockMovement objects
        """
        try:
            query = (
                select(StockMovement)
                .offset(skip)
                .limit(limit)
                .order_by(desc(StockMovement.movement_date))
            )

            result = await session.execute(query)
            movements = result.scalars().all()

            self._logger.info(
                f"Retrieved {len(movements)} movements (skip={skip}, limit={limit})",
                extra=create_owasp_log_context(
                    user="system",
                    action="get_all_movements_success",
                    location="InventoryRepository.get_all",
                ),
            )

            return list(movements)

        except SQLAlchemyError as e:
            error_msg = f"Database error while retrieving movements: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="get_all_movements_db_error",
                    location="InventoryRepository.get_all",
                ),
            )
            return []

    async def delete(self, session: AsyncSession, movement_id: int) -> bool:
        """
        Delete a stock movement record (for historical cleanup).
        WARNING: This does NOT reverse the stock quantity change.

        Args:
            session: AsyncSession for database operations
            movement_id: ID of the movement to delete

        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            stmt = delete(StockMovement).where(StockMovement.movement_id == movement_id)
            result = await session.execute(stmt)
            await session.commit()

            if result.rowcount == 0:
                self._logger.warning(
                    f"Movement not found for deletion: {movement_id}",
                    extra=create_owasp_log_context(
                        user="system",
                        action="delete_movement_not_found",
                        location="InventoryRepository.delete",
                    ),
                )
                return False

            self._logger.info(
                f"Movement deleted successfully: {movement_id}",
                extra=create_owasp_log_context(
                    user="system",
                    action="delete_movement_success",
                    location="InventoryRepository.delete",
                ),
            )

            return True

        except SQLAlchemyError as e:
            await session.rollback()
            error_msg = (
                f"Database error while deleting movement {movement_id}: {str(e)}"
            )
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="delete_movement_db_error",
                    location="InventoryRepository.delete",
                ),
            )
            return False

    async def filter_movements(
        self,
        session: AsyncSession,
        filters: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
    ) -> List[StockMovement]:
        """
        Filter stock movements based on various criteria.

        Args:
            session: AsyncSession for database operations
            filters: Dictionary of filter criteria
                - product_id: Product UUID
                - movement_type: MovementType enum or string
                - start_date: Start date for filtering
                - end_date: End date for filtering
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of filtered StockMovement objects
        """
        try:
            query = select(StockMovement)
            conditions = []

            # Product filter
            if "product_id" in filters and filters["product_id"]:
                product_id = filters["product_id"]
                if isinstance(product_id, str):
                    product_id = uuid.UUID(product_id)
                conditions.append(StockMovement.product_id == product_id)

            # Movement type filter
            if "movement_type" in filters and filters["movement_type"]:
                movement_type = filters["movement_type"]
                if isinstance(movement_type, str):
                    movement_type = MovementType[movement_type]
                conditions.append(StockMovement.movement_type == movement_type)

            # Date range filter
            if "start_date" in filters and filters["start_date"]:
                conditions.append(StockMovement.movement_date >= filters["start_date"])

            if "end_date" in filters and filters["end_date"]:
                conditions.append(StockMovement.movement_date <= filters["end_date"])

            # Apply all conditions
            if conditions:
                query = query.where(and_(*conditions))

            # Apply pagination and ordering
            query = (
                query.offset(skip)
                .limit(limit)
                .order_by(desc(StockMovement.movement_date))
            )

            result = await session.execute(query)
            movements = result.scalars().all()

            self._logger.info(
                f"Filtered movements: {len(movements)} results (filters={filters})",
                extra=create_owasp_log_context(
                    user="system",
                    action="filter_movements_success",
                    location="InventoryRepository.filter_movements",
                ),
            )

            return list(movements)

        except SQLAlchemyError as e:
            error_msg = f"Database error while filtering movements: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="filter_movements_db_error",
                    location="InventoryRepository.filter_movements",
                ),
            )
            return []

    async def get_product_movements(
        self,
        session: AsyncSession,
        product_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[StockMovement]:
        """
        Get all movements for a specific product.

        Args:
            session: AsyncSession for database operations
            product_id: UUID of the product
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of StockMovement objects for the product
        """
        return await self.filter_movements(
            session, filters={"product_id": product_id}, skip=skip, limit=limit
        )

    async def get_current_stock_level(
        self, session: AsyncSession, product_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Calculate current stock level for a product based on movements.

        Args:
            session: AsyncSession for database operations
            product_id: UUID of the product

        Returns:
            Dictionary with stock level information
        """
        try:
            # Get product
            product_result = await session.execute(
                select(Product).where(Product.id == product_id)
            )
            product = product_result.scalar_one_or_none()

            if not product:
                return None

            # Calculate totals from movements
            in_query = select(func.sum(StockMovement.quantity)).where(
                and_(
                    StockMovement.product_id == product_id,
                    StockMovement.movement_type == MovementType.IN,
                )
            )
            out_query = select(func.sum(StockMovement.quantity)).where(
                and_(
                    StockMovement.product_id == product_id,
                    StockMovement.movement_type == MovementType.OUT,
                )
            )

            total_in_result = await session.execute(in_query)
            total_out_result = await session.execute(out_query)

            total_in = total_in_result.scalar() or 0
            total_out = total_out_result.scalar() or 0

            # Get last movement date
            last_movement_query = (
                select(StockMovement.movement_date)
                .where(StockMovement.product_id == product_id)
                .order_by(desc(StockMovement.movement_date))
                .limit(1)
            )
            last_movement_result = await session.execute(last_movement_query)
            last_movement_date = last_movement_result.scalar_one_or_none()

            return {
                "product_id": str(product_id),
                "product_name": product.name,
                "current_stock": product.stock_qty,
                "total_in": total_in,
                "total_out": total_out,
                "last_movement_date": last_movement_date,
            }

        except SQLAlchemyError as e:
            error_msg = f"Database error while calculating stock level: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="get_stock_level_db_error",
                    location="InventoryRepository.get_current_stock_level",
                ),
            )
            return None

    async def get_movements_by_date_range(
        self,
        session: AsyncSession,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100,
    ) -> List[StockMovement]:
        """
        Get movements within a specific date range.

        Args:
            session: AsyncSession for database operations
            start_date: Start date
            end_date: End date
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of StockMovement objects
        """
        return await self.filter_movements(
            session,
            filters={"start_date": start_date, "end_date": end_date},
            skip=skip,
            limit=limit,
        )

    async def count_movements(
        self, session: AsyncSession, filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Count total movements matching filters.

        Args:
            session: AsyncSession for database operations
            filters: Optional filter criteria

        Returns:
            Total count of movements
        """
        try:
            query = select(func.count(StockMovement.movement_id))
            conditions = []

            if filters:
                if "product_id" in filters and filters["product_id"]:
                    product_id = filters["product_id"]
                    if isinstance(product_id, str):
                        product_id = uuid.UUID(product_id)
                    conditions.append(StockMovement.product_id == product_id)

                if "movement_type" in filters and filters["movement_type"]:
                    movement_type = filters["movement_type"]
                    if isinstance(movement_type, str):
                        movement_type = MovementType[movement_type]
                    conditions.append(StockMovement.movement_type == movement_type)

                if "start_date" in filters and filters["start_date"]:
                    conditions.append(
                        StockMovement.movement_date >= filters["start_date"]
                    )

                if "end_date" in filters and filters["end_date"]:
                    conditions.append(
                        StockMovement.movement_date <= filters["end_date"]
                    )

            if conditions:
                query = query.where(and_(*conditions))

            result = await session.execute(query)
            count = result.scalar()

            return count or 0

        except SQLAlchemyError as e:
            error_msg = f"Database error while counting movements: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="count_movements_db_error",
                    location="InventoryRepository.count_movements",
                ),
            )
            return 0
