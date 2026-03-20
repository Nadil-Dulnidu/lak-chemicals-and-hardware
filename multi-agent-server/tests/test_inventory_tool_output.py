import pytest
from app.core.agents.tools.inventory_tool import get_inventory_report
from app.core.agents.tools.schemas.inventory_tool_model import (
    InventoryToolParams,
    InventoryToolResponse,
)


@pytest.mark.integration
def test_inventory_tool_output():
    """
    Call the sales tool directly via .invoke() and verify the response
    contains the expected keys. The tool returns a dict (model_dump()),
    not a SalesToolResponse object.
    """
    result = get_inventory_report.invoke(
        {
            "category": "",
            "low_stock_only": False,
        }
    )

    # The tool should NOT return an error
    assert "error" not in result, f"Tool returned an error: {result.get('error')}"

    # Check the expected top-level keys are present
    assert "report_type" in result
    assert "generated_at" in result
    assert "summary" in result
    assert "items" in result
    assert "low_stock_items" in result
