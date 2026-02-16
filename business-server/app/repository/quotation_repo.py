import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select, delete, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.models.quotation_model import Quotation, QuotationItem
from app.models.product_model import Product
from app.constants import QuotationStatus
from app.config.logging import get_logger, create_owasp_log_context


class QuotationRepository:
    """
    Singleton repository for Quotation CRUD operations.
    Implements comprehensive logging and error handling for production use.
    """

    _instance: Optional["QuotationRepository"] = None
    _logger = None

    def __new__(cls):
        """Singleton pattern implementation"""
        if cls._instance is None:
            cls._instance = super(QuotationRepository, cls).__new__(cls)
            cls._logger = get_logger(__name__)
            cls._logger.info(
                "QuotationRepository singleton instance created",
                extra=create_owasp_log_context(
                    user="system",
                    action="repository_initialization",
                    location="QuotationRepository.__new__",
                ),
            )
        return cls._instance

    async def create(
        self, session: AsyncSession, quotation_data: Dict[str, Any]
    ) -> Optional[Quotation]:
        """
        Create a new quotation with items.

        Args:
            session: AsyncSession for database operations
            quotation_data: Dictionary containing quotation information
                - user_id: str
                - items: List[Dict] with product_id, quantity
                - notes: Optional[str]

        Returns:
            Created Quotation object or None if creation fails
        """
        try:
            # Extract items from quotation_data
            items_data = quotation_data.pop("items", [])

            if not items_data:
                raise ValueError("At least one item is required")

            # Create quotation
            quotation = Quotation(
                user_id=quotation_data["user_id"],
                status=QuotationStatus.PENDING,
                total_amount=Decimal("0.00"),
                notes=quotation_data.get("notes"),
            )
            session.add(quotation)
            await session.flush()  # Get quotation_id

            # Create quotation items and calculate total
            total_amount = Decimal("0.00")

            for item_data in items_data:
                product_id = uuid.UUID(item_data["product_id"])
                quantity = item_data["quantity"]

                # Get product to get price
                product_result = await session.execute(
                    select(Product).where(Product.id == product_id)
                )
                product = product_result.scalar_one_or_none()

                if not product:
                    raise ValueError(f"Product not found: {product_id}")

                # Calculate subtotal
                unit_price = Decimal(str(product.price))
                subtotal = unit_price * quantity

                # Create quotation item
                quotation_item = QuotationItem(
                    quotation_id=quotation.quotation_id,
                    product_id=product_id,
                    quantity=quantity,
                    unit_price=unit_price,
                    subtotal=subtotal,
                )
                session.add(quotation_item)
                total_amount += subtotal

            # Update quotation total
            quotation.total_amount = total_amount

            await session.commit()
            await session.refresh(quotation)

            self._logger.info(
                f"Quotation created: {quotation.quotation_id} for user {quotation.user_id}",
                extra=create_owasp_log_context(
                    user=quotation.user_id,
                    action="create_quotation_success",
                    location="QuotationRepository.create",
                ),
            )

            return quotation

        except ValueError as e:
            await session.rollback()
            raise

        except SQLAlchemyError as e:
            await session.rollback()
            error_msg = f"Database error creating quotation: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="create_quotation_db_error",
                    location="QuotationRepository.create",
                ),
            )
            return None

    async def get_by_id(
        self, session: AsyncSession, quotation_id: int
    ) -> Optional[Quotation]:
        """
        Get quotation by ID with items.

        Args:
            session: AsyncSession for database operations
            quotation_id: Quotation ID

        Returns:
            Quotation object or None if not found
        """
        try:
            result = await session.execute(
                select(Quotation).where(Quotation.quotation_id == quotation_id)
            )
            quotation = result.scalar_one_or_none()

            if quotation:
                self._logger.info(
                    f"Quotation retrieved: {quotation_id}",
                    extra=create_owasp_log_context(
                        user="system",
                        action="get_quotation_by_id_success",
                        location="QuotationRepository.get_by_id",
                    ),
                )

            return quotation

        except SQLAlchemyError as e:
            error_msg = f"Database error retrieving quotation {quotation_id}: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="get_quotation_by_id_db_error",
                    location="QuotationRepository.get_by_id",
                ),
            )
            return None

    async def get_user_quotations(
        self, session: AsyncSession, user_id: str, skip: int = 0, limit: int = 100
    ) -> List[Quotation]:
        """
        Get all quotations for a user.

        Args:
            session: AsyncSession for database operations
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Quotation objects
        """
        try:
            query = (
                select(Quotation)
                .where(Quotation.user_id == user_id)
                .offset(skip)
                .limit(limit)
                .order_by(desc(Quotation.created_at))
            )

            result = await session.execute(query)
            quotations = result.scalars().all()

            self._logger.info(
                f"Retrieved {len(quotations)} quotations for user {user_id}",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="get_user_quotations_success",
                    location="QuotationRepository.get_user_quotations",
                ),
            )

            return list(quotations)

        except SQLAlchemyError as e:
            error_msg = f"Database error retrieving user quotations: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user=user_id,
                    action="get_user_quotations_db_error",
                    location="QuotationRepository.get_user_quotations",
                ),
            )
            return []

    async def update_status(
        self,
        session: AsyncSession,
        quotation_id: int,
        status: QuotationStatus,
        discount_amount: Optional[Decimal] = None,
    ) -> Optional[Quotation]:
        """
        Update quotation status.

        Args:
            session: AsyncSession for database operations
            quotation_id: Quotation ID
            status: New status
            discount_amount: Optional discount amount (only applied if status is approved)

        Returns:
            Updated Quotation or None if not found
        """
        try:
            result = await session.execute(
                select(Quotation).where(Quotation.quotation_id == quotation_id)
            )
            quotation = result.scalar_one_or_none()

            if not quotation:
                self._logger.warning(
                    f"Quotation not found for status update: {quotation_id}",
                    extra=create_owasp_log_context(
                        user="system",
                        action="update_quotation_status_not_found",
                        location="QuotationRepository.update_status",
                    ),
                )
                return None

            old_status = quotation.status
            quotation.status = status
            if discount_amount is not None:
                quotation.discount_amount = discount_amount
            quotation.updated_at = datetime.utcnow()

            await session.commit()
            await session.refresh(quotation)

            self._logger.info(
                f"Quotation status updated: {quotation_id} ({old_status.value} -> {status.value})",
                extra=create_owasp_log_context(
                    user=quotation.user_id,
                    action="update_quotation_status_success",
                    location="QuotationRepository.update_status",
                ),
            )

            return quotation

        except SQLAlchemyError as e:
            await session.rollback()
            error_msg = f"Database error updating quotation status: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="update_quotation_status_db_error",
                    location="QuotationRepository.update_status",
                ),
            )
            return None

    async def filter_quotations(
        self,
        session: AsyncSession,
        user_id: Optional[str],
        filters: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
    ) -> List[Quotation]:
        """
        Filter quotations based on criteria.

        Args:
            session: AsyncSession for database operations
            user_id: User ID
            filters: Dictionary of filter criteria
                - status: QuotationStatus
                - start_date: datetime
                - end_date: datetime
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of filtered Quotation objects
        """
        try:
            query = select(Quotation)
            conditions = []

            if user_id:
                conditions.append(Quotation.user_id == user_id)

            # Status filter
            if "status" in filters and filters["status"]:
                status = filters["status"]
                if isinstance(status, str):
                    status = QuotationStatus[status]
                conditions.append(Quotation.status == status)

            # Date range filter
            if "start_date" in filters and filters["start_date"]:
                conditions.append(Quotation.created_at >= filters["start_date"])

            if "end_date" in filters and filters["end_date"]:
                conditions.append(Quotation.created_at <= filters["end_date"])

            # Apply all conditions
            if conditions:
                query = query.where(and_(*conditions))

            # Apply pagination and ordering
            query = query.offset(skip).limit(limit).order_by(desc(Quotation.created_at))

            result = await session.execute(query)
            quotations = result.scalars().all()

            self._logger.info(
                f"Filtered quotations: {len(quotations)} results (filters={filters})",
                extra=create_owasp_log_context(
                    user=user_id,
                    action="filter_quotations_success",
                    location="QuotationRepository.filter_quotations",
                ),
            )

            return list(quotations)

        except SQLAlchemyError as e:
            error_msg = f"Database error filtering quotations: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user=user_id,
                    action="filter_quotations_db_error",
                    location="QuotationRepository.filter_quotations",
                ),
            )
            return []

    async def count_quotations(
        self,
        session: AsyncSession,
        user_id: Optional[str],
        filters: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Count total quotations matching filters.

        Args:
            session: AsyncSession for database operations
            user_id: User ID
            filters: Optional filter criteria

        Returns:
            Total count of quotations
        """
        try:
            query = select(func.count(Quotation.quotation_id))
            conditions = []

            if user_id:
                conditions.append(Quotation.user_id == user_id)

            if filters:
                if "status" in filters and filters["status"]:
                    status = filters["status"]
                    if isinstance(status, str):
                        status = QuotationStatus[status]
                    conditions.append(Quotation.status == status)

                if "start_date" in filters and filters["start_date"]:
                    conditions.append(Quotation.created_at >= filters["start_date"])

                if "end_date" in filters and filters["end_date"]:
                    conditions.append(Quotation.created_at <= filters["end_date"])

            if conditions:
                query = query.where(and_(*conditions))

            result = await session.execute(query)
            count = result.scalar()

            return count or 0

        except SQLAlchemyError as e:
            error_msg = f"Database error counting quotations: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user=user_id,
                    action="count_quotations_db_error",
                    location="QuotationRepository.count_quotations",
                ),
            )
            return 0

    async def delete(self, session: AsyncSession, quotation_id: int) -> bool:
        """
        Delete a quotation.

        Args:
            session: AsyncSession for database operations
            quotation_id: Quotation ID to delete

        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            stmt = delete(Quotation).where(Quotation.quotation_id == quotation_id)
            result = await session.execute(stmt)
            await session.commit()

            if result.rowcount == 0:
                self._logger.warning(
                    f"Quotation not found for deletion: {quotation_id}",
                    extra=create_owasp_log_context(
                        user="system",
                        action="delete_quotation_not_found",
                        location="QuotationRepository.delete",
                    ),
                )
                return False

            self._logger.info(
                f"Quotation deleted: {quotation_id}",
                extra=create_owasp_log_context(
                    user="system",
                    action="delete_quotation_success",
                    location="QuotationRepository.delete",
                ),
            )

            return True

        except SQLAlchemyError as e:
            await session.rollback()
            error_msg = f"Database error deleting quotation: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="delete_quotation_db_error",
                    location="QuotationRepository.delete",
                ),
            )
            return False
