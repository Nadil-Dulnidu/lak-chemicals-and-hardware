import pytest
from langchain_core.messages import HumanMessage
from app.core.agents.agents import get_analytics_router_agent
from app.core.agents.schemas import AnalyticsRouterAgentResponse


@pytest.mark.integration
def test_analytics_router_agent_responds():
    agent = get_analytics_router_agent()
    result = agent.invoke(
        {"messages": [HumanMessage(content="Show me the sales summary")]}
    )
    # Just check the structure came back correctly
    assert "structured_response" in result
    response = result["structured_response"]
    assert isinstance(response, AnalyticsRouterAgentResponse)
