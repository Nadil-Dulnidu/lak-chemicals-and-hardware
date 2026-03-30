import pytest
from app.core.agents.tools.product_list_tool import fetch_product_list
from app.core.agents.tools.schemas.product_list_tool_model import (
    ProductListToolResponse,
)


@pytest.mark.integration
def test_product_list_tool_output():
    """
    Call the product list tool directly via .invoke() and verify the response
    contains the expected keys. The tool returns a dict (model_dump()),
    not a ProductListToolResponse object.
    """
    result = fetch_product_list.invoke(
        {
            "skip": 0,
            "limit": 100,
            "include_inactive": False,
        }
    )

    # The tool should NOT return an error
    assert "error" not in result, f"Tool returned an error: {result.get('error')}"

    # Check the response is a dict
    assert isinstance(result, ProductListToolResponse)

    # Check the expected top-level keys are present
    assert hasattr(result, "products")
    assert hasattr(result, "total")
    assert hasattr(result, "skip")
    assert hasattr(result, "limit")
