from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import uuid

from app.utils.db import get_async_session
from app.services.supplier_service import SupplierService
from app.schemas.supplier_schema import (
    SupplierCreate,
    SupplierUpdate,
    SupplierResponse,
    SupplierListResponse,
    SupplierFilterParams,
    SupplierProductLink,
    SupplierProductUnlink,
    SupplierDetailResponse,
)

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])

# Initialize service
supplier_service = SupplierService()


@router.post(
    "/",
    response_model=SupplierResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new supplier",
    description="Create a new supplier with the provided information",
)
async def create_supplier(
    supplier_data: SupplierCreate,
    session: AsyncSession = Depends(get_async_session),
    # user_id: str = Depends(get_current_user)  # Add authentication later
):
    """
    Create a new supplier.

    - **name**: Supplier name (required)
    - **contact_number**: Contact phone number (required)
    - **email**: Supplier email address (required, must be unique)
    - **contact_person**: Contact person name (optional)
    - **address**: Supplier address (optional)
    """
    try:
        supplier = await supplier_service.create_supplier(
            session, supplier_data, user_id="admin"  # Replace with actual user_id
        )

        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create supplier",
            )

        return supplier

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{supplier_id}",
    response_model=SupplierResponse,
    summary="Get supplier by ID",
    description="Retrieve a single supplier by its UUID",
)
async def get_supplier(
    supplier_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get a supplier by its ID.

    - **supplier_id**: UUID of the supplier
    """
    supplier = await supplier_service.get_supplier(
        session, supplier_id, user_id="admin"
    )

    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with ID {supplier_id} not found",
        )

    return supplier


@router.get(
    "/{supplier_id}/detail",
    response_model=SupplierDetailResponse,
    summary="Get supplier with product details",
    description="Retrieve a supplier with all associated products",
)
async def get_supplier_detail(
    supplier_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get a supplier with detailed product information.

    - **supplier_id**: UUID of the supplier

    Returns supplier information along with all products they supply,
    including supply prices and last supplied dates.
    """
    supplier = await supplier_service.get_supplier_detail(
        session, supplier_id, user_id="admin"
    )

    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with ID {supplier_id} not found",
        )

    return supplier


@router.get(
    "/",
    response_model=SupplierListResponse,
    summary="Get all suppliers",
    description="Retrieve all suppliers with pagination",
)
async def get_all_suppliers(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    include_inactive: bool = Query(False, description="Include inactive suppliers"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get all suppliers with pagination.

    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum records to return (default: 100, max: 500)
    - **include_inactive**: Include inactive suppliers (default: false)
    """
    return await supplier_service.get_all_suppliers(
        session, skip, limit, include_inactive, user_id="admin"
    )


@router.put(
    "/{supplier_id}",
    response_model=SupplierResponse,
    summary="Update supplier",
    description="Update an existing supplier",
)
async def update_supplier(
    supplier_id: uuid.UUID,
    update_data: SupplierUpdate,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Update a supplier.

    - **supplier_id**: UUID of the supplier to update
    - All fields are optional; only provided fields will be updated
    """
    try:
        supplier = await supplier_service.update_supplier(
            session, supplier_id, update_data, user_id="admin"
        )

        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Supplier with ID {supplier_id} not found",
            )

        return supplier

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{supplier_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete supplier",
    description="Delete a supplier (soft delete by default)",
)
async def delete_supplier(
    supplier_id: uuid.UUID,
    hard: bool = Query(False, description="Perform hard delete instead of soft delete"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Delete a supplier.

    - **supplier_id**: UUID of the supplier to delete
    - **hard**: If true, permanently delete; otherwise soft delete (default: false)
    """
    try:
        success = await supplier_service.delete_supplier(
            session, supplier_id, soft=not hard, user_id="admin"
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Supplier with ID {supplier_id} not found",
            )

        return None

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/filter",
    response_model=SupplierListResponse,
    summary="Filter suppliers",
    description="Filter suppliers based on various criteria",
)
async def filter_suppliers(
    filter_params: SupplierFilterParams,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Filter suppliers based on criteria.

    - **is_active**: Filter by active status
    - **search**: Search in name, email, contact person
    - **skip**: Pagination offset
    - **limit**: Maximum records to return
    """
    return await supplier_service.filter_suppliers(
        session, filter_params, user_id="admin"
    )


@router.get(
    "/search/query",
    response_model=SupplierListResponse,
    summary="Search suppliers",
    description="Search suppliers by name, email, or contact person",
)
async def search_suppliers(
    q: str = Query(..., min_length=1, description="Search term"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Search suppliers by name, email, or contact person.

    - **q**: Search term (required)
    - **skip**: Pagination offset
    - **limit**: Maximum records to return
    """
    return await supplier_service.search_suppliers(
        session, q, skip, limit, user_id="admin"
    )


@router.post(
    "/{supplier_id}/products",
    status_code=status.HTTP_201_CREATED,
    summary="Link product to supplier",
    description="Create a relationship between a supplier and a product",
)
async def link_product_to_supplier(
    supplier_id: uuid.UUID,
    link_data: SupplierProductLink,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Link a product to a supplier.

    - **supplier_id**: UUID of the supplier
    - **product_id**: UUID of the product to link
    - **supply_price**: Optional price at which supplier provides this product

    This creates a many-to-many relationship allowing one supplier to supply
    multiple products and one product to come from multiple suppliers.
    """
    success = await supplier_service.link_product_to_supplier(
        session, supplier_id, link_data, user_id="admin"
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to link product to supplier. Check if supplier and product exist, and if link already exists.",
        )

    return {"message": "Product linked to supplier successfully"}


@router.delete(
    "/{supplier_id}/products/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unlink product from supplier",
    description="Remove the relationship between a supplier and a product",
)
async def unlink_product_from_supplier(
    supplier_id: uuid.UUID,
    product_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Unlink a product from a supplier.

    - **supplier_id**: UUID of the supplier
    - **product_id**: UUID of the product to unlink

    This removes the many-to-many relationship between the supplier and product.
    """
    success = await supplier_service.unlink_product_from_supplier(
        session, supplier_id, product_id, user_id="admin"
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found between supplier and product",
        )

    return None
