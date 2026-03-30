from enum import Enum


class AnalyticsRouterAgentEnum(Enum):
    """Enum for analytics router agent"""

    SALES_PREDICTION = "sales_prediction"
    SALES_ANALYSIS = "sales_analysis"
    INVENTORY_ANALYSIS = "inventory_analysis"
    PRODUCT_PERFORMANCE = "product_performance"


class ProductRetrievalSuggestionAgentEnum(Enum):
    """Enum for product retrieval suggestion agent"""

    AVAILABLE = "AVAILABLE"
    ALTERNATIVE_AVAILABLE = "ALTERNATIVE_AVAILABLE"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    NOT_SOLD = "NOT_SOLD"
