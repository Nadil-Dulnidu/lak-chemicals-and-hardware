from fastapi import FastAPI, HTTPException, Request, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config.open_api_tags import openapi_tags
from app.routers.product_router import router as product_router
from app.routers.supplier_router import router as supplier_router
from app.routers.inventory_router import router as inventory_router
from app.routers.cart_router import router as cart_router
from app.routers.quotation_router import router as quotation_router
from app.routers.order_router import router as order_router
from app.routers.report_router import router as report_router
from app.routers.stripe_router import router as stripe_router
from contextlib import asynccontextmanager
from app.utils.db import create_db_and_tables
from app.security.jwt import verify_clerk_token


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan manager for the application.

    Args:
        app (FastAPI): The FastAPI application instance.
    """
    await create_db_and_tables()
    yield


app = FastAPI(
    title="Lak Chemicals and Hardware API",
    description="API for Lak Chemicals and Hardware",
    version="1.0.0",
    openapi_tags=openapi_tags,
    lifespan=lifespan,
    root_path="/api/v1",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Exception handler for unhandled exceptions.

    Args:
        request (Request): The incoming request.
        exc (Exception): The exception that occurred.

    Returns:
        JSONResponse: A JSON response with the error details.
    """

    if isinstance(exc, HTTPException):
        raise exc

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


@app.get("/", status_code=status.HTTP_200_OK, tags=["Main"])
async def root():
    """
    Endpoint for the root of the API.

    Returns:
        dict: A dictionary containing a message indicating that the system is healthy.
    """
    return {"message": "Welcome to Lak Chemicals and Hardware"}


@app.get("/health", status_code=status.HTTP_200_OK, tags=["Main"])
async def health():
    """
    Endpoint for checking the health of the system.

    Returns:
        dict: A dictionary containing a message indicating that the system is healthy.
    """
    return {"message": "Lak Chemicals and Hardware is healthy"}


# Include routers
app.include_router(product_router)
app.include_router(supplier_router, dependencies=[Depends(verify_clerk_token)])
app.include_router(inventory_router, dependencies=[Depends(verify_clerk_token)])
app.include_router(cart_router)
app.include_router(quotation_router, dependencies=[Depends(verify_clerk_token)])
app.include_router(order_router, dependencies=[Depends(verify_clerk_token)])
app.include_router(report_router, dependencies=[Depends(verify_clerk_token)])
app.include_router(stripe_router, dependencies=[Depends(verify_clerk_token)])
