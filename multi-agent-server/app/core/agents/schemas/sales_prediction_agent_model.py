from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class HistoricalSalesSummary(BaseModel):

    total_sales: int = Field(
        ...,
        description="Total number of sales transactions observed in the historical period used for forecasting.",
    )

    total_revenue: float = Field(
        ...,
        description="Total revenue generated during the historical analysis period.",
    )

    total_quantity: int = Field(
        ...,
        description="Total number of product units sold during the historical period.",
    )

    average_sale_value: float = Field(
        ...,
        description="Average value of a single sale transaction during the historical period.",
    )


class ForecastItem(BaseModel):

    period: str = Field(
        ...,
        description="Future time period for which the prediction is generated. Format depends on grouping (day/week/month).",
    )

    predicted_sales: int = Field(
        ...,
        description="Predicted number of sales transactions expected in this period.",
    )

    predicted_revenue: float = Field(
        ..., description="Predicted total revenue expected during this period."
    )

    predicted_quantity: int = Field(
        ..., description="Predicted number of product units expected to be sold."
    )


class PredictionInsight(BaseModel):

    expected_growth_rate: float = Field(
        ...,
        description="Expected percentage growth or decline in revenue compared to the historical period.",
    )

    predicted_top_product: Optional[str] = Field(
        None,
        description="Product expected to generate the highest revenue during the prediction period.",
    )

    predicted_top_category: Optional[str] = Field(
        None,
        description="Category expected to generate the highest revenue during the prediction period.",
    )

    demand_trend: str = Field(
        ...,
        description="Overall expected demand trend. Possible values include increasing, decreasing, or stable.",
    )

    risk_level: str = Field(
        ...,
        description="Estimated risk level of the prediction such as low, medium, or high depending on data variability.",
    )


class SalesPredictionAgentResponse(BaseModel):

    report_type: str = Field(
        ...,
        description="Type of analytics report generated. Always 'SALES_PREDICTION' for this agent.",
    )

    historical_start_date: datetime = Field(
        ...,
        description="Start date of the historical data used to generate the prediction.",
    )

    historical_end_date: datetime = Field(
        ..., description="End date of the historical data used for forecasting."
    )

    prediction_start_date: datetime = Field(
        ..., description="Start date of the future prediction window."
    )

    prediction_end_date: datetime = Field(
        ..., description="End date of the future prediction window."
    )

    historical_summary: HistoricalSalesSummary = Field(
        ...,
        description="Summary of historical sales data used as the basis for forecasting.",
    )

    forecast: List[ForecastItem] = Field(
        ..., description="Predicted sales performance for future periods."
    )

    insights: PredictionInsight = Field(
        ...,
        description="AI-generated insights explaining the expected sales behavior and trends.",
    )

    natural_language_summary: str = Field(
        ...,
        description="Human-readable explanation summarizing the predicted sales trends and expected business impact.",
    )
