import pytest
from langchain_core.messages import HumanMessage
from app.core.agents.agents import get_sales_prediction_agent
from app.core.agents.schemas import SalesPredictionAgentResponse


@pytest.mark.integration
def test_sales_prediction_agent_responds():
    agent = get_sales_prediction_agent()
    result = agent.invoke(
        {
            "messages": [
                HumanMessage(
                    content="Baed on past Sales summeries predict next month sales"
                )
            ]
        }
    )
    # Just check the structure came back correctly
    assert "structured_response" in result
    response = result["structured_response"]
    assert isinstance(response, SalesAnalyticsAgentResponse)
