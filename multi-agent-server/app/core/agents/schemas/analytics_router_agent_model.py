from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from app.core.agents.constants import AnalyticsRouterAgentEnum

class AnalyticsRouterAgentModel(BaseModel):
    """Model for analytics router agent"""
    query_type: AnalyticsRouterAgentEnum = Field(..., description="Type of the user query")
    
    
    