from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config.open_api_tags import openapi_tags
from app.routers.product_router import router as product_router
from contextlib import asynccontextmanager
from app.utils.db import create_db_and_tables


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


app.include_router(product_router)
