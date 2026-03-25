from jose import jwt
from jose.exceptions import JWTError
from fastapi import Depends, HTTPException, Request, status
import httpx
from app.config.logging import get_logger


def get_config_value(*keys, default=None):
    from app.config.config_loader import get_config_value as _get_config_value

    return _get_config_value(*keys, default=default)


logger = get_logger(__name__)

JWKS_URL = get_config_value("clerk", "jwks_url")
CLERK_ISSUER = get_config_value("clerk", "issuer")

_jwks_cache = None


async def get_jwks():
    global _jwks_cache
    if not _jwks_cache:
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(JWKS_URL)
                _jwks_cache = res.json()
                logger.info(
                    "JWKS fetched successfully", extra={"action": "jwks_fetch_success"}
                )
        except Exception as e:
            logger.error(
                f"Failed to fetch JWKS: {str(e)}",
                extra={"action": "jwks_fetch_error"},
                exc_info=True,
            )
            raise
    return _jwks_cache


async def verify_clerk_token(request: Request):
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        logger.warning(
            "Authentication failed: Missing or invalid authorization header",
            extra={"action": "auth_missing_token"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing token",
        )

    token = auth_header.replace("Bearer ", "")

    jwks = await get_jwks()

    try:
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            issuer=CLERK_ISSUER,
            options={"verify_aud": False},
        )

        user_id = payload.get("sub", "unknown")
        logger.info(
            "Token verified successfully",
            extra={"user": user_id, "action": "auth_success"},
        )

        return payload
    except JWTError as e:
        logger.warning(
            f"Token verification failed: {str(e)}",
            extra={"action": "auth_token_invalid"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )


def role_from_claims(payload: dict) -> str | None:
    """
    Resolve app role from Clerk JWT claims.

    Supports a top-level `role` claim (custom session template) and
    `public_metadata.role` (Clerk public metadata on the user).
    """
    r = payload.get("role")
    if r is not None and r != "":
        return str(r)
    pm = payload.get("public_metadata")
    if isinstance(pm, dict):
        r = pm.get("role")
        if r is not None and r != "":
            return str(r)
    return None


async def require_admin(user_data: dict = Depends(verify_clerk_token)) -> dict:
    if role_from_claims(user_data) != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user_data
