from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query,
    UploadFile,
    File,
    Form,
)
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import uuid
import json

from app.utils.db import get_async_session
from app.services.product_service import ProductService
from app.schemas.product_schema import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
    ProductFilterParams,
    LowStockAlert,
    ProductCategoryEnum,
)
from app.utils.image_upload import upload_image

router = APIRouter(prefix="/products", tags=["Products"])

# Initialize service
product_service = ProductService()


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product",
    description="Create a new product with optional image upload",
)
async def create_product(
    name: str = Form(...),
    price: float = Form(...),
    stock_qty: int = Form(...),
    category: Optional[str] = Form(None),
    brand: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    reorder_level: Optional[int] = Form(10),
    image: Optional[UploadFile] = File(None),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Create a new product with optional image upload.

    - **name**: Product name (required)
    - **price**: Product price (required, must be positive)
    - **stock_qty**: Stock quantity (required, must be non-negative)
    - **category**: Product category (optional)
    - **brand**: Product brand (optional)
    - **description**: Product description (optional)
    - **reorder_level**: Reorder level for low stock alerts (optional, default: 10)
    - **image**: Product image file (optional)
    """
    try:
        # Upload image if provided
        image_url = None
        if image and image.filename:
            image_url = await upload_image(image)
            if not image_url:
                # Log warning but continue without image
                pass

        # Create product data
        product_data = ProductCreate(
            name=name,
            price=price,
            stock_qty=stock_qty,
            category=ProductCategoryEnum(category) if category else None,
            brand=brand,
            description=description,
            reorder_level=reorder_level or 10,
            image_url=image_url,
        )

        product = await product_service.create_product(
            session, product_data, user_id="admin"
        )

        if not product:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create product",
            )

        return product

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get product by ID",
    description="Retrieve a single product by its UUID",
)
async def get_product(
    product_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get a product by its ID.

    - **product_id**: UUID of the product
    """
    product = await product_service.get_product(session, product_id, user_id="admin")

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found",
        )

    return product


@router.get(
    "/",
    response_model=ProductListResponse,
    summary="Get all products",
    description="Retrieve all products with pagination",
)
async def get_all_products(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    include_inactive: bool = Query(False, description="Include inactive products"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get all products with pagination.

    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum records to return (default: 100, max: 500)
    - **include_inactive**: Include inactive products (default: false)
    """
    return await product_service.get_all_products(
        session, skip, limit, include_inactive, user_id="admin"
    )


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update product",
    description="Update an existing product",
)
async def update_product(
    product_id: uuid.UUID,
    update_data: ProductUpdate,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Update a product.

    - **product_id**: UUID of the product to update
    - All fields are optional; only provided fields will be updated
    """
    try:
        product = await product_service.update_product(
            session, product_id, update_data, user_id="admin"
        )

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found",
            )

        return product

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete product",
    description="Delete a product (soft delete by default)",
)
async def delete_product(
    product_id: uuid.UUID,
    hard: bool = Query(False, description="Perform hard delete instead of soft delete"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Delete a product.

    - **product_id**: UUID of the product to delete
    - **hard**: If true, permanently delete; otherwise soft delete (default: false)
    """
    success = await product_service.delete_product(
        session, product_id, soft=not hard, user_id="admin"
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found",
        )

    return None


@router.get(
    "/search/query",
    response_model=ProductListResponse,
    summary="Search products",
    description="Search products by name or description",
)
async def search_products(
    q: str = Query(..., min_length=1, description="Search term"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Search products by name or description.

    - **q**: Search term (required)
    - **skip**: Pagination offset
    - **limit**: Maximum records to return
    """
    return await product_service.search_products(
        session, q, skip, limit, user_id="admin"
    )


@router.get(
    "/category/{category}",
    response_model=ProductListResponse,
    summary="Get products by category",
    description="Retrieve all products in a specific category",
)
async def get_products_by_category(
    category: ProductCategoryEnum,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get all products in a specific category.

    - **category**: Product category
    - **skip**: Pagination offset
    - **limit**: Maximum records to return
    """
    return await product_service.get_products_by_category(
        session, category.value, skip, limit, user_id="admin"
    )


@router.get(
    "/alerts/low-stock",
    response_model=list[LowStockAlert],
    summary="Get low stock alerts",
    description="Get products with low stock that need restocking",
)
async def get_low_stock_alerts(
    threshold: int = Query(10, ge=1, description="Stock quantity threshold"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get products with low stock.

    - **threshold**: Stock quantity threshold (default: 10)
    - **limit**: Maximum records to return

    Returns products with stock below threshold, including:
    - Priority level (critical/high/medium/low)
    - Quantity needed to reach threshold
    """
    return await product_service.get_low_stock_alerts(
        session, threshold, limit, user_id="admin"
    )
