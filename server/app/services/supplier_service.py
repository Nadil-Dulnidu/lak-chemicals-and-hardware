from typing import Optional, List
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.repository.supplier_repo import SupplierRepository
from app.schemas.supplier_schema import (
    SupplierCreate,
    SupplierUpdate,
    SupplierResponse,
    SupplierListResponse,
    SupplierFilterParams,
    SupplierProductLink,
    SupplierDetailResponse,
    ProductSupplierInfo,
)
from app.config.logging import get_logger, create_owasp_log_context


class SupplierService:
    """
    Service layer for Supplier business logic.
    Handles validation, business rules, orchestration, and data transformation.
    """

    def __init__(self):
        self.repo = SupplierRepository()
        self._logger = get_logger(__name__)

    async def create_supplier(
        self,
        session: AsyncSession,
        supplier_data: SupplierCreate,
        user_id: Optional[str] = None,
    ) -> Optional[SupplierResponse]:
        """
        Create a new supplier with business validation.

        Args:
            session: Database session
            supplier_data: Validated supplier data from Pydantic schema
            user_id: Optional user ID for audit logging

        Returns:
            SupplierResponse or None if creation fails

        Raises:
            ValueError: If business validation fails
        """
        try:
            self._logger.info(
                f"Creating supplier: {supplier_data.name}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="create_supplier",
                    location="SupplierService.create_supplier",
                ),
            )

            # Convert Pydantic model to dict
            supplier_dict = supplier_data.model_dump(exclude_unset=True)

            # Call repository
            supplier = await self.repo.create(session, supplier_dict)

            if supplier:
                self._logger.info(
                    f"Supplier created successfully: {supplier.id}",
                    extra=create_owasp_log_context(
                        user=user_id or "system",
                        action="create_supplier_success",
                        location="SupplierService.create_supplier",
                    ),
                )

                return self._to_response(supplier)

            return None

        except ValueError as e:
            self._logger.error(
                f"Validation error creating supplier: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="create_supplier_validation_error",
                    location="SupplierService.create_supplier",
                ),
            )
            raise

        except Exception as e:
            self._logger.error(
                f"Service error creating supplier: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="create_supplier_error",
                    location="SupplierService.create_supplier",
                ),
            )
            raise

    async def get_supplier(
        self,
        session: AsyncSession,
        supplier_id: uuid.UUID,
        user_id: Optional[str] = None,
    ) -> Optional[SupplierResponse]:
        """
        Get supplier by ID.

        Args:
            session: Database session
            supplier_id: Supplier UUID
            user_id: Optional user ID for audit logging

        Returns:
            SupplierResponse or None if not found
        """
        try:
            supplier = await self.repo.get_by_id(session, supplier_id)

            if supplier:
                self._logger.info(
                    f"Supplier retrieved: {supplier_id}",
                    extra=create_owasp_log_context(
                        user=user_id or "system",
                        action="get_supplier",
                        location="SupplierService.get_supplier",
                    ),
                )
                return self._to_response(supplier)

            self._logger.warning(
                f"Supplier not found: {supplier_id}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="get_supplier_not_found",
                    location="SupplierService.get_supplier",
                ),
            )
            return None

        except Exception as e:
            self._logger.error(
                f"Service error getting supplier: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="get_supplier_error",
                    location="SupplierService.get_supplier",
                ),
            )
            return None

    async def get_supplier_detail(
        self,
        session: AsyncSession,
        supplier_id: uuid.UUID,
        user_id: Optional[str] = None,
    ) -> Optional[SupplierDetailResponse]:
        """
        Get supplier with detailed product information.

        Args:
            session: Database session
            supplier_id: Supplier UUID
            user_id: Optional user ID for audit logging

        Returns:
            SupplierDetailResponse with products or None if not found
        """
        try:
            supplier = await self.repo.get_by_id(session, supplier_id)

            if not supplier:
                return None

            # Get supplier products
            products = await self.repo.get_supplier_products(session, supplier_id)

            # Convert to ProductSupplierInfo
            product_infos = [
                ProductSupplierInfo(
                    product_id=p["product_id"],
                    product_name=p["product_name"],
                    supply_price=p["supply_price"],
                    last_supplied_date=p["last_supplied_date"],
                )
                for p in products
            ]

            return SupplierDetailResponse(
                id=str(supplier.id),
                name=supplier.name,
                contact_person=supplier.contact_person,
                contact_number=supplier.contact_number,
                email=supplier.email,
                address=supplier.address,
                created_at=supplier.created_at,
                last_purchase_date=supplier.last_purchase_date,
                is_active=supplier.is_active,
                products=product_infos,
            )

        except Exception as e:
            self._logger.error(
                f"Service error getting supplier detail: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="get_supplier_detail_error",
                    location="SupplierService.get_supplier_detail",
                ),
            )
            return None

    async def get_all_suppliers(
        self,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
        user_id: Optional[str] = None,
    ) -> SupplierListResponse:
        """
        Get all suppliers with pagination.

        Args:
            session: Database session
            skip: Number of records to skip
            limit: Maximum records to return
            include_inactive: Whether to include inactive suppliers
            user_id: Optional user ID for audit logging

        Returns:
            SupplierListResponse with suppliers and metadata
        """
        try:
            suppliers = await self.repo.get_all(session, skip, limit, include_inactive)

            self._logger.info(
                f"Retrieved {len(suppliers)} suppliers",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="get_all_suppliers",
                    location="SupplierService.get_all_suppliers",
                ),
            )

            return SupplierListResponse(
                suppliers=[self._to_response(s) for s in suppliers],
                total=len(suppliers),
                skip=skip,
                limit=limit,
                has_more=len(suppliers) == limit,
            )

        except Exception as e:
            self._logger.error(
                f"Service error getting all suppliers: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="get_all_suppliers_error",
                    location="SupplierService.get_all_suppliers",
                ),
            )
            return SupplierListResponse(
                suppliers=[], total=0, skip=skip, limit=limit, has_more=False
            )

    async def update_supplier(
        self,
        session: AsyncSession,
        supplier_id: uuid.UUID,
        update_data: SupplierUpdate,
        user_id: Optional[str] = None,
    ) -> Optional[SupplierResponse]:
        """
        Update a supplier with business validation.

        Args:
            session: Database session
            supplier_id: Supplier UUID
            update_data: Validated update data from Pydantic schema
            user_id: Optional user ID for audit logging

        Returns:
            SupplierResponse or None if update fails
        """
        try:
            # Get current supplier for comparison
            current_supplier = await self.repo.get_by_id(session, supplier_id)
            if not current_supplier:
                self._logger.warning(
                    f"Supplier not found for update: {supplier_id}",
                    extra=create_owasp_log_context(
                        user=user_id or "system",
                        action="update_supplier_not_found",
                        location="SupplierService.update_supplier",
                    ),
                )
                return None

            # Convert Pydantic model to dict, excluding unset fields
            update_dict = update_data.model_dump(exclude_unset=True)

            # Business logic: Log email changes
            if (
                "email" in update_dict
                and update_dict["email"] != current_supplier.email
            ):
                self._logger.info(
                    f"Email change for supplier {supplier_id}: {current_supplier.email} -> {update_dict['email']}",
                    extra=create_owasp_log_context(
                        user=user_id or "system",
                        action="supplier_email_change",
                        location="SupplierService.update_supplier",
                    ),
                )

            # Update via repository
            updated_supplier = await self.repo.update(session, supplier_id, update_dict)

            if updated_supplier:
                self._logger.info(
                    f"Supplier updated successfully: {supplier_id}",
                    extra=create_owasp_log_context(
                        user=user_id or "system",
                        action="update_supplier_success",
                        location="SupplierService.update_supplier",
                    ),
                )

                return self._to_response(updated_supplier)

            return None

        except ValueError as e:
            self._logger.error(
                f"Validation error updating supplier: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="update_supplier_validation_error",
                    location="SupplierService.update_supplier",
                ),
            )
            raise

        except Exception as e:
            self._logger.error(
                f"Service error updating supplier: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="update_supplier_error",
                    location="SupplierService.update_supplier",
                ),
            )
            raise

    async def delete_supplier(
        self,
        session: AsyncSession,
        supplier_id: uuid.UUID,
        soft: bool = True,
        user_id: Optional[str] = None,
    ) -> bool:
        """
        Delete a supplier (soft or hard delete).

        Args:
            session: Database session
            supplier_id: Supplier UUID
            soft: If True, perform soft delete; otherwise hard delete
            user_id: Optional user ID for audit logging

        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            delete_type = "soft" if soft else "hard"

            self._logger.info(
                f"Attempting {delete_type} delete of supplier: {supplier_id}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action=f"{delete_type}_delete_supplier",
                    location="SupplierService.delete_supplier",
                ),
            )

            if soft:
                success = await self.repo.soft_delete(session, supplier_id)
            else:
                success = await self.repo.delete(session, supplier_id)

            if success:
                self._logger.info(
                    f"Supplier {delete_type} deleted successfully: {supplier_id}",
                    extra=create_owasp_log_context(
                        user=user_id or "system",
                        action=f"{delete_type}_delete_supplier_success",
                        location="SupplierService.delete_supplier",
                    ),
                )
            else:
                self._logger.warning(
                    f"Supplier not found for {delete_type} deletion: {supplier_id}",
                    extra=create_owasp_log_context(
                        user=user_id or "system",
                        action=f"{delete_type}_delete_supplier_not_found",
                        location="SupplierService.delete_supplier",
                    ),
                )

            return success

        except Exception as e:
            self._logger.error(
                f"Service error deleting supplier: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="delete_supplier_error",
                    location="SupplierService.delete_supplier",
                ),
            )
            return False

    async def filter_suppliers(
        self,
        session: AsyncSession,
        filter_params: SupplierFilterParams,
        user_id: Optional[str] = None,
    ) -> SupplierListResponse:
        """
        Filter suppliers based on various criteria.

        Args:
            session: Database session
            filter_params: Validated filter parameters
            user_id: Optional user ID for audit logging

        Returns:
            SupplierListResponse with filtered suppliers and metadata
        """
        try:
            # Convert Pydantic model to dict for repository
            filters = filter_params.model_dump(
                exclude={"skip", "limit"}, exclude_unset=True
            )

            suppliers = await self.repo.filter_suppliers(
                session, filters, filter_params.skip, filter_params.limit
            )

            self._logger.info(
                f"Filtered suppliers: {len(suppliers)} results",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="filter_suppliers",
                    location="SupplierService.filter_suppliers",
                ),
            )

            return SupplierListResponse(
                suppliers=[self._to_response(s) for s in suppliers],
                total=len(suppliers),
                skip=filter_params.skip,
                limit=filter_params.limit,
                has_more=len(suppliers) == filter_params.limit,
            )

        except Exception as e:
            self._logger.error(
                f"Service error filtering suppliers: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="filter_suppliers_error",
                    location="SupplierService.filter_suppliers",
                ),
            )
            return SupplierListResponse(
                suppliers=[],
                total=0,
                skip=filter_params.skip,
                limit=filter_params.limit,
                has_more=False,
            )

    async def search_suppliers(
        self,
        session: AsyncSession,
        search_term: str,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[str] = None,
    ) -> SupplierListResponse:
        """
        Search suppliers by name, email, or contact person.

        Args:
            session: Database session
            search_term: Search term
            skip: Number of records to skip
            limit: Maximum records to return
            user_id: Optional user ID for audit logging

        Returns:
            SupplierListResponse with search results
        """
        try:
            suppliers = await self.repo.search_suppliers(
                session, search_term, skip, limit
            )

            self._logger.info(
                f"Search results for '{search_term}': {len(suppliers)} suppliers found",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="search_suppliers",
                    location="SupplierService.search_suppliers",
                ),
            )

            return SupplierListResponse(
                suppliers=[self._to_response(s) for s in suppliers],
                total=len(suppliers),
                skip=skip,
                limit=limit,
                has_more=len(suppliers) == limit,
            )

        except Exception as e:
            self._logger.error(
                f"Service error searching suppliers: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="search_suppliers_error",
                    location="SupplierService.search_suppliers",
                ),
            )
            return SupplierListResponse(
                suppliers=[], total=0, skip=skip, limit=limit, has_more=False
            )

    async def link_product_to_supplier(
        self,
        session: AsyncSession,
        supplier_id: uuid.UUID,
        link_data: SupplierProductLink,
        user_id: Optional[str] = None,
    ) -> bool:
        """
        Link a product to a supplier.

        Args:
            session: Database session
            supplier_id: Supplier UUID
            link_data: Product link data with product_id and optional supply_price
            user_id: Optional user ID for audit logging

        Returns:
            True if link was successful, False otherwise
        """
        try:
            product_id = uuid.UUID(link_data.product_id)

            success = await self.repo.link_product(
                session, supplier_id, product_id, link_data.supply_price
            )

            if success:
                self._logger.info(
                    f"Product {product_id} linked to supplier {supplier_id}",
                    extra=create_owasp_log_context(
                        user=user_id or "system",
                        action="link_product_success",
                        location="SupplierService.link_product_to_supplier",
                    ),
                )

                # Update last purchase date
                await self.repo.update_last_purchase_date(
                    session, supplier_id, datetime.utcnow()
                )

            return success

        except Exception as e:
            self._logger.error(
                f"Service error linking product to supplier: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="link_product_error",
                    location="SupplierService.link_product_to_supplier",
                ),
            )
            return False

    async def unlink_product_from_supplier(
        self,
        session: AsyncSession,
        supplier_id: uuid.UUID,
        product_id: str,
        user_id: Optional[str] = None,
    ) -> bool:
        """
        Unlink a product from a supplier.

        Args:
            session: Database session
            supplier_id: Supplier UUID
            product_id: Product UUID as string
            user_id: Optional user ID for audit logging

        Returns:
            True if unlink was successful, False otherwise
        """
        try:
            product_uuid = uuid.UUID(product_id)

            success = await self.repo.unlink_product(session, supplier_id, product_uuid)

            if success:
                self._logger.info(
                    f"Product {product_id} unlinked from supplier {supplier_id}",
                    extra=create_owasp_log_context(
                        user=user_id or "system",
                        action="unlink_product_success",
                        location="SupplierService.unlink_product_from_supplier",
                    ),
                )

            return success

        except Exception as e:
            self._logger.error(
                f"Service error unlinking product from supplier: {str(e)}",
                extra=create_owasp_log_context(
                    user=user_id or "system",
                    action="unlink_product_error",
                    location="SupplierService.unlink_product_from_supplier",
                ),
            )
            return False

    def _to_response(self, supplier) -> SupplierResponse:
        """
        Convert Supplier model to SupplierResponse schema.

        Args:
            supplier: Supplier model instance

        Returns:
            SupplierResponse schema
        """
        return SupplierResponse(
            id=str(supplier.id),
            name=supplier.name,
            contact_person=supplier.contact_person,
            contact_number=supplier.contact_number,
            email=supplier.email,
            address=supplier.address,
            created_at=supplier.created_at,
            last_purchase_date=supplier.last_purchase_date,
            is_active=supplier.is_active,
        )
