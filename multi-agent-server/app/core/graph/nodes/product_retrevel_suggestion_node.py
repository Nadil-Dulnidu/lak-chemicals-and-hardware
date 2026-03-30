from typing import Any, Dict

from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.graph.state import GraphState
from app.core.graph.nodes.base_node import BaseNode
from app.exceptions.graph_exceptions import AgentInvocationError

from langchain_core.messages import HumanMessage, AIMessage
import json

from app.core.agents.constants.enums import ProductRetrievalSuggestionAgentEnum


class ProductSuggestionAgentNode(BaseNode):
    def __init__(self, agent):
        super().__init__("product_suggestion_node")
        self.agent = agent

    def _format_suggestions_markdown(self, response) -> str:
        """Helper to format the suggestion response into a readable Markdown string."""
        md_parts = []

        md_parts.append("---\n\n")

        if response.message_to_user:
            md_parts.append(f"{response.message_to_user}\n")

        if response.suggestions:
            for p in response.suggestions:
                price_str = f"Rs. {p.price:,.2f}"
                stock_info = (
                    f"*(Stock: {p.stock_qty})*"
                    if p.stock_qty > 0
                    else "*(Out of Stock)*"
                )

                md_parts.append(f"- **{p.name}** — {price_str} {stock_info}")
                md_parts.append(f"  > {p.short_reason}\n")

        md_parts.append("---\n\n")

        return "\n".join(md_parts)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    def execute(self, state: GraphState) -> Dict[str, Any]:
        try:
            self._log_start()
            product_intelligence_response = state["product_intelligence_response"]

            if not product_intelligence_response:
                self._log_error("Product intelligence respo nse is required")
                raise ValueError("Product intelligence response is required")

            requirements = product_intelligence_response.get("requirements", None)

            if not requirements:
                self._log_error("Requirements are required")
                raise ValueError("Requirements are required")

            result = self.agent.invoke(
                {"messages": [HumanMessage(content=json.dumps(requirements))]}
            )

            structured_response = result["structured_response"]

            content = None

            if (
                structured_response.availability_status
                == ProductRetrievalSuggestionAgentEnum.AVAILABLE
                or structured_response.availability_status
                == ProductRetrievalSuggestionAgentEnum.ALTERNATIVE_AVAILABLE
            ):
                content = self._format_suggestions_markdown(structured_response)
            else:
                content = ""

            self._log_end()

            return {
                "messages": AIMessage(content=content),
                "product_suggestion_response": structured_response.model_dump(),
            }
        except Exception as exc:
            self._log_error(str(exc))
            raise AgentInvocationError(
                "Failed to invoke product suggestion agent"
            ) from exc
