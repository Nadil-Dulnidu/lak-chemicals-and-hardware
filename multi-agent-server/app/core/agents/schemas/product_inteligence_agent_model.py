from pydantic import BaseModel, Field
from typing import List, Optional


class ProductRequirement(BaseModel):

    category: str = Field(
        ...,
        description="Hardware store product category such as tools, paints, electrical, plumbing, or hardware.",
    )

    purpose: str = Field(
        ...,
        description="Specific purpose or task the product will be used for, such as drilling, painting walls, or fixing leaks.",
    )

    keywords: List[str] = Field(
        ..., description="Important search keywords to identify suitable products."
    )

    required_features: List[str] = Field(
        ..., description="Essential features or specifications needed for the product."
    )

    optional_features: List[str] = Field(
        default_factory=list,
        description="Additional non-critical features that would improve usability or performance.",
    )

    estimated_budget: Optional[str] = Field(
        None, description="Approximate budget range such as low, medium, or high."
    )


class SafetyConsideration(BaseModel):

    risk: str = Field(
        ...,
        description="Potential risk associated with the task such as electrical hazard, sharp tools, or chemical exposure.",
    )

    recommendation: str = Field(..., description="Safety advice to mitigate the risk.")


class ProductIntelligenceAgentResponse(BaseModel):

    user_intent: str = Field(
        ..., description="Clear description of what the user wants to achieve."
    )

    task_type: str = Field(
        ...,
        description="Type of task such as installation, repair, maintenance, or construction.",
    )

    requirements: List[ProductRequirement] = Field(
        ...,
        description="List of structured product requirements derived from the user's request.",
    )

    suggested_search_queries: List[str] = Field(
        ...,
        description="Refined search queries that can be used to find matching products in the inventory.",
    )

    safety_considerations: List[SafetyConsideration] = Field(
        default_factory=list,
        description="Important safety considerations related to the task.",
    )

    natural_language_summary: str = Field(
        ...,
        description="User-friendly explanation of what products are needed and why.",
    )
