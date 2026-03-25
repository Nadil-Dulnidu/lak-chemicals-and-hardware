from typing import Any, Dict

from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.graph.state import GraphState
from app.core.graph.nodes.base_node import BaseNode
from app.exceptions.graph_exceptions import AgentInvocationError


class ProductIntelligenceAgentNode(BaseNode):
    def __init__(self, agent):
        """
        Initialize the product intelligence node.

        Args:
            agent: The product intelligence agent.
        """
        super().__init__("product_intelligence_node")
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
            self._log_start(state)

            # Get the user's query from the state
            clarification_response = state["clarification_validation_response"]

            if not clarification_response:
                self._log_error(state, "Clarification response not found")
                raise AgentInvocationError("Clarification response not found")

            if clarification_response.refined_query != "":
                user_query = clarification_response.refined_query
            else:
                user_query = state.get("base_user_query", "")

            # Call the product intelligence agent
            response = self.agent.invoke({"messages": user_query})

            structured_response = response["structured_response"]

            self._log_end(state)

            return {
                "product_intelligence_response": structured_response.model_dump(),
            }
        except Exception as e:
            self._log_error(state, str(e))
            raise AgentInvocationError(f"Error in product intelligence node: {str(e)}")
