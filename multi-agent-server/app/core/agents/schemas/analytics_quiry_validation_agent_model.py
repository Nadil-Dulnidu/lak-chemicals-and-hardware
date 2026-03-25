from pydantic import BaseModel, Field
from typing import List, Optional


class AnalyticsQueryValidationAgentResponse(BaseModel):
    in_scope: bool = Field(
        ...,
        description="Whether the user query is related to supported admin analytics capabilities."
    )

    is_clear: bool = Field(
        ...,
        description="Whether the query is clear enough to route to a specific analytics agent without further clarification."
    )

    clarification_needed: bool = Field(
        ...,
        description="Whether the system needs additional clarification before continuing to the analytics router agent."
    )

    is_user_answer_for_clarification: bool = Field(
        ...,
        description="True if the current user message is answering a previously asked clarification question."
    )

    validation_status: str = Field(
        ...,
        description="Validation result. Possible values: 'valid', 'out_of_scope', 'missing_details', 'ambiguous'."
    )

    missing_fields: List[str] = Field(
        default_factory=list,
        description="Important missing details required to properly route or process the analytics request, such as date range, category, product, or forecast period."
    )

    clarification_question: Optional[str] = Field(
        None,
        description="A single most important follow-up question to ask the admin user when clarification is needed."
    )

    refined_query: Optional[str] = Field(
        None,
        description="A cleaned and more explicit version of the analytics query, ready for the analytics router agent."
    )

    reasoning: str = Field(
        ...,
        description="Short explanation of why the query is valid, unclear, ambiguous, or out of scope."
    )

    message_to_user: str = Field(
        ...,
        description="Friendly message either asking for clarification or confirming that the request is understood."
    )