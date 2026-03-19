from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader


def get_config_value(*keys, default=None):
    """Lazy import to avoid circular dependency"""
    from app.config.config_loader import get_config_value as _get_config_value

    return _get_config_value(*keys, default=default)


API_KEY = get_config_value("api_key", "key")
API_KEY_NAME = get_config_value("api_key", "name")

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key == API_KEY:
        return api_key
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Invalid or missing API Key",
    )
