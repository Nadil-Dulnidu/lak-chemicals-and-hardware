from typing import Any, Dict

from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.graph.state import GraphState
from app.core.graph.nodes.base_node import BaseNode
from app.exceptions.graph_exceptions import AgentInvocationError
from langchain_core.messages import HumanMessage, AIMessage

import json


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
            self._log_start()
            user_confirmation_response = state.get("user_confirmation_response", None)

            if not user_confirmation_response:
                self._log_error("User confirmation response is required")
                raise ValueError("User confirmation response is required")

            selected_items = user_confirmation_response.get("selected_items", None)

            if not selected_items:
                self._log_error("Selected items are required")
                raise ValueError("Selected items are required")

            user_id = state["user_id"]

            query = f"""
                user id: {user_id}
                user selected items: {json.dumps(selected_items)}
            """

            print(f"Invoking add to cart agent with query: {query}")

            result = self.agent.invoke({"messages": [HumanMessage(content=query)]})

            structured_response = result["structured_response"]

            self._log_end()

            return {
                "messages": AIMessage(content=structured_response.message_to_user),
                "add_to_cart_response": structured_response.model_dump(),
            }

        except Exception as exc:
            self._log_error(str(exc))
            raise AgentInvocationError("Failed to invoke add to cart agent") from exc
