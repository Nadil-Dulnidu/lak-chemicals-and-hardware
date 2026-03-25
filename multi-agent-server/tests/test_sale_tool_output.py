import pytest
from app.core.agents.tools.sales_tool import get_sales_report
from app.core.agents.tools.schemas.sales_tool_model import (
    SalesToolParams,
    SalesToolResponse,
)


@pytest.mark.integration
def test_sales_tool_output():
    """
    Call the sales tool directly via .invoke() and verify the response
    contains the expected keys. The tool returns a dict (model_dump()),
    not a SalesToolResponse object.
    """
    result = get_sales_report.invoke(
        {
            "start_date": "2026-03-01",
            "end_date": "2026-03-18",
        }
    )

    # The tool should NOT return an error
    assert "error" not in result, f"Tool returned an error: {result.get('error')}"

    # Check the expected top-level keys are present
    assert "start_date" in result
    assert "end_date" in result
    assert "summary" in result
    assert "items" in result
    assert "product_breakdown" in result
    assert "category_breakdown" in result
