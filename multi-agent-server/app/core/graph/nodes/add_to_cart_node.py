from typing import Any, Dict

from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.graph.state import GraphState
from app.core.graph.nodes.base_node import BaseNode
from app.exceptions.graph_exceptions import AgentInvocationError
from langchain_core.messages import HumanMessage
from app.core.agents.schemas import AddToCartAgentResponse


class AddToCartNode(BaseNode):
    def __init__(self, agent):
        super().__init__("add_to_cart_node")
        self.agent = agent

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    def execute(self, state: GraphState) -> GraphState:
        try:
            self._log_start(state)
            product_suggestion_response = state["product_suggestion_response"]

            if not product_suggestion_response:
                self._log_error(state, "Product suggestion response is required")
                raise ValueError("Product suggestion response is required")

            product_suggestions = product_suggestion_response.suggestions

            if not product_suggestions:
                self._log_error(state, "Product suggestions are required")
                raise ValueError("Product suggestions are required")
            user_id = state["user_id"]

            query = f"""
                user id: {user_id}
                product suggestions: {product_suggestions}
            """

            result = self.agent.invoke({"messages": [HumanMessage(content=query)]})

            structured_response = result["structured_response"]

            return {
                "add_to_cart_response": structured_response.model_dump(),
            }

            self._log_end(state)
        except Exception as exc:
            self._log_error(state, str(exc))
            raise AgentInvocationError("Failed to invoke add to cart agent") from exc
