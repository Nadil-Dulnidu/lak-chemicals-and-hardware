from typing import Any, Dict

from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.graph.state import GraphState
from app.core.graph.nodes.base_node import BaseNode
from app.exceptions.graph_exceptions import AgentInvocationError
from langchain_core.messages import AIMessage
from app.core.agents.schemas import ClarificationValidationAgentResponse


class ClarificationValidationNode(BaseNode):
    """
    Node for invoking the clarification validation agent.
    """

    def __init__(self, agent):
        """
        Initialize the clarification validation node.

        Args:
            agent: The clarification validation agent.
        """
        super().__init__("clarification_validation_node")
        self.agent = agent

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def execute(self, state: GraphState) -> GraphState:
        """
        Invoke the clarification validation agent.

        Args:
            state: The current state of the graph.

        Returns:
            The response from the clarification validation agent.
        """
        self._log_start()
        try:
            messages = state["messages"]
            response = self.agent.invoke({"messages": messages})
            if not response:
                self._log_error("Empty response from agent")
                raise AgentInvocationError("Empty response from agent")

            self._log_end("Clarification validation agent invoked successfully")

            structured_response = response["structured_response"]

            if structured_response.current_question:
                result = self._create_clarification_message(state, structured_response)
                self._log_end("Clarification message created successfully")
                return result
            else:
                result = self._create_completed_state(state, structured_response)
                self._log_end("Completed state created successfully")
                return result

            return result

        except Exception as e:
            self._log_error(str(e))
            raise AgentInvocationError(str(e))

    def _create_clarification_message(
        self,
        state: GraphState,
        structured_response: ClarificationValidationAgentResponse,
    ) -> Dict[str, Any]:
        """
        Create a clarification message.

        Args:
            state: The current state of the graph.
            structured_response: The response from the clarification validation agent.

        Returns:
            A clarification message.
        """
        return {
            "interrupt_question": structured_response.current_question,
        }

    def _create_completed_state(
        self,
        state: GraphState,
        structured_response: ClarificationValidationAgentResponse,
    ) -> Dict[str, Any]:
        """
        Create a completed state.

        Args:
            state: The current state of the graph.

        Returns:
            A completed state.
        """
        return {
            "interrupt_question": None,
            "clarification_validation_completed": True,
            "clarification_validation_response": structured_response.model_dump(),
        }
