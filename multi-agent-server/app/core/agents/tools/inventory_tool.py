from app.configs.logging import get_logger
import requests
from datetime import datetime
from pydantic import ValidationError
from requests.exceptions import ConnectionError, Timeout, RequestException
from typing import Optional
from langchain_core.tools import tool

from app.core.agents.tools.schemas.inventory_tool_model import (
    InventoryToolParams,
    InventoryToolResponse,
)


logger = get_logger(__name__)


def get_config_value(*keys, default=None):
    from app.configs.config_loader import get_config_value as _get_config_value

    return _get_config_value(*keys, default=default)


@tool(
    args_schema=InventoryToolParams,
    description="Fetch the inventory report from the business server API.",
)
def get_inventory_report(
    category: Optional[str] = None,
    low_stock_only: bool = False,
) -> dict:
    """
    Fetch the inventory report from the business server API.

    This tool is designed for use by AI agents.  It validates all input
    parameters using Pydantic before making the request, and sends the
    required API key via the configured HTTP header.

    Args:
        category:  (optional) Product category name to filter results.
        low_stock_only:  (optional) Whether to return only low stock items.

    Returns:
        A dictionary representation of ``InventoryToolResponse`` on success, or a
        dict with an ``"error"`` key describing the failure.
    """
    try:
        params = InventoryToolParams(
            category=category,
            low_stock_only=low_stock_only,
        )
    except ValidationError as exc:
        errors = exc.errors()
        logger.warning("Inventory tool parameter validation failed: %s", errors)
        return {
            "error": "Invalid parameters provided to get_inventory_report.",
            "validation_errors": [
                {"field": ".".join(str(loc) for loc in e["loc"]), "message": e["msg"]}
                for e in errors
            ],
        }

    base_url: str = get_config_value("business_server", "base_url")
    api_key: str = get_config_value("business_server", "api_key")
    api_key_name: str = get_config_value(
        "business_server", "api_key_name", default="x-api-key"
    )

    if not base_url:
        logger.error("business_server.base_url is not configured.")
        return {"error": "Server configuration error: base_url is missing."}

    if not api_key:
        logger.error("business_server.api_key is not configured.")
        return {"error": "Server configuration error: api_key is missing."}

    url = f"{base_url.rstrip('/')}/api/v1/tools/inventory"

    headers = {
        api_key_name: api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    query_params: dict = {}

    if params.category is not None:
        query_params["category"] = params.category

    if params.low_stock_only is not None:
        query_params["low_stock_only"] = params.low_stock_only

    logger.info(
        "Fetching inventory report | url=%s | category=%s | low_stock_only=%s",
        url,
        params.category,
        params.low_stock_only,
    )

    try:
        response = requests.post(url, headers=headers, json=query_params, timeout=30)
    except ConnectionError:
        logger.exception("Could not connect to business server at %s", base_url)
        return {"error": f"Could not connect to the business server at {base_url}."}
    except Timeout:
        logger.exception("Request to business server timed out.")
        return {"error": "The request to the business server timed out."}
    except RequestException as exc:
        logger.exception("Unexpected request error: %s", exc)
        return {"error": f"An unexpected network error occurred: {exc}"}

    if response.status_code == 401:
        logger.error("Authentication failed – check business_server.api_key in config.")
        return {"error": "Authentication failed. The provided API key was rejected."}

    if response.status_code == 403:
        logger.error(
            "Access forbidden – the API key may lack the required permissions."
        )
        return {
            "error": "Access forbidden. The API key does not have the required permissions."
        }

    if response.status_code == 404:
        logger.error("Inventory analytics endpoint not found at %s", url)
        return {"error": f"Inventory analytics endpoint not found ({url})."}

    if not response.ok:
        logger.error(
            "Business server returned HTTP %s: %s", response.status_code, response.text
        )
        return {
            "error": f"Business server returned an error (HTTP {response.status_code}).",
            "details": response.text,
        }

    try:
        raw_data = response.json()
    except ValueError:
        logger.error("Business server response is not valid JSON: %s", response.text)
        return {"error": "Business server returned an invalid (non-JSON) response."}

    try:
        inventory_response = InventoryToolResponse(**raw_data)
    except (ValidationError, TypeError) as exc:
        logger.error("Response schema validation failed: %s", exc)
        return {
            "error": "Business server response did not match the expected schema.",
            "details": str(exc),
        }

    logger.info(
        "Inventory report fetched successfully | category=%s | low_stock_only=%s",
        params.category,
        params.low_stock_only,
    )

    return inventory_response.dict()
