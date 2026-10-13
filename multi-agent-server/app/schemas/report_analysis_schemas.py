"""
Schemas for autonomous report analysis.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class ReportAnalysisRequest(BaseModel):
    """Payload received from the business-server containing raw database report data."""
    report_type: str = Field(
        ...,
        description="Type of report: SALES, INVENTORY, PRODUCT_PERFORMANCE, LOW_STOCK, SALES_PREDICTION"
    )
    data: Union[Dict[str, Any], List[Any]] = Field(
        ...,
        description="Raw structured report data from database queries"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional filter context such as start_date, end_date, generated_by"
    )


class ReportAnalysisResponse(BaseModel):
    """Structured AI executive report analysis and recommendations."""
    report_type: str = Field(..., description="Report type processed")
    summary: str = Field(..., description="Executive summary of key findings")
    insights: List[str] = Field(
        default_factory=list,
        description="Key trends, volume analysis, and performance metrics"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Actionable business recommendations for management"
    )
    risk_alerts: List[str] = Field(
        default_factory=list,
        description="Critical risk alerts regarding stockouts, low margins, or delayed orders"
    )
