from typing import Any, Dict

from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.graph.state import GraphState
from app.core.graph.nodes.base_node import BaseNode
from app.exceptions.graph_exceptions import AgentInvocationError


class ProductSuggestionAgentNode(BaseNode):
    def __init__(self, agent):
        super().__init__("product_suggestion_node")
        self.agent = agent

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    def execute(self, state: GraphState) -> Dict[str, Any]:
        try:
            self._log_start(state)
            product_intelligence_response = state["product_intelligence_response"]

            if not product_intelligence_response:
                self._log_error(state, "Product intelligence response is required")
                raise ValueError("Product intelligence response is required")

            requirements = product_intelligence_response.requirements

            if not requirements:
                self._log_error(state, "Requirements are required")
                raise ValueError("Requirements are required")

            result = self.agent.invoke(
                {"messages": [HumanMessage(content=requirements)]}
            )

            structured_response = result["structured_response"]

            self._log_end(state)

            return {"product_suggestion_response": structured_response.model_dump()}
        except Exception as exc:
            self._log_error(state, str(exc))
            raise AgentInvocationError(
                "Failed to invoke product suggestion agent"
            ) from exc
