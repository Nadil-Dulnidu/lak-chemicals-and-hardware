import pytest
from app.core.agents.tools.product_performance_tool import (
    get_product_performance_report,
)
from app.core.agents.tools.schemas.product_performance_tool_model import (
    ProductPerformanceToolParams,
    ProductPerformanceToolResponse,
)


@pytest.mark.integration
def test_product_performance_tool_output():
    """
    Call the product performance tool directly via .invoke() and verify the response
    contains the expected keys. The tool returns a dict (model_dump()),
    not a ProductPerformanceToolResponse object.
    """
    result = get_product_performance_report.invoke(
        {
            "start_date": "2026-03-01",
            "end_date": "2026-03-18",
            "category": "",
            "top_n": 10,
        }
    )

    # The tool should NOT return an error
    assert "error" not in result, f"Tool returned an error: {result.get('error')}"

    # Check the expected top-level keys are present
    assert "report_type" in result
    assert "start_date" in result
    assert "end_date" in result
    assert "summary" in result
    assert "top_products" in result
    assert "category_performance" in result
