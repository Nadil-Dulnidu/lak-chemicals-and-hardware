from typing import Optional, List
import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.repository.inventory_repo import InventoryRepository
from app.repository.product_repo import ProductRepository
from app.schemas.inventory_schema import (
    StockMovementCreate,
    StockMovementResponse,
    StockMovementListResponse,
    StockMovementFilterParams,
    InventoryLevelResponse,
    ReorderAlertResponse,
    StockSummaryResponse,
    BulkStockMovementCreate,
    StockAdjustmentRequest,
)
from app.config.logging import get_logger, create_owasp_log_context


class InventoryService:
    """
    Service layer for Inventory business logic.
    Handles validation, business rules, orchestration, and data transformation.
    """

    def __init__(self):
        self.repo = InventoryRepository()
        self.product_repo = ProductRepository()
        self._logger = get_logger(__name__)

    async def record_stock_movement(
        self,
        session: AsyncSession,
        movement_data: StockMovementCreate,
        user_id: Optional[str] = None,
    ) -> Optional[StockMovementResponse]:
        """
        Record a stock movement (IN or OUT).
        Unified method for both stock-in and stock-out transactions.

        Args:
            session: Database session
            movement_data: Validated movement data
            user_id: Optional user ID for audit logging

        Returns:
            StockMovementResponse or None if creation fails
        """
        try:
            movement_type = movement_data.movement_type.value

            self._logger.info(
                f"Recording stock {movement_type}: {movement_data.quantity} units for product {movement_data.product_id}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action=f"record_stock_{movement_type.lower()}",
                    location="InventoryService.record_stock_movement",
                ),
            )

            # Convert to dict and add created_by
            movement_dict = movement_data.model_dump(exclude_unset=True)
            movement_dict["created_by"] = user_id

            # Create movement (repository will update product stock)
            movement = await self.repo.create_movement(session, movement_dict)

            if movement:
                # Check if stock is now low (for OUT movements)
                if movement_type == "OUT":
                    product = await self.product_repo.get_by_id(
                        session, uuid.UUID(movement_data.product_id)
                    )
                    if product and product.stock_qty < 10:  # Low stock threshold
                        self._logger.warning(
                            f"Low stock alert: Product {product.id} now has {product.stock_qty} units",
                            extra=create_owasp_log_context(
                                user=user_id or "system",
                                action="low_stock_alert",
                                location="InventoryService.record_stock_movement",
                            ),
                        )

                self._logger.info(
                    f"Stock {movement_type} recorded successfully: {movement.movement_id}",
                    extra=create_owasp_log_context(
                        user=user_id or "system",
                        action=f"record_stock_{movement_type.lower()}_success",
                        location="InventoryService.record_stock_movement",
                    ),
                )

                return await self._to_response(session, movement)

            return None

        except ValueError as e:
            self._logger.error(
                f"Validation error recording stock movement: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="record_stock_movement_validation_error",
                    location="InventoryService.record_stock_movement",
                ),
            )
            raise

        except Exception as e:
            self._logger.error(
                f"Service error recording stock movement: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="record_stock_movement_error",
                    location="InventoryService.record_stock_movement",
                ),
            )
            raise

    async def record_stock_in(
        self,
        session: AsyncSession,
        movement_data: StockMovementCreate,
        user_id: Optional[str] = None,
    ) -> Optional[StockMovementResponse]:
        """
        Record a stock-in transaction.

        Args:
            session: Database session
            movement_data: Validated movement data
            user_id: Optional user ID for audit logging

        Returns:
            StockMovementResponse or None if creation fails
        """
        try:
            self._logger.info(
                f"Recording stock IN: {movement_data.quantity} units for product {movement_data.product_id}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="record_stock_in",
                    location="InventoryService.record_stock_in",
                ),
            )

            # Ensure movement type is IN
            if movement_data.movement_type.value != "IN":
                raise ValueError("Movement type must be IN for stock-in transactions")

            # Convert to dict and add created_by
            movement_dict = movement_data.model_dump(exclude_unset=True)
            movement_dict["created_by"] = user_id

            # Create movement (repository will update product stock)
            movement = await self.repo.create_movement(session, movement_dict)

            if movement:
                self._logger.info(
                    f"Stock IN recorded successfully: {movement.movement_id}",
                    extra=create_owasp_log_context(
                        user=user_id or "system",
                        action="record_stock_in_success",
                        location="InventoryService.record_stock_in",
                    ),
                )

                return await self._to_response(session, movement)

            return None

        except ValueError as e:
            self._logger.error(
                f"Validation error recording stock IN: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="record_stock_in_validation_error",
                    location="InventoryService.record_stock_in",
                ),
            )
            raise

        except Exception as e:
            self._logger.error(
                f"Service error recording stock IN: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="record_stock_in_error",
                    location="InventoryService.record_stock_in",
                ),
            )
            raise

    async def record_stock_out(
        self,
        session: AsyncSession,
        movement_data: StockMovementCreate,
        user_id: Optional[str] = None,
    ) -> Optional[StockMovementResponse]:
        """
        Record a stock-out transaction.

        Args:
            session: Database session
            movement_data: Validated movement data
            user_id: Optional user ID for audit logging

        Returns:
            StockMovementResponse or None if creation fails
        """
        try:
            self._logger.info(
                f"Recording stock OUT: {movement_data.quantity} units for product {movement_data.product_id}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="record_stock_out",
                    location="InventoryService.record_stock_out",
                ),
            )

            # Ensure movement type is OUT
            if movement_data.movement_type.value != "OUT":
                raise ValueError("Movement type must be OUT for stock-out transactions")

            # Convert to dict and add created_by
            movement_dict = movement_data.model_dump(exclude_unset=True)
            movement_dict["created_by"] = user_id

            # Create movement (repository will check stock and update)
            movement = await self.repo.create_movement(session, movement_dict)

            if movement:
                # Check if stock is now low
                product = await self.product_repo.get_by_id(
                    session, uuid.UUID(movement_data.product_id)
                )
                if product and product.stock_qty < 10:  # Low stock threshold
                    self._logger.warning(
                        f"Low stock alert: Product {product.id} now has {product.stock_qty} units",
                        extra=create_owasp_log_context(
                            user=user_id or "system",
                            action="low_stock_alert",
                            location="InventoryService.record_stock_out",
                        ),
                    )

                self._logger.info(
                    f"Stock OUT recorded successfully: {movement.movement_id}",
                    extra=create_owasp_log_context(
                        user=user_id or "system",
                        action="record_stock_out_success",
                        location="InventoryService.record_stock_out",
                    ),
                )

                return await self._to_response(session, movement)

            return None

        except ValueError as e:
            self._logger.error(
                f"Validation error recording stock OUT: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="record_stock_out_validation_error",
                    location="InventoryService.record_stock_out",
                ),
            )
            raise

        except Exception as e:
            self._logger.error(
                f"Service error recording stock OUT: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="record_stock_out_error",
                    location="InventoryService.record_stock_out",
                ),
            )
            raise

    async def get_movement(
        self, session: AsyncSession, movement_id: int, user_id: Optional[str] = None
    ) -> Optional[StockMovementResponse]:
        """
        Get movement by ID.

        Args:
            session: Database session
            movement_id: Movement ID
            user_id: Optional user ID for audit logging

        Returns:
            StockMovementResponse or None if not found
        """
        try:
            movement = await self.repo.get_by_id(session, movement_id)

            if movement:
                return await self._to_response(session, movement)

            return None

        except Exception as e:
            self._logger.error(
                f"Service error getting movement: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="get_movement_error",
                    location="InventoryService.get_movement",
                ),
            )
            return None

    async def get_all_movements(
        self,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[str] = None,
    ) -> StockMovementListResponse:
        """
        Get all movements with pagination.

        Args:
            session: Database session
            skip: Number of records to skip
            limit: Maximum records to return
            user_id: Optional user ID for audit logging

        Returns:
            StockMovementListResponse with movements and metadata
        """
        try:
            movements = await self.repo.get_all(session, skip, limit)
            total = await self.repo.count_movements(session)

            movement_responses = []
            for movement in movements:
                response = await self._to_response(session, movement)
                if response:
                    movement_responses.append(response)

            return StockMovementListResponse(
                movements=movement_responses,
                total=total,
                skip=skip,
                limit=limit,
                has_more=skip + len(movements) < total,
            )

        except Exception as e:
            self._logger.error(
                f"Service error getting all movements: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="get_all_movements_error",
                    location="InventoryService.get_all_movements",
                ),
            )
            return StockMovementListResponse(
                movements=[], total=0, skip=skip, limit=limit, has_more=False
            )

    async def filter_movements(
        self,
        session: AsyncSession,
        filter_params: StockMovementFilterParams,
        user_id: Optional[str] = None,
    ) -> StockMovementListResponse:
        """
        Filter movements based on criteria.

        Args:
            session: Database session
            filter_params: Validated filter parameters
            user_id: Optional user ID for audit logging

        Returns:
            StockMovementListResponse with filtered movements
        """
        try:
            # Convert Pydantic model to dict for repository
            filters = filter_params.model_dump(
                exclude={"skip", "limit"}, exclude_unset=True
            )

            movements = await self.repo.filter_movements(
                session, filters, filter_params.skip, filter_params.limit
            )

            total = await self.repo.count_movements(session, filters)

            movement_responses = []
            for movement in movements:
                response = await self._to_response(session, movement)
                if response:
                    movement_responses.append(response)

            return StockMovementListResponse(
                movements=movement_responses,
                total=total,
                skip=filter_params.skip,
                limit=filter_params.limit,
                has_more=filter_params.skip + len(movements) < total,
            )

        except Exception as e:
            self._logger.error(
                f"Service error filtering movements: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="filter_movements_error",
                    location="InventoryService.filter_movements",
                ),
            )
            return StockMovementListResponse(
                movements=[],
                total=0,
                skip=filter_params.skip,
                limit=filter_params.limit,
                has_more=False,
            )

    async def get_product_movements(
        self,
        session: AsyncSession,
        product_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[str] = None,
    ) -> StockMovementListResponse:
        """
        Get all movements for a specific product.

        Args:
            session: Database session
            product_id: Product UUID
            skip: Number of records to skip
            limit: Maximum records to return
            user_id: Optional user ID for audit logging

        Returns:
            StockMovementListResponse with product movements
        """
        try:
            movements = await self.repo.get_product_movements(
                session, product_id, skip, limit
            )
            total = await self.repo.count_movements(session, {"product_id": product_id})

            movement_responses = []
            for movement in movements:
                response = await self._to_response(session, movement)
                if response:
                    movement_responses.append(response)

            return StockMovementListResponse(
                movements=movement_responses,
                total=total,
                skip=skip,
                limit=limit,
                has_more=skip + len(movements) < total,
            )

        except Exception as e:
            self._logger.error(
                f"Service error getting product movements: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="get_product_movements_error",
                    location="InventoryService.get_product_movements",
                ),
            )
            return StockMovementListResponse(
                movements=[], total=0, skip=skip, limit=limit, has_more=False
            )

    async def get_inventory_level(
        self,
        session: AsyncSession,
        product_id: uuid.UUID,
        user_id: Optional[str] = None,
    ) -> Optional[InventoryLevelResponse]:
        """
        Get current inventory level for a product.

        Args:
            session: Database session
            product_id: Product UUID
            user_id: Optional user ID for audit logging

        Returns:
            InventoryLevelResponse with stock information
        """
        try:
            stock_info = await self.repo.get_current_stock_level(session, product_id)

            if stock_info:
                return InventoryLevelResponse(**stock_info)

            return None

        except Exception as e:
            self._logger.error(
                f"Service error getting inventory level: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="get_inventory_level_error",
                    location="InventoryService.get_inventory_level",
                ),
            )
            return None

    async def delete_movement(
        self, session: AsyncSession, movement_id: int, user_id: Optional[str] = None
    ) -> bool:
        """
        Delete a historical movement record.
        WARNING: This does NOT reverse the stock quantity change.

        Args:
            session: Database session
            movement_id: Movement ID to delete
            user_id: Optional user ID for audit logging

        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            self._logger.warning(
                f"Deleting movement record: {movement_id} (stock quantity NOT reversed)",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="delete_movement",
                    location="InventoryService.delete_movement",
                ),
            )

            success = await self.repo.delete(session, movement_id)

            if success:
                self._logger.info(
                    f"Movement deleted successfully: {movement_id}",
                    extra=create_owasp_log_context(
                        user=user_id or "system",
                        action="delete_movement_success",
                        location="InventoryService.delete_movement",
                    ),
                )

            return success

        except Exception as e:
            self._logger.error(
                f"Service error deleting movement: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="delete_movement_error",
                    location="InventoryService.delete_movement",
                ),
            )
            return False

    async def adjust_stock(
        self,
        session: AsyncSession,
        adjustment: StockAdjustmentRequest,
        user_id: Optional[str] = None,
    ) -> Optional[StockMovementResponse]:
        """
        Adjust stock to a specific target quantity.
        Creates an IN or OUT movement to reach the target.

        Args:
            session: Database session
            adjustment: Stock adjustment request
            user_id: Optional user ID for audit logging

        Returns:
            StockMovementResponse or None if adjustment fails
        """
        try:
            product_id = uuid.UUID(adjustment.product_id)
            product = await self.product_repo.get_by_id(session, product_id)

            if not product:
                raise ValueError(f"Product not found: {adjustment.product_id}")

            current_stock = product.stock_qty
            difference = adjustment.target_quantity - current_stock

            if difference == 0:
                self._logger.info(
                    f"No adjustment needed for product {product_id}: already at target {adjustment.target_quantity}",
                    extra=create_owasp_log_context(
                        user=user_id or "system",
                        action="stock_adjustment_no_change",
                        location="InventoryService.adjust_stock",
                    ),
                )
                return None

            # Create movement to adjust stock
            movement_type = "IN" if difference > 0 else "OUT"
            quantity = abs(difference)

            movement_data = StockMovementCreate(
                product_id=adjustment.product_id,
                movement_type=movement_type,
                quantity=quantity,
                reference=adjustment.reference
                or f"Stock adjustment to {adjustment.target_quantity}",
            )

            self._logger.info(
                f"Adjusting stock for product {product_id}: {current_stock} -> {adjustment.target_quantity} ({movement_type} {quantity})",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="stock_adjustment",
                    location="InventoryService.adjust_stock",
                ),
            )

            # Use unified method for both IN and OUT
            return await self.record_stock_movement(session, movement_data, user_id)

        except ValueError as e:
            self._logger.error(
                f"Validation error adjusting stock: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="stock_adjustment_validation_error",
                    location="InventoryService.adjust_stock",
                ),
            )
            raise

        except Exception as e:
            self._logger.error(
                f"Service error adjusting stock: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="stock_adjustment_error",
                    location="InventoryService.adjust_stock",
                ),
            )
            raise

    async def _to_response(
        self, session: AsyncSession, movement
    ) -> StockMovementResponse:
        """
        Convert StockMovement model to StockMovementResponse schema.

        Args:
            session: Database session
            movement: StockMovement model instance

        Returns:
            StockMovementResponse schema
        """
        # Get product name
        product = await self.product_repo.get_by_id(session, movement.product_id)
        product_name = product.name if product else None

        return StockMovementResponse(
            movement_id=movement.movement_id,
            product_id=str(movement.product_id),
            product_name=product_name,
            movement_type=movement.movement_type.value,
            quantity=movement.quantity,
            reference=movement.reference,
            movement_date=movement.movement_date,
            created_by=movement.created_by,
        )
