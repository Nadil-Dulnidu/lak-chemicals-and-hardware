import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.api import app
from app.schemas.report_analysis_schemas import ReportAnalysisRequest, ReportAnalysisResponse
from app.services.report_analysis_service import ReportAnalysisService

client = TestClient(app)

VALID_API_KEY = "l534ZA3RKXewEG+Ch4bFXHXltV38zOWd/kDO5+IEQdge2jsNS33uMFxiBDTr3ZkTQWyG8sex35FwIaY04iN6Yg=="

@pytest.mark.asyncio
async def test_report_analysis_service_success():
    service = ReportAnalysisService()
    
    mock_llm_response = MagicMock()
    mock_llm_response.content = """```json
{
  "report_type": "SALES",
  "summary": "Revenue increased by 15% across all categories.",
  "insights": ["Highest volume was in building materials.", "Retail customer conversion rose."],
  "recommendations": ["Restock cement inventory.", "Run promotion on fasteners."],
  "risk_alerts": ["Supply chain delay in chemical imports."]
}
```"""
    
    service.model = MagicMock()
    service.model.invoke.return_value = mock_llm_response

    req = ReportAnalysisRequest(
        report_type="SALES",
        data={"total_sales": 150000, "orders": 42},
        metadata={"start_date": "2026-09-01", "end_date": "2026-09-30"}
    )
    response = await service.analyze_report(req)
    
    assert response.report_type == "SALES"
    assert "15%" in response.summary
    assert len(response.insights) == 2
    assert len(response.recommendations) == 2
    assert len(response.risk_alerts) == 1
    assert "Supply chain" in response.risk_alerts[0]


def test_report_analysis_api_unauthorized():
    response = client.post(
        "/api/v1/reports/analyze",
        headers={"x-api-key": "invalid-wrong-key"},
        json={"report_type": "SALES", "data": {"test": 123}}
    )
    assert response.status_code == 401


def test_report_analysis_api_authorized():
    mock_response = ReportAnalysisResponse(
        report_type="SALES",
        summary="Test executive summary",
        insights=["Insight 1"],
        recommendations=["Action 1"],
        risk_alerts=[]
    )
    
    with patch("app.routers.report_analysis_router.report_analysis_service.analyze_report", return_value=mock_response):
        response = client.post(
            "/api/v1/reports/analyze",
            headers={"x-api-key": VALID_API_KEY},
            json={
                "report_type": "SALES",
                "data": {"revenue": 50000},
                "metadata": {"period": "last_week"}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["report_type"] == "SALES"
        assert data["summary"] == "Test executive summary"
        assert data["insights"] == ["Insight 1"]
