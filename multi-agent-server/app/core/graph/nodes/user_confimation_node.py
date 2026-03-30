from typing import Any, Dict

from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.graph.state import GraphState
from app.core.graph.nodes.base_node import BaseNode
from app.exceptions.graph_exceptions import AgentInvocationError
from langchain_core.messages import HumanMessage
from app.core.agents.schemas import UserConfirmationAgentResponse

from langchain_core.messages import AIMessage

import json


class UserConfirmationNode(BaseNode):
    def __init__(self, agent):
        super().__init__("user_confirmation_node")
        self.agent = agent

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    def execute(self, state: GraphState) -> GraphState:
        try:
            self._log_start()
            product_suggestion_response = state.get("product_suggestion_response", None)

            if not product_suggestion_response:
                self._log_error("Product suggestion response is required")
                raise ValueError("Product suggestion response is required")

            product_suggestions = product_suggestion_response.get("suggestions", None)

            if not product_suggestions:
                self._log_error("Product suggestions are required")
                raise ValueError("Product suggestions are required")

            query = f"""
                messages: {state.get("messages", [])},
                product_suggestions: {json.dumps(product_suggestions)}
            """

            result = self.agent.invoke({"messages": [HumanMessage(content=query)]})

            structured_response = result["structured_response"]

            if structured_response.confirmed == None:
                result = self._create_user_confirmation_process(
                    state, structured_response
                )
                self._log_end()
                return result
            else:
                if self._need_user_clarification(structured_response):
                    result = self._create_user_clarification_process(
                        state, structured_response
                    )
                    self._log_end()
                    return result
                else:
                    result = self._create_completed_state(state, structured_response)
                    self._log_end()
                    return result

            self._log_end()
        except Exception as exc:
            self._log_error(str(exc))
            raise AgentInvocationError("Failed to invoke add to cart agent") from exc

    def _create_user_confirmation_process(
        self, state: GraphState, structured_response: UserConfirmationAgentResponse
    ) -> Dict[str, Any]:
        """
        Create a user confirmation process.

        Args:
            state: The current state of the graph.
            structured_response: The response from the user confirmation agent.

        Returns:
            A user confirmation process.
        """
        return {
            "messages": AIMessage(content=""),
            "interrupt_question": structured_response.message_to_user,
        }

    def _need_user_clarification(
        self, structured_response: UserConfirmationAgentResponse
    ) -> bool:
        """
        Create a user accept or reject process.

        Args:
            structured_response: The response from the user confirmation agent.

        Returns:
            A user accept or reject process.
        """
        return structured_response.clarification_needed

    def _create_user_clarification_process(
        self, state: GraphState, structured_response: UserConfirmationAgentResponse
    ) -> Dict[str, Any]:
        """
        Create a user clarification process.

        Args:
            state: The current state of the graph.
            structured_response: The response from the user confirmation agent.

        Returns:
            A user clarification process.
        """
        return {
            "messages": AIMessage(content=""),
            "interrupt_question": structured_response.message_to_user,
        }

    def _create_completed_state(
        self, state: GraphState, structured_response: UserConfirmationAgentResponse
    ) -> Dict[str, Any]:
        """
        Create a completed state.

        Args:
            state: The current state of the graph.
            structured_response: The response from the user confirmation agent.

        Returns:
            A completed state.
        """
        return {
            "messages": AIMessage(content=structured_response.message_to_user),
            "user_confirmation_completed": True,
            "user_confirmation_response": structured_response.model_dump(),
            "should_execute_add_to_cart": structured_response.confirmed,
        }
