from typing import Any, Dict

from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.graph.state import GraphState
from app.core.graph.nodes.base_node import BaseNode
from app.exceptions.graph_exceptions import AgentInvocationError
from langchain_core.messages import AIMessage


class ProductPerformanceNode(BaseNode):
    def __init__(self, agent):
        """
        Initialize the analytics router node.

        Args:
            agent: The analytics router agent.
        """
        super().__init__("product_performance_node")
        self.agent = agent

    def _format_to_markdown(self, response: Any) -> str:
        """
        Format the product performance structured response into a human-readable markdown string.
        """
        md = "---\n\n"
        md += f"### Product Performance\n\n"
        md += f"**{response.natural_language_summary}**\n\n"

        md += f"**Insights:**\n"
        md += f"- Performance Trend: {response.insights.performance_trend}\n"
        md += f"- Recommendation: {response.insights.recommendation}\n"
        if response.insights.top_product:
            md += f"- Top Product: {response.insights.top_product}\n"
        if response.insights.highest_demand_product:
            md += f"- Highest Demand Product: {response.insights.highest_demand_product}\n"

        md += f"\n**Summary:**\n"
        md += f"- Total Revenue: Rs.{response.summary.total_revenue:,.2f}\n"
        md += f"- Total Units Sold: {response.summary.total_quantity_sold}\n"

        if response.top_products:
            md += f"\n**Top Products:**\n"
            for item in response.top_products[:5]:
                md += f"- {item.product_name} (Sold: {item.total_quantity_sold}, Revenue: Rs.{item.total_revenue:,.2f})\n"

        return md.strip()

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def execute(self, state: GraphState) -> GraphState:
        """
        Execute the product intelligence node.

        Args:
            state: The graph state.

        Returns:
            The updated graph state.
        """
        try:
            self._log_start()

            # Get the user's query from the state
            analytics_inquiry_validation_response = state.get(
                "analytics_inquiry_validation_response", None
            )

            if not analytics_inquiry_validation_response:
                self._log_error("Clarification response not found")
                raise AgentInvocationError("Clarification response not found")

            analytics_inquiry_validation_response = (
                analytics_inquiry_validation_response.get("refined_query", "")
            )

            if analytics_inquiry_validation_response != "":
                user_query = analytics_inquiry_validation_response
            else:
                user_query = state.get("base_user_query", "")

            # Call the product intelligence agent
            response = self.agent.invoke({"messages": user_query})

            structured_response = response["structured_response"]

            # Format the structured response to markdown
            markdown_content = self._format_to_markdown(structured_response)

            self._log_end()

            return {
                "messages": AIMessage(content=markdown_content),
                "product_performance_response": structured_response.model_dump(),
            }
        except Exception as e:
            self._log_error(str(e))
            raise AgentInvocationError(f"Error in product intelligence node: {str(e)}")
