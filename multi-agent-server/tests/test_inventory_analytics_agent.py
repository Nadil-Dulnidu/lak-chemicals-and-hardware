import pytest
from langchain_core.messages import HumanMessage
from app.core.agents.agents import get_inventory_analytics_agent
from app.core.agents.schemas import InventoryAnalyticsAgentResponse


@pytest.mark.integration7
def test_inventory_analytics_agent_responds():
    agent = get_inventory_analytics_agent()
    result = agent.invoke(
        {"messages": [HumanMessage(content="Show me the all inventory report")]}
    )
    # Just check the structure came back correctly
    assert "structured_response" in result
    response = result["structured_response"]
    assert isinstance(response, InventoryAnalyticsAgentResponse)
