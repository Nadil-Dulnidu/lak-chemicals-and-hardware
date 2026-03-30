from typing import Any, Dict

from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.graph.state import GraphState
from app.core.graph.nodes.base_node import BaseNode
from app.exceptions.graph_exceptions import AgentInvocationError


class ProductPerformanceNode(BaseNode):
    def __init__(self, agent):
        """
        Initialize the analytics router node.

        Args:
            agent: The analytics router agent.
        """
        super().__init__("product_performance_node")
        self.agent = agent

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def execute(self, state: GraphState) -> GraphState:
        """
        Execute the product intelligence node.

        Args:
            state: The graph state.

        Returns:
            The updated graph state.
        """
        try:
            self._log_start()

            # Get the user's query from the state
            analytics_inquiry_validation_response = state["analytics_router_response"]

            if not analytics_inquiry_validation_response:
                self._log_error(state, "Clarification response not found")
                raise AgentInvocationError("Clarification response not found")

            if analytics_inquiry_validation_response.refined_query != "":
                user_query = analytics_inquiry_validation_response.refined_query
            else:
                user_query = state.get("base_user_query", "")

            # Call the product intelligence agent
            response = self.agent.invoke({"messages": user_query})

            structured_response = response["structured_response"]

            self._log_end()

            return {
                "product_performance_response": structured_response.model_dump(),
            }
        except Exception as e:
            self._log_error(str(e))
            raise AgentInvocationError(f"Error in product intelligence node: {str(e)}")
