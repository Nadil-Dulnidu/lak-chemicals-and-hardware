from typing import Any, Dict

from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.graph.state import GraphState
from app.core.graph.nodes.base_node import BaseNode
from app.exceptions.graph_exceptions import AgentInvocationError
from langchain_core.messages import AIMessage
from app.core.agents.schemas import AnalyticsQueryValidationAgentResponse

class AnalyticsQueryValidationNode(BaseNode):
    """
    Node that validates analytics inquiry using the analytics inquiry validation agent.

    This node uses the analytics inquiry validation agent to validate the user's
    analytics inquiry and returns an AnalyticsQueryValidationAgentResponse as structured output.
    """

    def __init__(self, agent):
        super().__init__("analytics_query_validation_node")
        self.agent = agent

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    def execute(self, state: GraphState) -> Dict[str, Any]:
        """
        Invoke the analytics inquiry validation agent with the given state.

        Args:
            state: The current graph state.

        Returns:
            A dictionary containing the analytics inquiry validation agent response.
        """
        self._log_start()
        try:
            response = self.agent.invoke({"messages": state["messages"]})
            if not response:
                self._log_error("Empty response from agent")
                raise AgentInvocationError("Empty response from agent")

            structured_response = response["structured_response"]

            if structured_response.clarification_needed:
              result = self._handle_clarification_needed(state, structured_response)
              self._log_end("Clarification needed")
              return result
            else:
              result = self._handle_clarification_not_needed(state, structured_response)
              self._log_end("Clarification not needed")
              return result

        except Exception as exc:
            raise AgentInvocationError(
                "Failed to invoke analytics inquiry validation agent",
                agent_name="analytics_inquiry_validation_agent",
                original_exception=exc,
            ) from exc
    
    def _handle_clarification_needed(self, state: GraphState, structured_response: AnalyticsQueryValidationAgentResponse) -> Dict[str, Any]:
        """
        Handle the case where clarification is needed.

        Args:
            state: The current graph state.
            structured_response: The analytics inquiry validation agent response.

        Returns:
            A dictionary containing the analytics inquiry validation agent response.
        """
        return {
            "interrupt_question": structured_response.message_to_user,
        }

    def _handle_clarification_not_needed(self, state: GraphState, structured_response: AnalyticsQueryValidationAgentResponse) -> Dict[str, Any]:
        """
        Handle the case where clarification is not needed.

        Args:
            state: The current graph state.
            structured_response: The analytics inquiry validation agent response.

        Returns:
            A dictionary containing the analytics inquiry validation agent response.
        """
        return {
            "messages": [AIMessage(content=structured_response.message_to_user)],
            "analytics_inquiry_validation_completed": True,
            "analytics_inquiry_validation_response": structured_response.model_dump(),
        }