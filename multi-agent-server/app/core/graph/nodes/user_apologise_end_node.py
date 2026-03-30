from typing import Any, Dict

from app.core.graph.state import GraphState
from app.core.graph.nodes.base_node import BaseNode

from langchain_core.messages import AIMessage


class UserApologiseEndNode(BaseNode):
    def __init__(self):
        """
        Initialize the user apologise end node.

        Args:
            agent: The user apologise end agent.
        """
        super().__init__("user_apologise_end_node")

    def execute(self, state: GraphState) -> GraphState:
        """
        Execute the product intelligence node.

        Args:
            state: The graph state.

        Returns:
            The updated graph state.
        """
        self._log_start()

        message_to_user = (
            "---\n\n"
            "### 😔 We're Sorry!\n\n"
            "**Unfortunately, we don't currently sell or stock the specific items you are looking for.**\n\n"
            "Lak Chemicals and Hardware specializes in a wide variety of hardware equipment, building materials, and industrial chemicals. "
            "While we cannot fulfill this specific request, we might have alternative solutions that could work for your needs.\n\n"
            "Please feel free to ask about our available products, and we would be more than happy to assist you further! 🛠️🧪"
        )

        self._log_end()

        return {
            "messages": AIMessage(content=message_to_user),
        }
