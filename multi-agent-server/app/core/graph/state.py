from langgraph.graph import MessagesState
from app.core.agents.schemas import ClarificationValidationAgentResponse


class GraphState(MessagesState):
    """State for the graph."""

    user_id: str | None = None
    is_admin: bool = False
    clarification_questions: list[str] = []
    clarification_answers: list[str] = []
    interrupt_question: str | None = None
    clarification_validation_completed: bool = False
    clarification_validation_response: ClarificationValidationAgentResponse | None = (
        None
    )
