from typing import Optional, Any, Dict
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.base import BaseCheckpointSaver

from app.configs.logging import get_logger
from app.core.observability.langfuse_tracing import (
    langfuse,
    sanitize_state,
)
from app.core.graph.state import GraphState
from app.core.graph.nodes import (
    ClarificationValidationNode,
    AskInterruptQuestionsNode,
    ProductIntelligenceAgentNode,
    ProductSuggestionAgentNode,
    UserConfirmationNode,
    AddToCartGatewayNode,
    AddToCartNode,
    UserApologiseEndNode,
)
from app.core.agents.constants import ProductRetrievalSuggestionAgentEnum

logger = get_logger(__name__)


class GraphBuilder:
    """
    Builds and compiles the customer conversational workflow graph.

    This graph handles:
    1. Customer product requirement clarification
    2. Product intelligence and stock lookup
    3. Product suggestion and alternatives
    4. User confirmation for ordering/cart additions
    5. Adding items to cart
    """

    def __init__(
        self,
        clarification_validation_agent,
        product_intelligence_agent,
        product_suggestion_agent,
        user_confirmation_agent,
        add_to_cart_agent,
        checkpointer: Optional[BaseCheckpointSaver] = None,
    ):
        self.state_graph = StateGraph(GraphState)
        self.checkpointer = checkpointer or InMemorySaver()

        # Initialize nodes with their dependencies (customer flow only)
        self.nodes = {
            "clarification_validation": ClarificationValidationNode(
                clarification_validation_agent
            ),
            "ask_interrupt_questions_for_user_clarification_confirmation": AskInterruptQuestionsNode(),
            "product_intelligence": ProductIntelligenceAgentNode(
                product_intelligence_agent
            ),
            "product_suggestion": ProductSuggestionAgentNode(product_suggestion_agent),
            "user_confirmation": UserConfirmationNode(user_confirmation_agent),
            "ask_interrupt_questions_for_add_to_cart_confirmation": AskInterruptQuestionsNode(),
            "add_to_cart_gateway": AddToCartGatewayNode(),
            "add_to_cart": AddToCartNode(add_to_cart_agent),
            "user_apologise_end": UserApologiseEndNode(),
        }

        logger.info(
            "GraphBuilder initialized with customer workflow nodes: %s",
            list(self.nodes.keys()),
        )

    def _add_nodes(self) -> None:
        """Add all nodes to the state graph."""
        for node_name, node_instance in self.nodes.items():
            def traced_execute(
                state: GraphState,
                _node_name: str = node_name,
                _node_instance=node_instance,
            ):
                with langfuse.start_as_current_observation(
                    name=_node_name,
                    as_type="span",
                    metadata={"node_type": "langgraph_node"},
                ) as span:
                    span.update(input={"state": sanitize_state(state)})

                    metadata: Dict[str, Any] = {
                        "clarification_done": state.get(
                            "clarification_validation_completed"
                        ),
                        "user_confirmation_done": state.get(
                            "user_confirmation_completed"
                        ),
                        "should_add_to_cart": state.get("should_execute_add_to_cart"),
                    }

                    if _node_name in {"add_to_cart_gateway", "user_confirmation"}:
                        if state.get("should_execute_add_to_cart") is not None:
                            metadata["should_execute_add_to_cart"] = state.get(
                                "should_execute_add_to_cart"
                            )
                        if state.get("user_confirmation_completed") is not None:
                            metadata["user_confirmation_completed"] = state.get(
                                "user_confirmation_completed"
                            )

                    metadata = {k: v for k, v in metadata.items() if v is not None}
                    if metadata:
                        span.update(metadata=metadata)

                    try:
                        result = _node_instance.execute(state)
                        span.update(output={"state": sanitize_state(result)})
                        return result
                    except Exception as e:
                        span.update(level="ERROR", status_message=str(e))
                        raise

            self.state_graph.add_node(node_name, traced_execute)
            logger.debug(f"Added node: {node_name}")

    def _add_edges(self) -> None:
        """Define customer flow edges and transitions between nodes."""
        # Direct entry from START to customer clarification
        self.state_graph.add_edge(START, "clarification_validation")

        self.state_graph.add_conditional_edges(
            "clarification_validation",
            self._should_ask_more_questions,
            {
                True: "ask_interrupt_questions_for_user_clarification_confirmation",
                False: "product_intelligence",
            },
        )

        self.state_graph.add_edge(
            "ask_interrupt_questions_for_user_clarification_confirmation",
            "clarification_validation",
        )

        self.state_graph.add_edge("product_intelligence", "product_suggestion")

        self.state_graph.add_conditional_edges(
            "product_suggestion",
            self._check_suggest_product_available,
            {
                True: "user_confirmation",
                False: "user_apologise_end",
            },
        )

        self.state_graph.add_edge("user_apologise_end", END)

        self.state_graph.add_conditional_edges(
            "user_confirmation",
            self._should_ask_user_clarification,
            {
                True: "ask_interrupt_questions_for_add_to_cart_confirmation",
                False: "add_to_cart_gateway",
            },
        )

        self.state_graph.add_edge(
            "ask_interrupt_questions_for_add_to_cart_confirmation", "user_confirmation"
        )

        self.state_graph.add_conditional_edges(
            "add_to_cart_gateway",
            self._should_execute_add_to_cart,
            {
                True: "add_to_cart",
                False: END,
            },
        )

        self.state_graph.add_edge("add_to_cart", END)
        logger.debug("Customer workflow graph edges configured")

    def _should_ask_more_questions(self, state: GraphState) -> bool:
        needs_more_questions = not state.get("clarification_validation_completed")
        logger.debug(f"Should ask more questions: {needs_more_questions}")
        return needs_more_questions

    def _should_ask_user_clarification(self, state: GraphState) -> bool:
        needs_user_clarification = not state.get("user_confirmation_completed", False)
        logger.debug(f"Should ask user clarification: {needs_user_clarification}")
        return needs_user_clarification

    def _should_execute_add_to_cart(self, state: GraphState) -> bool:
        should_execute_add_to_cart = state.get("should_execute_add_to_cart", False)
        logger.debug(f"Should execute add to cart: {should_execute_add_to_cart}")
        return should_execute_add_to_cart

    def _check_suggest_product_available(self, state: GraphState) -> bool:
        suggestion_resp = state.get("product_suggestion_response")
        if not suggestion_resp:
            logger.debug("Suggested product response is missing")
            return False

        suggest_product_available = suggestion_resp.get("availability_status", None)
        if not suggest_product_available:
            return False

        if (
            suggest_product_available == ProductRetrievalSuggestionAgentEnum.AVAILABLE
            or suggest_product_available
            == ProductRetrievalSuggestionAgentEnum.ALTERNATIVE_AVAILABLE
        ):
            return True
        return False

    def build(self) -> StateGraph:
        """Build and compile the customer workflow graph."""
        logger.info("Building customer flow graph...")
        self._add_nodes()
        self._add_edges()
        compiled_graph = self.state_graph.compile(checkpointer=self.checkpointer)
        logger.info("Customer flow graph built successfully")
        return compiled_graph
