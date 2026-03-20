import pytest
from langchain_core.messages import HumanMessage
from app.core.agents.agents import get_product_performance_agent
from app.core.agents.schemas import ProductPerformanceAgentResponse


@pytest.mark.integration
def test_product_performance_agent_responds():
    agent = get_product_performance_agent()
    result = agent.invoke(
        {
            "messages": [
                HumanMessage(content="Show me the product performance for March 2026")
            ]
        }
    )
    # Just check the structure came back correctly
    assert "structured_response" in result
    response = result["structured_response"]
    assert isinstance(response, ProductPerformanceAgentResponse)
