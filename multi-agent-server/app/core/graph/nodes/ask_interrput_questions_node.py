from langgraph.types import interrupt

from app.core.graph.state import GraphState
from app.core.graph.nodes.base_node import BaseNode
from langchain_core.messages import HumanMessage


class AskInterruptQuestionsNode(BaseNode):
    def __init__(self):
        super().__init__("ask_interrupt_questions_node")

    def execute(self, state: GraphState) -> GraphState:
        self._log_start()

        interruption_question = state.get("interrupt_question", None)

        if interruption_question:
            self.logger.info(
                f"Triggering interrupt with question: {interruption_question}"
            )

            user_response = interrupt(interruption_question)
            self._log_end(f"Interrupt resolved with answer: {user_response}")

            return {
                "messages": [HumanMessage(content=user_response)],
                "interrupt_question": None,
            }
        else:
            self._log_end("No interruption needed")

        return state
