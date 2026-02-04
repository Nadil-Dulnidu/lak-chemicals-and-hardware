from typing import Optional, Dict, Any
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.repository.product_repo import ProductRepository
from app.constants import ProductCategory
from app.schemas.product_schema import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
    ProductFilterParams,
    LowStockAlert,
)
from app.config.logging import get_logger, create_owasp_log_context


class ProductService:
    """
    Service layer for Product business logic.
    Handles validation, business rules, orchestration, and data transformation.
    """

    def __init__(self):
        self.repo = ProductRepository()
        self._logger = get_logger(__name__)

    async def create_product(
        self,
        session: AsyncSession,
        product_data: ProductCreate,
        user_id: Optional[str] = None,
    ) -> Optional[ProductResponse]:
        """
        Create a new product with business validation.

        Args:
            session: Database session
            product_data: Validated product data from Pydantic schema
            user_id: Optional user ID for audit logging

        Returns:
            ProductResponse or None if creation fails

        Raises:
            ValueError: If business validation fails
        """
        try:
            self._logger.info(
                f"Creating product: {product_data.name}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="create_product",
                    location="ProductService.create_product",
                ),
            )

            # Convert Pydantic model to dict
            product_dict = product_data.model_dump(exclude_unset=True)

            # Convert category enum to string for repository
            if "category" in product_dict and product_dict["category"]:
                product_dict["category"] = product_dict["category"].upper()

            # Call repository
            product = await self.repo.create(session, product_dict)

            if product:
                # Post-creation business logic
                await self._check_and_log_low_stock(product, user_id)

                self._logger.info(
                    f"Product created successfully: {product.id}",
                    extra=create_owasp_log_context(
                        user=user_id or "system",
                        action="create_product_success",
                        location="ProductService.create_product",
                    ),
                )

                return self._to_response(product)

            return None

        except ValueError as e:
            self._logger.error(
                f"Validation error creating product: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="create_product_validation_error",
                    location="ProductService.create_product",
                ),
            )
            raise

        except Exception as e:
            self._logger.error(
                f"Service error creating product: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="create_product_error",
                    location="ProductService.create_product",
                ),
            )
            raise

    async def get_product(
        self,
        session: AsyncSession,
        product_id: uuid.UUID,
        user_id: Optional[str] = None,
    ) -> Optional[ProductResponse]:
        """
        Get product by ID.

        Args:
            session: Database session
            product_id: Product UUID
            user_id: Optional user ID for audit logging

        Returns:
            ProductResponse or None if not found
        """
        try:
            product = await self.repo.get_by_id(session, product_id)

            if product:
                self._logger.info(
                    f"Product retrieved: {product_id}",
                    extra=create_owasp_log_context(
                        user=user_id or "system",
                        action="get_product",
                        location="ProductService.get_product",
                    ),
                )
                return self._to_response(product)

            self._logger.warning(
                f"Product not found: {product_id}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="get_product_not_found",
                    location="ProductService.get_product",
                ),
            )
            return None

        except Exception as e:
            self._logger.error(
                f"Service error getting product: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="get_product_error",
                    location="ProductService.get_product",
                ),
            )
            return None

    async def get_all_products(
        self,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
        user_id: Optional[str] = None,
    ) -> ProductListResponse:
        """
        Get all products with pagination.

        Args:
            session: Database session
            skip: Number of records to skip
            limit: Maximum records to return
            include_inactive: Whether to include inactive products
            user_id: Optional user ID for audit logging

        Returns:
            ProductListResponse with products and metadata
        """
        try:
            products = await self.repo.get_all(session, skip, limit, include_inactive)

            self._logger.info(
                f"Retrieved {len(products)} products",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="get_all_products",
                    location="ProductService.get_all_products",
                ),
            )

            return ProductListResponse(
                products=[self._to_response(p) for p in products],
                total=len(products),
                skip=skip,
                limit=limit,
                has_more=len(products) == limit,
            )

        except Exception as e:
            self._logger.error(
                f"Service error getting all products: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="get_all_products_error",
                    location="ProductService.get_all_products",
                ),
            )
            return ProductListResponse(
                products=[], total=0, skip=skip, limit=limit, has_more=False
            )

    async def update_product(
        self,
        session: AsyncSession,
        product_id: uuid.UUID,
        update_data: ProductUpdate,
        user_id: Optional[str] = None,
    ) -> Optional[ProductResponse]:
        """
        Update a product with business validation.

        Args:
            session: Database session
            product_id: Product UUID
            update_data: Validated update data from Pydantic schema
            user_id: Optional user ID for audit logging

        Returns:
            ProductResponse or None if update fails
        """
        try:
            # Get current product for comparison
            current_product = await self.repo.get_by_id(session, product_id)
            if not current_product:
                self._logger.warning(
                    f"Product not found for update: {product_id}",
                    extra=create_owasp_log_context(
                        user=user_id or "system",
                        action="update_product_not_found",
                        location="ProductService.update_product",
                    ),
                )
                return None

            # Convert Pydantic model to dict, excluding unset fields
            update_dict = update_data.model_dump(exclude_unset=True)

            # Convert category enum to string for repository
            if "category" in update_dict and update_dict["category"]:
                update_dict["category"] = update_dict["category"].upper()

            # Business logic: Log significant stock changes
            if "stock_qty" in update_dict:
                old_stock = current_product.stock_qty
                new_stock = update_dict["stock_qty"]

                if new_stock < old_stock * 0.5:  # 50% reduction
                    self._logger.warning(
                        f"Significant stock reduction for product {product_id}: {old_stock} -> {new_stock}",
                        extra=create_owasp_log_context(
                            user=user_id or "system",
                            action="stock_reduction_warning",
                            location="ProductService.update_product",
                        ),
                    )

            # Business logic: Log price changes
            if "price" in update_dict:
                old_price = current_product.price
                new_price = update_dict["price"]

                if abs(new_price - old_price) / old_price > 0.2:  # 20% change
                    self._logger.info(
                        f"Significant price change for product {product_id}: {old_price} -> {new_price}",
                        extra=create_owasp_log_context(
                            user=user_id or "system",
                            action="price_change_notification",
                            location="ProductService.update_product",
                        ),
                    )

            # Update via repository
            updated_product = await self.repo.update(session, product_id, update_dict)

            if updated_product:
                await self._check_and_log_low_stock(updated_product, user_id)

                self._logger.info(
                    f"Product updated successfully: {product_id}",
                    extra=create_owasp_log_context(
                        user=user_id or "system",
                        action="update_product_success",
                        location="ProductService.update_product",
                    ),
                )

                return self._to_response(updated_product)

            return None

        except ValueError as e:
            self._logger.error(
                f"Validation error updating product: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="update_product_validation_error",
                    location="ProductService.update_product",
                ),
            )
            raise

        except Exception as e:
            self._logger.error(
                f"Service error updating product: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="update_product_error",
                    location="ProductService.update_product",
                ),
            )
            raise

    async def delete_product(
        self,
        session: AsyncSession,
        product_id: uuid.UUID,
        soft: bool = True,
        user_id: Optional[str] = None,
    ) -> bool:
        """
        Delete a product (soft or hard delete).

        Args:
            session: Database session
            product_id: Product UUID
            soft: If True, perform soft delete; otherwise hard delete
            user_id: Optional user ID for audit logging

        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            delete_type = "soft" if soft else "hard"

            self._logger.info(
                f"Attempting {delete_type} delete of product: {product_id}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action=f"{delete_type}_delete_product",
                    location="ProductService.delete_product",
                ),
            )

            if soft:
                success = await self.repo.soft_delete(session, product_id)
            else:
                success = await self.repo.delete(session, product_id)

            if success:
                self._logger.info(
                    f"Product {delete_type} deleted successfully: {product_id}",
                    extra=create_owasp_log_context(
                        user=user_id or "system",
                        action=f"{delete_type}_delete_product_success",
                        location="ProductService.delete_product",
                    ),
                )
            else:
                self._logger.warning(
                    f"Product not found for {delete_type} deletion: {product_id}",
                    extra=create_owasp_log_context(
                        user=user_id or "system",
                        action=f"{delete_type}_delete_product_not_found",
                        location="ProductService.delete_product",
                    ),
                )

            return success

        except Exception as e:
            self._logger.error(
                f"Service error deleting product: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="delete_product_error",
                    location="ProductService.delete_product",
                ),
            )
            return False

        """
        Filter products based on various criteria.

        Args:
            session: Database session
            filter_params: Validated filter parameters
            user_id: Optional user ID for audit logging

        Returns:
            ProductListResponse with filtered products and metadata
        """
        try:
            # Convert Pydantic model to dict for repository
            filters = filter_params.model_dump(
                exclude={"skip", "limit"}, exclude_unset=True
            )

            # Convert category enums to strings
            if "category" in filters and filters["category"]:
                filters["category"] = [cat.upper() for cat in filters["category"]]

            products = await self.repo.filter_products(
                session, filters, filter_params.skip, filter_params.limit
            )

            self._logger.info(
                f"Filtered products: {len(products)} results",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="filter_products",
                    location="ProductService.filter_products",
                ),
            )

            return ProductListResponse(
                products=[self._to_response(p) for p in products],
                total=len(products),
                skip=filter_params.skip,
                limit=filter_params.limit,
                has_more=len(products) == filter_params.limit,
            )

        except Exception as e:
            self._logger.error(
                f"Service error filtering products: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="filter_products_error",
                    location="ProductService.filter_products",
                ),
            )
            return ProductListResponse(
                products=[],
                total=0,
                skip=filter_params.skip,
                limit=filter_params.limit,
                has_more=False,
            )

    async def search_products(
        self,
        session: AsyncSession,
        search_term: str,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[str] = None,
    ) -> ProductListResponse:
        """
        Search products by name or description.

        Args:
            session: Database session
            search_term: Search term
            skip: Number of records to skip
            limit: Maximum records to return
            user_id: Optional user ID for audit logging

        Returns:
            ProductListResponse with search results
        """
        try:
            products = await self.repo.search_products(
                session, search_term, skip, limit
            )

            self._logger.info(
                f"Search results for '{search_term}': {len(products)} products found",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="search_products",
                    location="ProductService.search_products",
                ),
            )

            return ProductListResponse(
                products=[self._to_response(p) for p in products],
                total=len(products),
                skip=skip,
                limit=limit,
                has_more=len(products) == limit,
            )

        except Exception as e:
            self._logger.error(
                f"Service error searching products: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="search_products_error",
                    location="ProductService.search_products",
                ),
            )
            return ProductListResponse(
                products=[], total=0, skip=skip, limit=limit, has_more=False
            )

    async def get_products_by_category(
        self,
        session: AsyncSession,
        category: str,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[str] = None,
    ) -> ProductListResponse:
        """
        Get all products in a specific category.

        Args:
            session: Database session
            category: Category name (string)
            skip: Number of records to skip
            limit: Maximum records to return
            user_id: Optional user ID for audit logging

        Returns:
            ProductListResponse with category products
        """
        try:
            # Convert string to ProductCategory enum
            category_enum = ProductCategory[category.upper()]

            products = await self.repo.get_by_category(
                session, category_enum, skip, limit
            )

            self._logger.info(
                f"Retrieved {len(products)} products in category '{category}'",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="get_products_by_category",
                    location="ProductService.get_products_by_category",
                ),
            )

            return ProductListResponse(
                products=[self._to_response(p) for p in products],
                total=len(products),
                skip=skip,
                limit=limit,
                has_more=len(products) == limit,
            )

        except KeyError:
            self._logger.warning(
                f"Invalid category: {category}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="get_products_by_category_invalid",
                    location="ProductService.get_products_by_category",
                ),
            )
            return ProductListResponse(
                products=[], total=0, skip=skip, limit=limit, has_more=False
            )

        except Exception as e:
            self._logger.error(
                f"Service error getting products by category: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="get_products_by_category_error",
                    location="ProductService.get_products_by_category",
                ),
            )
            return ProductListResponse(
                products=[], total=0, skip=skip, limit=limit, has_more=False
            )

    async def get_low_stock_alerts(
        self,
        session: AsyncSession,
        threshold: int = 10,
        limit: int = 100,
        user_id: Optional[str] = None,
    ) -> list[LowStockAlert]:
        """
        Get products with low stock that need restocking.

        Args:
            session: Database session
            threshold: Stock quantity threshold
            limit: Maximum records to return
            user_id: Optional user ID for audit logging

        Returns:
            List of LowStockAlert objects with priority information
        """
        try:
            products = await self.repo.get_low_stock_products(session, threshold, limit)

            alerts = []
            for product in products:
                # Calculate priority based on stock level
                if product.stock_qty == 0:
                    priority = "critical"
                elif product.stock_qty < 5:
                    priority = "high"
                elif product.stock_qty < threshold * 0.5:
                    priority = "medium"
                else:
                    priority = "low"

                alert = LowStockAlert(
                    id=str(product.id),
                    name=product.name,
                    description=product.description,
                    brand=product.brand,
                    category=product.category.value if product.category else None,
                    price=product.price,
                    stock_qty=product.stock_qty,
                    image_url=product.image_url,
                    created_at=product.created_at,
                    is_active=product.is_active,
                    restock_needed=max(0, threshold - product.stock_qty),
                    priority=priority,
                )
                alerts.append(alert)

            self._logger.info(
                f"Low stock alerts: {len(alerts)} products below threshold {threshold}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="get_low_stock_alerts",
                    location="ProductService.get_low_stock_alerts",
                ),
            )

            return alerts

        except Exception as e:
            self._logger.error(
                f"Service error getting low stock alerts: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="get_low_stock_alerts_error",
                    location="ProductService.get_low_stock_alerts",
                ),
            )
            return []

    def _to_response(self, product) -> ProductResponse:
        """
        Convert Product model to ProductResponse schema.

        Args:
            product: Product model instance

        Returns:
            ProductResponse schema
        """
        return ProductResponse(
            id=str(product.id),
            name=product.name,
            description=product.description,
            brand=product.brand,
            category=product.category.value if product.category else None,
            price=product.price,
            stock_qty=product.stock_qty,
            image_url=product.image_url,
            created_at=product.created_at,
            is_active=product.is_active,
        )

    async def _check_and_log_low_stock(self, product, user_id: Optional[str] = None):
        """
        Business logic: Check and log if product stock is low.

        Args:
            product: Product model instance
            user_id: Optional user ID for audit logging
        """
        if product.stock_qty < 10:
            priority = (
                "critical"
                if product.stock_qty == 0
                else "high" if product.stock_qty < 5 else "medium"
            )

            self._logger.warning(
                f"Low stock alert: {product.name} (qty: {product.stock_qty}, priority: {priority})",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="low_stock_alert",
                    location="ProductService._check_and_log_low_stock",
                ),
            )
            # Here you could trigger additional actions:
            # - Send email notification
            # - Create notification in database
            # - Trigger webhook
            # - Update dashboard metrics
