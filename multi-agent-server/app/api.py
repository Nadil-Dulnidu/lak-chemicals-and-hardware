from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.configs.open_api_tags import openapi_tags
from app.routers.chat_router import chat_router
from app.configs.logging import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="Lak Chemicals and Hardware Multi Agent Server",
    description="A system to manage knowledge using multiple agents.",
    version="0.1.0",
    openapi_tags=openapi_tags,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
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

    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={"action": "unhandled_exception", "location": f"{request.url.path}"},
        exc_info=True,
    )
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
    return {"message": "Welcome to IKMS"}


@app.get("/health", status_code=status.HTTP_200_OK, tags=["Main"])
async def health():
    """
    Endpoint for checking the health of the system.

    Returns:
        dict: A dictionary containing a message indicating that the system is healthy.
    """
    return {"message": "IKMS is healthy"}


# Include chat router
app.include_router(chat_router)
