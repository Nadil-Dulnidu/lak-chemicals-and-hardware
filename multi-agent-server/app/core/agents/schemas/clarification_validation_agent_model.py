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

    current_question: Optional[str] = Field(
        None,
        description="The next question to ask the user. Only one question at a time.",
    )

    refined_query: Optional[str] = Field(
        None, description="Final refined query after all clarifications are completed."
    )
