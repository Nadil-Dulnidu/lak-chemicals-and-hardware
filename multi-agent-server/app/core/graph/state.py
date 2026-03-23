from langgraph.graph import MessagesState
from app.core.agents.schemas import (
    ClarificationValidationAgentResponse,
    ProductIntelligenceAgentResponse,
    ProductSuggestionAgentResponse,
    AddToCartAgentResponse,
    UserConfirmationAgentResponse,
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
    user_confirmation_response: UserConfirmationAgentResponse | None = None
    user_confirmation_completed: bool = False
    should_execute_add_to_cart: bool | None = None
    add_to_cart_response: AddToCartAgentResponse | None = None
