import logging
import requests
from datetime import datetime
from pydantic import ValidationError
from requests.exceptions import ConnectionError, Timeout, RequestException
from typing import Optional
from langchain_core.tools import tool

from app.core.agents.tools.schemas.product_performance_tool_model import (
    ProductPerformanceToolParams,
    ProductPerformanceToolResponse,
)

logger = logging.getLogger(__name__)


def get_config_value(*keys, default=None):
    from app.configs.config_loader import get_config_value as _get_config_value

    return _get_config_value(*keys, default=default)


@tool(
    args_schema=ProductPerformanceToolParams,
    description="Fetch the product performance report from the business server API.",
)
def get_product_performance_report(
    start_date: datetime,
    end_date: datetime,
    category: Optional[str] = None,
    top_n: int = 10,
) -> dict:
    """
    Fetch the product performance report from the business server API.

    This tool is designed for use by AI agents.  It validates all input
    parameters using Pydantic before making the request, and sends the
    required API key via the configured HTTP header.

    Args:
        start_date:  (required) Start date for report.
        end_date:  (required) End date for report.
        category:  (optional) Product category name to filter results.
        top_n:  (optional) Number of top products to show.

    Returns:
        A dictionary representation of ``ProductPerformanceToolResponse`` on success, or a
        dict with an ``"error"`` key describing the failure.
    """
    try:
        params = ProductPerformanceToolParams(
            start_date=start_date,
            end_date=end_date,
            category=category,
            top_n=top_n,
        )
    except ValidationError as exc:
        errors = exc.errors()
        logger.warning(
            "Product performance tool parameter validation failed: %s", errors
        )
        return {
            "error": "Invalid parameters provided to get_product_performance_report.",
            "validation_errors": [
                {
                    "field": ".".join(str(loc) for loc in e["loc"]),
                    "message": e["msg"],
                }  # noqa: B905
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

    url = f"{base_url.rstrip('/')}/api/v1/tools/product-performance"

    headers = {
        api_key_name: api_key,
        "Content-Type": "application/json",
    }

    query_params: dict = {}

    query_params["start_date"] = params.start_date.isoformat()
    query_params["end_date"] = params.end_date.isoformat()

    if params.category is not None:
        query_params["category"] = params.category

    if params.top_n is not None:
        query_params["top_n"] = params.top_n

    logger.info(
        "Fetching product performance report | url=%s | start_date=%s | end_date=%s | category=%s | top_n=%s",
        url,
        params.start_date,
        params.end_date,
        params.category,
        params.top_n,
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
        logger.error("Product performance endpoint not found at %s", url)
        return {"error": f"Product performance endpoint not found ({url})."}

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
        product_performance_response = ProductPerformanceToolResponse(**raw_data)
    except (ValidationError, TypeError) as exc:
        logger.error("Response schema validation failed: %s", exc)
        return {
            "error": "Business server response did not match the expected schema.",
            "details": str(exc),
        }

    logger.info(
        "Product performance report fetched successfully | start_date=%s | end_date=%s | category=%s | top_n=%s",
        params.start_date,
        params.end_date,
        params.category,
        params.top_n,
    )

    return product_performance_response.dict()
