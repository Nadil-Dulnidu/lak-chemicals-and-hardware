from __future__ import annotations

import os
from typing import Any, Dict

from langfuse import Langfuse
from app.configs.config_loader import get_config_value


def _configure_langfuse_from_config() -> None:
    public_key = get_config_value("langfuse", "public_key", default=None)
    secret_key = get_config_value("langfuse", "secret_key", default=None)
    base_url = get_config_value("langfuse", "base_url", default=None)
    host = get_config_value("langfuse", "host", default=None)

    if public_key:
        os.environ.setdefault("LANGFUSE_PUBLIC_KEY", public_key)
    if secret_key:
        os.environ.setdefault("LANGFUSE_SECRET_KEY", secret_key)
    if base_url:
        os.environ.setdefault("LANGFUSE_BASE_URL", base_url)
    if host:
        os.environ.setdefault("LANGFUSE_HOST", host)
        os.environ.setdefault("LANGFUSE_BASE_URL", host)


_configure_langfuse_from_config()
langfuse = Langfuse()


def _coerce_dict(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        try:
            return value.model_dump()
        except Exception:
            return {}
    if hasattr(value, "dict"):
        try:
            return value.dict()
        except Exception:
            return {}
    return {}


def sanitize_state(state: Any) -> Dict[str, Any]:
    if state is None:
        return {}

    if not isinstance(state, dict):
        try:
            state = dict(state)
        except Exception:
            return {}

    safe_state: Dict[str, Any] = {}

    def _copy_if_present(key: str) -> None:
        if key in state and state[key] is not None:
            safe_state[key] = state[key]

    for key in [
        "is_admin",
        "clarification_validation_completed",
        "user_confirmation_completed",
        "should_execute_add_to_cart",
        "analytics_inquiry_validation_completed",
        "user_id",
        "thread_id",
    ]:
        _copy_if_present(key)

    analytics_router_response = _coerce_dict(state.get("analytics_router_response"))
    if analytics_router_response.get("query_type") is not None:
        safe_state["analytics_query_type"] = analytics_router_response.get("query_type")

    product_suggestion_response = _coerce_dict(state.get("product_suggestion_response"))
    if product_suggestion_response.get("availability_status") is not None:
        safe_state["product_availability_status"] = product_suggestion_response.get(
            "availability_status"
        )

    return safe_state
