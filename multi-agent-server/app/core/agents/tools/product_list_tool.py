from app.configs.logging import get_logger
import requests
from datetime import datetime
from pydantic import ValidationError
from requests.exceptions import ConnectionError, Timeout, RequestException
from typing import Optional
from langchain_core.tools import tool

from app.core.agents.tools.schemas.product_list_tool_model import (
    ProductListToolResponse,
    ProductListToolParams,
)


logger = get_logger(__name__)


def get_config_value(*keys, default=None):
    from app.configs.config_loader import get_config_value as _get_config_value

    return _get_config_value(*keys, default=default)


@tool(
    args_schema=ProductListToolParams,
    description="Fetch the product list from the business server API.",
)
def fetch_product_list(
    skip: int = 0,
    limit: int = 100,
    include_inactive: bool = False,
) -> ProductListToolResponse:
    try:
        params = ProductListToolParams(
            skip=skip,
            limit=limit,
            include_inactive=include_inactive,
        )
    except ValidationError as exc:
        errors = exc.errors()
        logger.warning("Product list tool parameter validation failed: %s", errors)
        return {
            "error": "Invalid parameters provided to fetch_product_list.",
            "validation_errors": [
                {"field": "/".join(str(loc) for loc in e["loc"]), "message": e["msg"]}
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

    url = f"{base_url.rstrip('/')}/api/v1/tools/products"

    headers = {
        api_key_name: api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    query_params: dict = {}

    if params.skip is not None:
        query_params["skip"] = params.skip

    if params.limit is not None:
        query_params["limit"] = params.limit

    if params.include_inactive is not None:
        query_params["include_inactive"] = params.include_inactive

    logger.info(
        "Fetching product list | url=%s | skip=%s | limit=%s | include_inactive=%s",
        url,
        params.skip,
        params.limit,
        params.include_inactive,
    )

    try:
        response = requests.get(url, headers=headers, params=query_params, timeout=30)
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
        logger.error("Product list endpoint not found at %s", url)
        return {"error": f"Product list endpoint not found ({url})."}

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
        product_list_response = ProductListToolResponse(**raw_data)
    except (ValidationError, TypeError) as exc:
        logger.error("Response schema validation failed: %s", exc)
        return {
            "error": "Business server response did not match the expected schema.",
            "details": str(exc),
        }

    logger.info(
        "Product list fetched successfully | skip=%s | limit=%s | include_inactive=%s",
        params.skip,
        params.limit,
        params.include_inactive,
    )

    return product_list_response.dict()
