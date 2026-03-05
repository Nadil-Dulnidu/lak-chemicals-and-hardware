import logging
import requests
from datetime import datetime
from pydantic import ValidationError
from requests.exceptions import ConnectionError, Timeout, RequestException
from typing import Literal
from langchain_core.tools import tool

from app.core.agents.tools.schemas.sales_tool_model import (
    SalesToolParams,
    SalesToolResponse,
)


logger = logging.getLogger(__name__)


def get_config_value(*keys, default=None):
    from app.configs.config_loader import get_config_value as _get_config_value

    return _get_config_value(*keys, default=default)


@tool(
    args_schema=SalesToolParams,
    description="Fetch the sales report from the business server API.",
)
def get_sales_report(
    start_date: str,
    end_date: str,
    product_id: str | None = None,
    category: str | None = None,
    group_by: Literal["day", "week", "month"] = "day",
) -> dict:
    """
    Fetch the sales report from the business server API.

    This tool is designed for use by AI agents.  It validates all input
    parameters using Pydantic before making the request, and sends the
    required API key via the configured HTTP header.

    Args:
        start_date:  ISO-8601 datetime string for the start of the report period.
                     Example: "2024-01-01T00:00:00"
        end_date:    ISO-8601 datetime string for the end of the report period.
                     Example: "2024-01-31T23:59:59"
        product_id:  (optional) UUID string to filter results to a single product.
        category:    (optional) Product category name to filter results.
        group_by:    Time-grouping granularity – one of "day", "week", or "month".
                     Defaults to "day".

    Returns:
        A dictionary representation of ``SalesToolResponse`` on success, or a
        dict with an ``"error"`` key describing the failure.
    """

    try:
        params = SalesToolParams(
            start_date=start_date,
            end_date=end_date,
            product_id=product_id,
            category=category,
            group_by=group_by,
        )
    except ValidationError as exc:
        errors = exc.errors()
        logger.warning("Sales tool parameter validation failed: %s", errors)
        return {
            "error": "Invalid parameters provided to get_sales_report.",
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

    url = f"{base_url.rstrip('/')}/api/v1/tools/sales"

    headers = {
        api_key_name: api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    query_params: dict = {
        "start_date": params.start_date.isoformat(),
        "end_date": params.end_date.isoformat(),
        "group_by": params.group_by,
    }

    if params.product_id is not None:
        query_params["product_id"] = params.product_id

    if params.category is not None:
        query_params["category"] = params.category

    logger.info(
        "Fetching sales report | url=%s | start=%s | end=%s | group_by=%s",
        url,
        params.start_date.isoformat(),
        params.end_date.isoformat(),
        params.group_by,
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
        logger.error("Sales analytics endpoint not found at %s", url)
        return {"error": f"Sales analytics endpoint not found ({url})."}

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
        sales_response = SalesToolResponse(**raw_data)
    except (ValidationError, TypeError) as exc:
        logger.error("Response schema validation failed: %s", exc)
        return {
            "error": "Business server response did not match the expected schema.",
            "details": str(exc),
        }

    logger.info(
        "Sales report fetched successfully | period=%s to %s",
        sales_response.start_date,
        sales_response.end_date,
    )

    return sales_response.model_dump()


if __name__ == "__main__":

    response = get_sales_report(
        start_date="2026-03-01",
        end_date="2026-03-08",
        group_by="day",
    )
    print(response)
