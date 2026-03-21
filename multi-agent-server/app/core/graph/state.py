from langgraph.graph import MessagesState
from app.core.agents.schemas import (
    ClarificationValidationAgentResponse,
    ProductIntelligenceAgentResponse,
    ProductSuggestionAgentResponse,
)


class GraphState(MessagesState):
    """State for the graph."""

    user_id: str | None = None
    is_admin: bool = False
    base_user_query: str | None = None
    interrupt_question: str | None = None
    clarification_validation_completed: bool = False
    clarification_validation_response: ClarificationValidationAgentResponse | None = (
        None
    )
    product_intelligence_response: ProductIntelligenceAgentResponse | None = None
    product_suggestion_response: ProductSuggestionAgentResponse | None = None
