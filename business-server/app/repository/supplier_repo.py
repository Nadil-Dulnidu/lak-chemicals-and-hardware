import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import select, update, delete, and_, or_, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.models.supplier_model import Supplier
from app.models.product_model import Product
from app.models.supplier_product import supplier_product
from app.config.logging import get_logger, create_owasp_log_context


class SupplierRepository:
    """
    Singleton repository for Supplier CRUD operations.
    Implements comprehensive logging and error handling for production use.
    """

    _instance: Optional["SupplierRepository"] = None
    _logger = None

    def __new__(cls):
        """Singleton pattern implementation"""
        if cls._instance is None:
            cls._instance = super(SupplierRepository, cls).__new__(cls)
            cls._logger = get_logger(__name__)
            cls._logger.info(
                "SupplierRepository singleton instance created",
                extra=create_owasp_log_context(
                    user="system",
                    action="repository_initialization",
                    location="SupplierRepository.__new__",
                ),
            )
        return cls._instance

    async def create(
        self, session: AsyncSession, supplier_data: Dict[str, Any]
    ) -> Optional[Supplier]:
        """
        Create a new supplier.

        Args:
            session: AsyncSession for database operations
            supplier_data: Dictionary containing supplier information

        Returns:
            Created Supplier object or None if creation fails

        Raises:
            ValueError: If required fields are missing or invalid
        """
        try:
            # Validate required fields
            required_fields = ["name", "contact_number", "email"]
            missing_fields = [
                field for field in required_fields if field not in supplier_data
            ]

            if missing_fields:
                error_msg = f"Missing required fields: {', '.join(missing_fields)}"
                self._logger.error(
                    error_msg,
                    extra=create_owasp_log_context(
                        user="system",
                        action="create_supplier_validation_failed",
                        location="SupplierRepository.create",
                    ),
                )
                raise ValueError(error_msg)

            # Create supplier instance
            supplier = Supplier(**supplier_data)
            session.add(supplier)
            await session.commit()
            await session.refresh(supplier)

            self._logger.info(
                f"Supplier created successfully: {supplier.id} - {supplier.name}",
                extra=create_owasp_log_context(
                    user="system",
                    action="create_supplier_success",
                    location="SupplierRepository.create",
                ),
            )

            return supplier

        except IntegrityError as e:
            await session.rollback()
            error_msg = f"Database integrity error while creating supplier: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="create_supplier_integrity_error",
                    location="SupplierRepository.create",
                ),
            )
            raise ValueError("Supplier with this email already exists")

        except SQLAlchemyError as e:
            await session.rollback()
            error_msg = f"Database error while creating supplier: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="create_supplier_db_error",
                    location="SupplierRepository.create",
                ),
            )
            return None

        except Exception as e:
            await session.rollback()
            error_msg = f"Unexpected error while creating supplier: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="create_supplier_unexpected_error",
                    location="SupplierRepository.create",
                ),
            )
            return None

    async def get_by_id(
        self, session: AsyncSession, supplier_id: uuid.UUID
    ) -> Optional[Supplier]:
        """
        Retrieve a supplier by its ID.

        Args:
            session: AsyncSession for database operations
            supplier_id: UUID of the supplier

        Returns:
            Supplier object or None if not found
        """
        try:
            result = await session.execute(
                select(Supplier).where(Supplier.id == supplier_id)
            )
            supplier = result.scalar_one_or_none()

            if supplier:
                self._logger.info(
                    f"Supplier retrieved: {supplier_id}",
                    extra=create_owasp_log_context(
                        user="system",
                        action="get_supplier_by_id_success",
                        location="SupplierRepository.get_by_id",
                    ),
                )
            else:
                self._logger.warning(
                    f"Supplier not found: {supplier_id}",
                    extra=create_owasp_log_context(
                        user="system",
                        action="get_supplier_by_id_not_found",
                        location="SupplierRepository.get_by_id",
                    ),
                )

            return supplier

        except SQLAlchemyError as e:
            error_msg = (
                f"Database error while retrieving supplier {supplier_id}: {str(e)}"
            )
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="get_supplier_by_id_db_error",
                    location="SupplierRepository.get_by_id",
                ),
            )
            return None

    async def get_all(
        self,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> List[Supplier]:
        """
        Retrieve all suppliers with pagination.

        Args:
            session: AsyncSession for database operations
            skip: Number of records to skip
            limit: Maximum number of records to return
            include_inactive: Whether to include inactive suppliers

        Returns:
            List of Supplier objects
        """
        try:
            query = select(Supplier)

            if not include_inactive:
                query = query.where(Supplier.is_active == True)

            query = query.offset(skip).limit(limit).order_by(Supplier.created_at.desc())

            result = await session.execute(query)
            suppliers = result.scalars().all()

            self._logger.info(
                f"Retrieved {len(suppliers)} suppliers (skip={skip}, limit={limit})",
                extra=create_owasp_log_context(
                    user="system",
                    action="get_all_suppliers_success",
                    location="SupplierRepository.get_all",
                ),
            )

            return list(suppliers)

        except SQLAlchemyError as e:
            error_msg = f"Database error while retrieving suppliers: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="get_all_suppliers_db_error",
                    location="SupplierRepository.get_all",
                ),
            )
            return []

    async def update(
        self,
        session: AsyncSession,
        supplier_id: uuid.UUID,
        update_data: Dict[str, Any],
    ) -> Optional[Supplier]:
        """
        Update a supplier.

        Args:
            session: AsyncSession for database operations
            supplier_id: UUID of the supplier to update
            update_data: Dictionary containing fields to update

        Returns:
            Updated Supplier object or None if update fails
        """
        try:
            # Remove None values and id field if present
            update_data = {
                k: v for k, v in update_data.items() if v is not None and k != "id"
            }

            if not update_data:
                self._logger.warning(
                    f"No valid fields to update for supplier {supplier_id}",
                    extra=create_owasp_log_context(
                        user="system",
                        action="update_supplier_no_fields",
                        location="SupplierRepository.update",
                    ),
                )
                return await self.get_by_id(session, supplier_id)

            stmt = (
                update(Supplier)
                .where(Supplier.id == supplier_id)
                .values(**update_data)
                .execution_options(synchronize_session="fetch")
            )

            result = await session.execute(stmt)
            await session.commit()

            if result.rowcount == 0:
                self._logger.warning(
                    f"Supplier not found for update: {supplier_id}",
                    extra=create_owasp_log_context(
                        user="system",
                        action="update_supplier_not_found",
                        location="SupplierRepository.update",
                    ),
                )
                return None

            updated_supplier = await self.get_by_id(session, supplier_id)

            self._logger.info(
                f"Supplier updated successfully: {supplier_id}",
                extra=create_owasp_log_context(
                    user="system",
                    action="update_supplier_success",
                    location="SupplierRepository.update",
                ),
            )

            return updated_supplier

        except IntegrityError as e:
            await session.rollback()
            error_msg = f"Database integrity error while updating supplier {supplier_id}: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="update_supplier_integrity_error",
                    location="SupplierRepository.update",
                ),
            )
            raise ValueError("Email already exists for another supplier")

        except SQLAlchemyError as e:
            await session.rollback()
            error_msg = (
                f"Database error while updating supplier {supplier_id}: {str(e)}"
            )
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="update_supplier_db_error",
                    location="SupplierRepository.update",
                ),
            )
            return None

    async def delete(self, session: AsyncSession, supplier_id: uuid.UUID) -> bool:
        """
        Hard delete a supplier from the database.

        Args:
            session: AsyncSession for database operations
            supplier_id: UUID of the supplier to delete

        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            stmt = delete(Supplier).where(Supplier.id == supplier_id)
            result = await session.execute(stmt)
            await session.commit()

            if result.rowcount == 0:
                self._logger.warning(
                    f"Supplier not found for deletion: {supplier_id}",
                    extra=create_owasp_log_context(
                        user="system",
                        action="delete_supplier_not_found",
                        location="SupplierRepository.delete",
                    ),
                )
                return False

            self._logger.info(
                f"Supplier deleted successfully: {supplier_id}",
                extra=create_owasp_log_context(
                    user="system",
                    action="delete_supplier_success",
                    location="SupplierRepository.delete",
                ),
            )

            return True

        except SQLAlchemyError as e:
            await session.rollback()
            error_msg = (
                f"Database error while deleting supplier {supplier_id}: {str(e)}"
            )
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="delete_supplier_db_error",
                    location="SupplierRepository.delete",
                ),
            )
            return False

    async def soft_delete(self, session: AsyncSession, supplier_id: uuid.UUID) -> bool:
        """
        Soft delete a supplier by setting is_active to False.

        Args:
            session: AsyncSession for database operations
            supplier_id: UUID of the supplier to soft delete

        Returns:
            True if soft deletion was successful, False otherwise
        """
        try:
            updated_supplier = await self.update(
                session, supplier_id, {"is_active": False}
            )

            if updated_supplier:
                self._logger.info(
                    f"Supplier soft deleted successfully: {supplier_id}",
                    extra=create_owasp_log_context(
                        user="system",
                        action="soft_delete_supplier_success",
                        location="SupplierRepository.soft_delete",
                    ),
                )
                return True

            return False

        except Exception as e:
            error_msg = f"Error while soft deleting supplier {supplier_id}: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="soft_delete_supplier_error",
                    location="SupplierRepository.soft_delete",
                ),
            )
            return False

    async def filter_suppliers(
        self,
        session: AsyncSession,
        filters: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
    ) -> List[Supplier]:
        """
        Filter suppliers based on various criteria.

        Args:
            session: AsyncSession for database operations
            filters: Dictionary of filter criteria
                - is_active: Active status
                - search: Search term for name/email/contact_person
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of filtered Supplier objects
        """
        try:
            query = select(Supplier)
            conditions = []

            # Active status filter
            if "is_active" in filters:
                conditions.append(Supplier.is_active == filters["is_active"])
            else:
                # By default, only show active suppliers
                conditions.append(Supplier.is_active == True)

            # Search filter (name, email, or contact_person)
            if "search" in filters and filters["search"]:
                search_term = f"%{filters['search']}%"
                conditions.append(
                    or_(
                        Supplier.name.ilike(search_term),
                        Supplier.email.ilike(search_term),
                        Supplier.contact_person.ilike(search_term),
                    )
                )

            # Apply all conditions
            if conditions:
                query = query.where(and_(*conditions))

            # Apply pagination and ordering
            query = query.offset(skip).limit(limit).order_by(Supplier.created_at.desc())

            result = await session.execute(query)
            suppliers = result.scalars().all()

            self._logger.info(
                f"Filtered suppliers: {len(suppliers)} results (filters={filters})",
                extra=create_owasp_log_context(
                    user="system",
                    action="filter_suppliers_success",
                    location="SupplierRepository.filter_suppliers",
                ),
            )

            return list(suppliers)

        except SQLAlchemyError as e:
            error_msg = f"Database error while filtering suppliers: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="filter_suppliers_db_error",
                    location="SupplierRepository.filter_suppliers",
                ),
            )
            return []

    async def search_suppliers(
        self, session: AsyncSession, search_term: str, skip: int = 0, limit: int = 100
    ) -> List[Supplier]:
        """
        Search suppliers by name, email, or contact person.

        Args:
            session: AsyncSession for database operations
            search_term: Search term
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of matching Supplier objects
        """
        return await self.filter_suppliers(
            session, filters={"search": search_term}, skip=skip, limit=limit
        )

    async def link_product(
        self,
        session: AsyncSession,
        supplier_id: uuid.UUID,
        product_id: uuid.UUID,
        supply_price: Optional[float] = None,
    ) -> bool:
        """
        Link a supplier to a product (many-to-many relationship).

        Args:
            session: AsyncSession for database operations
            supplier_id: UUID of the supplier
            product_id: UUID of the product
            supply_price: Optional price at which supplier provides this product

        Returns:
            True if link was successful, False otherwise
        """
        try:
            # Check if supplier exists
            supplier = await self.get_by_id(session, supplier_id)
            if not supplier:
                self._logger.warning(
                    f"Supplier not found for linking: {supplier_id}",
                    extra=create_owasp_log_context(
                        user="system",
                        action="link_product_supplier_not_found",
                        location="SupplierRepository.link_product",
                    ),
                )
                return False

            # Check if product exists
            product_result = await session.execute(
                select(Product).where(Product.id == product_id)
            )
            product = product_result.scalar_one_or_none()
            if not product:
                self._logger.warning(
                    f"Product not found for linking: {product_id}",
                    extra=create_owasp_log_context(
                        user="system",
                        action="link_product_product_not_found",
                        location="SupplierRepository.link_product",
                    ),
                )
                return False

            # Check if link already exists
            check_query = select(supplier_product).where(
                and_(
                    supplier_product.c.supplier_id == supplier_id,
                    supplier_product.c.product_id == product_id,
                )
            )
            existing = await session.execute(check_query)
            if existing.first():
                self._logger.warning(
                    f"Supplier {supplier_id} already linked to product {product_id}",
                    extra=create_owasp_log_context(
                        user="system",
                        action="link_product_already_exists",
                        location="SupplierRepository.link_product",
                    ),
                )
                return False

            # Create the link
            insert_stmt = supplier_product.insert().values(
                supplier_id=supplier_id,
                product_id=product_id,
                supply_price=supply_price,
                created_at=datetime.utcnow(),
            )
            await session.execute(insert_stmt)
            await session.commit()

            self._logger.info(
                f"Supplier {supplier_id} linked to product {product_id}",
                extra=create_owasp_log_context(
                    user="system",
                    action="link_product_success",
                    location="SupplierRepository.link_product",
                ),
            )

            return True

        except SQLAlchemyError as e:
            await session.rollback()
            error_msg = f"Database error while linking supplier to product: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="link_product_db_error",
                    location="SupplierRepository.link_product",
                ),
            )
            return False

    async def unlink_product(
        self,
        session: AsyncSession,
        supplier_id: uuid.UUID,
        product_id: uuid.UUID,
    ) -> bool:
        """
        Unlink a supplier from a product.

        Args:
            session: AsyncSession for database operations
            supplier_id: UUID of the supplier
            product_id: UUID of the product

        Returns:
            True if unlink was successful, False otherwise
        """
        try:
            delete_stmt = delete(supplier_product).where(
                and_(
                    supplier_product.c.supplier_id == supplier_id,
                    supplier_product.c.product_id == product_id,
                )
            )
            result = await session.execute(delete_stmt)
            await session.commit()

            if result.rowcount == 0:
                self._logger.warning(
                    f"No link found between supplier {supplier_id} and product {product_id}",
                    extra=create_owasp_log_context(
                        user="system",
                        action="unlink_product_not_found",
                        location="SupplierRepository.unlink_product",
                    ),
                )
                return False

            self._logger.info(
                f"Supplier {supplier_id} unlinked from product {product_id}",
                extra=create_owasp_log_context(
                    user="system",
                    action="unlink_product_success",
                    location="SupplierRepository.unlink_product",
                ),
            )

            return True

        except SQLAlchemyError as e:
            await session.rollback()
            error_msg = (
                f"Database error while unlinking supplier from product: {str(e)}"
            )
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="unlink_product_db_error",
                    location="SupplierRepository.unlink_product",
                ),
            )
            return False

    async def get_supplier_products(
        self, session: AsyncSession, supplier_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """
        Get all products supplied by a specific supplier.

        Args:
            session: AsyncSession for database operations
            supplier_id: UUID of the supplier

        Returns:
            List of dictionaries containing product info and supply details
        """
        try:
            query = (
                select(
                    Product.id,
                    Product.name,
                    Product.category,
                    Product.price,
                    supplier_product.c.supply_price,
                    supplier_product.c.last_supplied_date,
                )
                .join(supplier_product, Product.id == supplier_product.c.product_id)
                .where(supplier_product.c.supplier_id == supplier_id)
            )

            result = await session.execute(query)
            products = []

            for row in result:
                products.append(
                    {
                        "product_id": str(row.id),
                        "product_name": row.name,
                        "category": row.category.value if row.category else None,
                        "retail_price": row.price,
                        "supply_price": row.supply_price,
                        "last_supplied_date": row.last_supplied_date,
                    }
                )

            self._logger.info(
                f"Retrieved {len(products)} products for supplier {supplier_id}",
                extra=create_owasp_log_context(
                    user="system",
                    action="get_supplier_products_success",
                    location="SupplierRepository.get_supplier_products",
                ),
            )

            return products

        except SQLAlchemyError as e:
            error_msg = f"Database error while getting supplier products: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="get_supplier_products_db_error",
                    location="SupplierRepository.get_supplier_products",
                ),
            )
            return []

    async def update_last_purchase_date(
        self, session: AsyncSession, supplier_id: uuid.UUID, purchase_date: datetime
    ) -> bool:
        """
        Update the last purchase date for a supplier.

        Args:
            session: AsyncSession for database operations
            supplier_id: UUID of the supplier
            purchase_date: Date of the purchase

        Returns:
            True if update was successful, False otherwise
        """
        try:
            supplier = await self.update(
                session, supplier_id, {"last_purchase_date": purchase_date}
            )

            if supplier:
                self._logger.info(
                    f"Updated last purchase date for supplier {supplier_id}",
                    extra=create_owasp_log_context(
                        user="system",
                        action="update_last_purchase_date_success",
                        location="SupplierRepository.update_last_purchase_date",
                    ),
                )
                return True

            return False

        except Exception as e:
            error_msg = f"Error updating last purchase date: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="update_last_purchase_date_error",
                    location="SupplierRepository.update_last_purchase_date",
                ),
            )
            return False
