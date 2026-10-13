"""
Router for autonomous AI report analysis.
"""

from fastapi import APIRouter, Depends, status
from app.configs.logging import get_logger
from app.schemas.report_analysis_schemas import ReportAnalysisRequest, ReportAnalysisResponse
from app.services.report_analysis_service import report_analysis_service
from app.security.api_key import verify_api_key

logger = get_logger(__name__)

report_analysis_router = APIRouter(
    prefix="/api/v1/reports",
    tags=["Reports Analysis"],
)


@report_analysis_router.post(
    "/analyze",
    response_model=ReportAnalysisResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_api_key)],
)
async def analyze_report_endpoint(payload: ReportAnalysisRequest) -> ReportAnalysisResponse:
    """
    Generate autonomous AI analysis and recommendations for raw business reports.
    
    Protected by inter-service API key header (`x-api-key`).
    Invoked directly by business-server during owner/admin report generation.
    """
    logger.info("Received report analysis request for: %s", payload.report_type)
    return await report_analysis_service.analyze_report(payload)
