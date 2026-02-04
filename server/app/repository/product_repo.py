import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.models.product_model import Product
from app.constants import ProductCategory
from app.config.logging import get_logger, create_owasp_log_context


class ProductRepository:
    """
    Singleton repository for Product CRUD operations.
    Implements comprehensive logging and error handling for production use.
    """

    _instance: Optional["ProductRepository"] = None
    _logger = None

    def __new__(cls):
        """Singleton pattern implementation"""
        if cls._instance is None:
            cls._instance = super(ProductRepository, cls).__new__(cls)
            cls._logger = get_logger(__name__)
            cls._logger.info(
                "ProductRepository singleton instance created",
                extra=create_owasp_log_context(
                    user="system",
                    action="repository_initialization",
                    location="ProductRepository.__new__",
                ),
            )
        return cls._instance

    async def create(
        self, session: AsyncSession, product_data: Dict[str, Any]
    ) -> Optional[Product]:
        """
        Create a new product.

        Args:
            session: AsyncSession for database operations
            product_data: Dictionary containing product information

        Returns:
            Created Product object or None if creation fails

        Raises:
            ValueError: If required fields are missing or invalid
        """
        try:
            # Validate required fields
            required_fields = [
                "name",
                "price",
                "stock_qty",
                "category",
                "description",
                "brand",
                "image_url",
            ]
            missing_fields = [
                field for field in required_fields if field not in product_data
            ]

            if missing_fields:
                error_msg = f"Missing required fields: {', '.join(missing_fields)}"
                self._logger.error(
                    error_msg,
                    extra=create_owasp_log_context(
                        user="system",
                        action="create_product_validation_failed",
                        location="ProductRepository.create",
                    ),
                )
                raise ValueError(error_msg)

            # Convert category string to enum if provided
            if "category" in product_data and isinstance(product_data["category"], str):
                try:
                    product_data["category"] = ProductCategory[
                        product_data["category"].upper()
                    ]
                except KeyError:
                    error_msg = f"Invalid category: {product_data['category']}"
                    self._logger.warning(
                        error_msg,
                        extra=create_owasp_log_context(
                            user="system",
                            action="create_product_invalid_category",
                            location="ProductRepository.create",
                        ),
                    )
                    raise ValueError(error_msg)

            # Create product instance
            product = Product(**product_data)
            session.add(product)
            await session.commit()
            await session.refresh(product)

            self._logger.info(
                f"Product created successfully: {product.id} - {product.name}",
                extra=create_owasp_log_context(
                    user="system",
                    action="create_product_success",
                    location="ProductRepository.create",
                ),
            )

            return product

        except IntegrityError as e:
            await session.rollback()
            error_msg = f"Database integrity error while creating product: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="create_product_integrity_error",
                    location="ProductRepository.create",
                ),
            )
            raise ValueError(error_msg)

        except SQLAlchemyError as e:
            await session.rollback()
            error_msg = f"Database error while creating product: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="create_product_db_error",
                    location="ProductRepository.create",
                ),
            )
            return None

        except Exception as e:
            await session.rollback()
            error_msg = f"Unexpected error while creating product: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="create_product_unexpected_error",
                    location="ProductRepository.create",
                ),
            )
            return None

    async def get_by_id(
        self, session: AsyncSession, product_id: uuid.UUID
    ) -> Optional[Product]:
        """
        Retrieve a product by its ID.

        Args:
            session: AsyncSession for database operations
            product_id: UUID of the product

        Returns:
            Product object or None if not found
        """
        try:
            result = await session.execute(
                select(Product).where(Product.id == product_id)
            )
            product = result.scalar_one_or_none()

            if product:
                self._logger.info(
                    f"Product retrieved: {product_id}",
                    extra=create_owasp_log_context(
                        user="system",
                        action="get_product_by_id_success",
                        location="ProductRepository.get_by_id",
                    ),
                )
            else:
                self._logger.warning(
                    f"Product not found: {product_id}",
                    extra=create_owasp_log_context(
                        user="system",
                        action="get_product_by_id_not_found",
                        location="ProductRepository.get_by_id",
                    ),
                )

            return product

        except SQLAlchemyError as e:
            error_msg = (
                f"Database error while retrieving product {product_id}: {str(e)}"
            )
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="get_product_by_id_db_error",
                    location="ProductRepository.get_by_id",
                ),
            )
            return None

    async def get_all(
        self,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> List[Product]:
        """
        Retrieve all products with pagination.

        Args:
            session: AsyncSession for database operations
            skip: Number of records to skip
            limit: Maximum number of records to return
            include_inactive: Whether to include inactive products

        Returns:
            List of Product objects
        """
        try:
            query = select(Product)

            if not include_inactive:
                query = query.where(Product.is_active == True)

            query = query.offset(skip).limit(limit).order_by(Product.created_at.desc())

            result = await session.execute(query)
            products = result.scalars().all()

            self._logger.info(
                f"Retrieved {len(products)} products (skip={skip}, limit={limit})",
                extra=create_owasp_log_context(
                    user="system",
                    action="get_all_products_success",
                    location="ProductRepository.get_all",
                ),
            )

            return list(products)

        except SQLAlchemyError as e:
            error_msg = f"Database error while retrieving products: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="get_all_products_db_error",
                    location="ProductRepository.get_all",
                ),
            )
            return []

    async def update(
        self,
        session: AsyncSession,
        product_id: uuid.UUID,
        update_data: Dict[str, Any],
    ) -> Optional[Product]:
        """
        Update a product.

        Args:
            session: AsyncSession for database operations
            product_id: UUID of the product to update
            update_data: Dictionary containing fields to update

        Returns:
            Updated Product object or None if update fails
        """
        try:
            # Convert category string to enum if provided
            if "category" in update_data and isinstance(update_data["category"], str):
                try:
                    update_data["category"] = ProductCategory[
                        update_data["category"].upper()
                    ]
                except KeyError:
                    error_msg = f"Invalid category: {update_data['category']}"
                    self._logger.warning(
                        error_msg,
                        extra=create_owasp_log_context(
                            user="system",
                            action="update_product_invalid_category",
                            location="ProductRepository.update",
                        ),
                    )
                    raise ValueError(error_msg)

            # Remove None values and id field if present
            update_data = {
                k: v for k, v in update_data.items() if v is not None and k != "id"
            }

            if not update_data:
                self._logger.warning(
                    f"No valid fields to update for product {product_id}",
                    extra=create_owasp_log_context(
                        user="system",
                        action="update_product_no_fields",
                        location="ProductRepository.update",
                    ),
                )
                return await self.get_by_id(session, product_id)

            stmt = (
                update(Product)
                .where(Product.id == product_id)
                .values(**update_data)
                .execution_options(synchronize_session="fetch")
            )

            result = await session.execute(stmt)
            await session.commit()

            if result.rowcount == 0:
                self._logger.warning(
                    f"Product not found for update: {product_id}",
                    extra=create_owasp_log_context(
                        user="system",
                        action="update_product_not_found",
                        location="ProductRepository.update",
                    ),
                )
                return None

            updated_product = await self.get_by_id(session, product_id)

            self._logger.info(
                f"Product updated successfully: {product_id}",
                extra=create_owasp_log_context(
                    user="system",
                    action="update_product_success",
                    location="ProductRepository.update",
                ),
            )

            return updated_product

        except IntegrityError as e:
            await session.rollback()
            error_msg = f"Database integrity error while updating product {product_id}: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="update_product_integrity_error",
                    location="ProductRepository.update",
                ),
            )
            raise ValueError(error_msg)

        except SQLAlchemyError as e:
            await session.rollback()
            error_msg = f"Database error while updating product {product_id}: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="update_product_db_error",
                    location="ProductRepository.update",
                ),
            )
            return None

    async def delete(self, session: AsyncSession, product_id: uuid.UUID) -> bool:
        """
        Hard delete a product from the database.

        Args:
            session: AsyncSession for database operations
            product_id: UUID of the product to delete

        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            stmt = delete(Product).where(Product.id == product_id)
            result = await session.execute(stmt)
            await session.commit()

            if result.rowcount == 0:
                self._logger.warning(
                    f"Product not found for deletion: {product_id}",
                    extra=create_owasp_log_context(
                        user="system",
                        action="delete_product_not_found",
                        location="ProductRepository.delete",
                    ),
                )
                return False

            self._logger.info(
                f"Product deleted successfully: {product_id}",
                extra=create_owasp_log_context(
                    user="system",
                    action="delete_product_success",
                    location="ProductRepository.delete",
                ),
            )

            return True

        except SQLAlchemyError as e:
            await session.rollback()
            error_msg = f"Database error while deleting product {product_id}: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="delete_product_db_error",
                    location="ProductRepository.delete",
                ),
            )
            return False

    async def soft_delete(self, session: AsyncSession, product_id: uuid.UUID) -> bool:
        """
        Soft delete a product by setting is_active to False.

        Args:
            session: AsyncSession for database operations
            product_id: UUID of the product to soft delete

        Returns:
            True if soft deletion was successful, False otherwise
        """
        try:
            updated_product = await self.update(
                session, product_id, {"is_active": False}
            )

            if updated_product:
                self._logger.info(
                    f"Product soft deleted successfully: {product_id}",
                    extra=create_owasp_log_context(
                        user="system",
                        action="soft_delete_product_success",
                        location="ProductRepository.soft_delete",
                    ),
                )
                return True

            return False

        except Exception as e:
            error_msg = f"Error while soft deleting product {product_id}: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="soft_delete_product_error",
                    location="ProductRepository.soft_delete",
                ),
            )
            return False

    async def filter_products(
        self,
        session: AsyncSession,
        filters: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
    ) -> List[Product]:
        """
        Filter products based on various criteria.

        Args:
            session: AsyncSession for database operations
            filters: Dictionary of filter criteria
                - category: ProductCategory or list of categories
                - brand: Brand name (exact match)
                - min_price: Minimum price
                - max_price: Maximum price
                - min_stock: Minimum stock quantity
                - max_stock: Maximum stock quantity
                - is_active: Active status
                - search: Search term for name/description
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of filtered Product objects
        """
        try:
            query = select(Product)
            conditions = []

            # Category filter
            if "category" in filters:
                category = filters["category"]
                if isinstance(category, list):
                    # Convert string categories to enums
                    enum_categories = []
                    for cat in category:
                        if isinstance(cat, str):
                            try:
                                enum_categories.append(ProductCategory[cat.upper()])
                            except KeyError:
                                self._logger.warning(
                                    f"Invalid category in filter: {cat}",
                                    extra=create_owasp_log_context(
                                        user="system",
                                        action="filter_products_invalid_category",
                                        location="ProductRepository.filter_products",
                                    ),
                                )
                        else:
                            enum_categories.append(cat)
                    conditions.append(Product.category.in_(enum_categories))
                else:
                    if isinstance(category, str):
                        try:
                            category = ProductCategory[category.upper()]
                        except KeyError:
                            self._logger.warning(
                                f"Invalid category in filter: {category}",
                                extra=create_owasp_log_context(
                                    user="system",
                                    action="filter_products_invalid_category",
                                    location="ProductRepository.filter_products",
                                ),
                            )
                            return []
                    conditions.append(Product.category == category)

            # Brand filter
            if "brand" in filters:
                conditions.append(Product.brand == filters["brand"])

            # Price range filters
            if "min_price" in filters:
                conditions.append(Product.price >= filters["min_price"])
            if "max_price" in filters:
                conditions.append(Product.price <= filters["max_price"])

            # Stock quantity filters
            if "min_stock" in filters:
                conditions.append(Product.stock_qty >= filters["min_stock"])
            if "max_stock" in filters:
                conditions.append(Product.stock_qty <= filters["max_stock"])

            # Active status filter
            if "is_active" in filters:
                conditions.append(Product.is_active == filters["is_active"])
            else:
                # By default, only show active products
                conditions.append(Product.is_active == True)

            # Search filter (name or description)
            if "search" in filters and filters["search"]:
                search_term = f"%{filters['search']}%"
                conditions.append(
                    or_(
                        Product.name.ilike(search_term),
                        Product.description.ilike(search_term),
                    )
                )

            # Apply all conditions
            if conditions:
                query = query.where(and_(*conditions))

            # Apply pagination and ordering
            query = query.offset(skip).limit(limit).order_by(Product.created_at.desc())

            result = await session.execute(query)
            products = result.scalars().all()

            self._logger.info(
                f"Filtered products: {len(products)} results (filters={filters})",
                extra=create_owasp_log_context(
                    user="system",
                    action="filter_products_success",
                    location="ProductRepository.filter_products",
                ),
            )

            return list(products)

        except SQLAlchemyError as e:
            error_msg = f"Database error while filtering products: {str(e)}"
            self._logger.error(
                error_msg,
                extra=create_owasp_log_context(
                    user="system",
                    action="filter_products_db_error",
                    location="ProductRepository.filter_products",
                ),
            )
            return []

    async def get_by_category(
        self,
        session: AsyncSession,
        category: ProductCategory,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Product]:
        """
        Get all products in a specific category.

        Args:
            session: AsyncSession for database operations
            category: ProductCategory enum value
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Product objects in the specified category
        """
        return await self.filter_products(
            session, filters={"category": category}, skip=skip, limit=limit
        )

    async def get_low_stock_products(
        self, session: AsyncSession, threshold: int = 10, limit: int = 100
    ) -> List[Product]:
        """
        Get products with stock quantity below a threshold.

        Args:
            session: AsyncSession for database operations
            threshold: Stock quantity threshold
            limit: Maximum number of records to return

        Returns:
            List of Product objects with low stock
        """
        return await self.filter_products(
            session, filters={"max_stock": threshold}, limit=limit
        )

    async def search_products(
        self, session: AsyncSession, search_term: str, skip: int = 0, limit: int = 100
    ) -> List[Product]:
        """
        Search products by name or description.

        Args:
            session: AsyncSession for database operations
            search_term: Search term
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of matching Product objects
        """
        return await self.filter_products(
            session, filters={"search": search_term}, skip=skip, limit=limit
        )
