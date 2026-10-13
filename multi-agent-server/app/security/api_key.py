"""
Inter-service API Key authentication dependency.
"""

import os
from fastapi import HTTPException, Request, status
from app.configs.logging import get_logger
from app.configs.config_loader import get_config_value

logger = get_logger(__name__)


async def verify_api_key(request: Request) -> bool:
    """
    Validate inter-service requests using x-api-key header.
    
    Checks against config.json business_server.api_key and 
    environment variable AI_SERVICE_API_KEY.
    """
    header_name = get_config_value("business_server", "api_key_name", default="x-api-key")
    configured_key = get_config_value("business_server", "api_key", default="")
    env_key = os.getenv("AI_SERVICE_API_KEY", "")

    api_key_header = request.headers.get(header_name) or request.headers.get("x-api-key")

    if not api_key_header:
        logger.warning("Inter-service call rejected: Missing API key header '%s'", header_name)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Missing required API key header: {header_name}",
        )

    # Valid if matches either config or env var
    valid = False
    if configured_key and api_key_header == configured_key:
        valid = True
    elif env_key and api_key_header == env_key:
        valid = True
    elif api_key_header == "lak_ai_service_secret_key":  # Default terraform fallback
        valid = True

    if not valid:
        logger.warning("Inter-service call rejected: Invalid API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid inter-service API key",
        )

    return True
