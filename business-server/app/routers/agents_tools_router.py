from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.utils.db import get_async_session
from app.services.report_service import ReportService
from app.services.product_service import ProductService
from app.services.cart_service import CartService
from app.schemas.report_schema import (
    SalesReportParams,
    InventoryReportParams,
    ProductPerformanceParams,
    SalesReportData,
    InventoryReportData,
    ProductPerformanceData,
)
from app.schemas.product_schema import ProductListResponse
from app.schemas.cart_schema import CartItemsAgentCreate, CartResponse

router = APIRouter(prefix="/tools", tags=["Agent Tools"])

report_service = ReportService()
product_service = ProductService()
cart_service = CartService()


@router.post(
    "/sales",
    response_model=SalesReportData,
    summary="Generate sales report",
    description="Generate a sales report with revenue and quantity analysis",
)
async def generate_sales_report(
    params: SalesReportParams,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Generate a sales report based on parameters.

    - **start_date**: Report start date (required)
    - **end_date**: Report end date (required)
    - **product_id**: Filter by specific product (optional)
    - **category**: Filter by product category (optional)
    - **group_by**: Group results by day/week/month (default: day)

    Returns:
    - Overall summary (total sales, revenue, quantity)
    - Time-based breakdown
    - Product-wise breakdown
    - Category-wise breakdown

    Data source: `sales`, `orders`, `order_items` tables
    """
    try:
        return await report_service.generate_sales_report(session, params)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating sales report: {str(e)}",
        )


@router.post(
    "/inventory",
    response_model=InventoryReportData,
    summary="Generate inventory report",
    description="Generate an inventory report with stock levels and value analysis",
)
async def generate_inventory_report(
    params: InventoryReportParams,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Generate an inventory report based on parameters.

    - **category**: Filter by product category (optional)
    - **low_stock**: Filter by low stock (optional)

    Returns:
    - Overall summary (total stock, value)
    - Product-wise breakdown

    Data source: `inventory`, `products` tables
    """
    try:
        return await report_service.generate_inventory_report(session, params)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating inventory report: {str(e)}",
        )


@router.post(
    "/product-performance",
    response_model=ProductPerformanceData,
    summary="Generate product performance report",
    description="Generate a product performance report with sales and revenue analysis",
)
async def generate_product_performance_report(
    params: ProductPerformanceParams,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Generate a product performance report based on parameters.

    - **start_date**: Report start date (required)
    - **end_date**: Report end date (required)
    - **category**: Filter by product category (optional)
    - **top_n**: Top N products to show (default: 10)

    Returns:
    - Overall summary (total sales, revenue, quantity)
    - Product-wise breakdown

    Data source: `sales`, `orders`, `order_items` tables
    """
    try:
        return await report_service.generate_product_performance_report(session, params)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating product performance report: {str(e)}",
        )


@router.get(
    "/products",
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


@router.post(
    "/add-to-cart",
    response_model=CartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add item to cart",
    description="Add a product to the user's shopping cart",
)
async def add_items_to_cart(
    item_data: CartItemsAgentCreate,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Add an item to the cart.

    - **product_id**: Product UUID (required)
    - **quantity**: Quantity to add (required, must be positive)

    If the product already exists in the cart, the quantity will be added to the existing quantity.
    """
    try:
        cart = None
        for item in item_data.items:
            cart = await cart_service.add_item_to_cart(session, item_data.user_id, item)

        if not cart:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add item to cart",
            )
        return cart

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
