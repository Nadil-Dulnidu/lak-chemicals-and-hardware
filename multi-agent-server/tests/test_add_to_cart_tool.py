import pytest
from app.core.agents.tools import add_to_cart_tool
from app.core.agents.tools.schemas.add_to_cart_model import AddToCartResponse


@pytest.mark.integration
def test_add_to_cart_tool():
    result = add_to_cart_tool.invoke(
        {
            "items": [
                {"product_id": "9e5e65dc-563d-4c80-a7a4-c01e2beb02df", "quantity": 1},
                {"product_id": "15b11d65-835d-4d2c-89c8-4ef24e350def", "quantity": 1},
            ],
            "user_id": "5694057d-2973-420e-808f-5703a4476577",
        }
    )
    assert "error" not in result, f"Tool returned an error: {result.get('error')}"
    assert "cart_id" in result, f"Tool returned an error: {result.get('cart_id')}"
    assert "user_id" in result, f"Tool returned an error: {result.get('user_id')}"
    assert "items" in result, f"Tool returned an error: {result.get('items')}"
    assert (
        "total_items" in result
    ), f"Tool returned an error: {result.get('total_items')}"
    assert (
        "total_amount" in result
    ), f"Tool returned an error: {result.get('total_amount')}"
