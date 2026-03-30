from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class ClarificationValidationAgentResponse(BaseModel):

    in_scope: bool = Field(
        ..., description="Whether the query is related to hardware store domain."
    )

    is_clear: bool = Field(
        ..., description="Whether the query has enough detail to proceed."
    )

    clarification_needed: bool = Field(
        ..., description="True if more answers are required before proceeding."
    )

    clarification_type: str = Field(
        ...,
        description="Type of clarification: out_of_scope, missing_details, ambiguous, none.",
    )

    clarification_questions: List[str] = Field(
        default_factory=list,
        description="List of all required clarification questions.",
    )

    clarification_answers: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of questions to user-provided answers.",
    )

    refined_query: Optional[str] = Field(
        None, description="Final refined query after all clarifications are completed."
    )

    message_to_user: str = Field(
        ...,
        description="Friendly message either asking for clarification or confirming that the request is understood.",
    )
