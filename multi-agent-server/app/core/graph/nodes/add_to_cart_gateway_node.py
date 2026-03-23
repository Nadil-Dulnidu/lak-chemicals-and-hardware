from langgraph.types import interrupt

from app.core.graph.state import GraphState
from app.core.graph.nodes.base_node import BaseNode
from langchain_core.messages import HumanMessage


class AddToCartGatewayNode(BaseNode):
    def __init__(self):
        super().__init__("add_to_cart_gateway_node")

    def execute(self, state: GraphState) -> GraphState:
        self._log_start()
        return state
