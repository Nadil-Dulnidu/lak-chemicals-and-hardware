from app.configs.logging import get_logger
from typing import Optional

from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.base import BaseCheckpointSaver

from app.core.graph.state import GraphState
from app.core.graph.nodes import (
    ClarificationValidationNode,
    AskInterruptQuestionsNode,
    ProductIntelligenceAgentNode,
    ProductSuggestionAgentNode,
    UserConfirmationNode,
    AddToCartGatewayNode,
    AddToCartNode,
    AnalyticsQueryValidationNode,
    AnalyticsRouterNode,
    InventoryAnalyticsNode,
    ProductPerformanceNode,
    SalesAnalyticsNode,
    SalesPredictionNode,
    UserApologiseEndNode,
)

from app.core.agents.constants import (
    AnalyticsRouterAgentEnum,
    ProductRetrievalSuggestionAgentEnum,
)

logger = get_logger(__name__)


class GraphBuilder:
    """
    Builds and compiles the workflow graph.

    This class is responsible for:
    1. Creating node instances with their dependencies
    2. Adding nodes to the graph
    3. Defining edges and conditional routing
    4. Compiling the graph with checkpointing

    Attributes:
        state_graph (StateGraph): The underlying LangGraph state graph.
        checkpointer (BaseCheckpointSaver): Checkpointer for conversation persistence.
        nodes (dict): Dictionary of initialized node instances.
    """

    def __init__(
        self,
        clarification_validation_agent,
        product_intelligence_agent,
        product_suggestion_agent,
        user_confirmation_agent,
        add_to_cart_agent,
        analytics_query_validation_agent,
        analytics_router_agent,
        inventory_analytics_agent,
        product_performance_agent,
        sales_analytics_agent,
        sales_prediction_agent,
        checkpointer: Optional[BaseCheckpointSaver] = None,
    ):
        """
        Initialize the graph builder.

        Args:
            clarification_validation_agent: The agent for clarification validation.
            checkpointer: Optional checkpointer for state persistence.
                         Defaults to InMemorySaver if not provided.
        """
        self.state_graph = StateGraph(GraphState)
        self.checkpointer = checkpointer or InMemorySaver()

        # Initialize nodes with their dependencies
        self.nodes = {
            "clarification_validation": ClarificationValidationNode(
                clarification_validation_agent
            ),
            "ask_interrupt_questions_for_user_clarification_confirmation": AskInterruptQuestionsNode(),
            "ask_interrupt_questions_for_analytics_inquiry_confirmation": AskInterruptQuestionsNode(),
            "ask_interrupt_questions_for_add_to_cart_confirmation": AskInterruptQuestionsNode(),
            "product_intelligence": ProductIntelligenceAgentNode(
                product_intelligence_agent
            ),
            "product_suggestion": ProductSuggestionAgentNode(product_suggestion_agent),
            "user_confirmation": UserConfirmationNode(user_confirmation_agent),
            "add_to_cart_gateway": AddToCartGatewayNode(),
            "add_to_cart": AddToCartNode(add_to_cart_agent),
            "analytics_query_validation": AnalyticsQueryValidationNode(
                analytics_query_validation_agent
            ),
            "analytics_router": AnalyticsRouterNode(analytics_router_agent),
            "inventory_analytics": InventoryAnalyticsNode(inventory_analytics_agent),
            "product_performance": ProductPerformanceNode(product_performance_agent),
            "sales_analytics": SalesAnalyticsNode(sales_analytics_agent),
            "sales_prediction": SalesPredictionNode(sales_prediction_agent),
            "user_apologise_end": UserApologiseEndNode(),
        }

        logger.info(
            "GraphBuilder initialized with nodes: %s",
            list(self.nodes.keys()),
        )

    def _add_nodes(self) -> None:
        """Add all nodes to the state graph."""
        for node_name, node_instance in self.nodes.items():
            self.state_graph.add_node(node_name, node_instance.execute)
            logger.debug(f"Added node: {node_name}")

    def _add_edges(self) -> None:
        """
        Define edges and transitions between nodes.

        """
        self.state_graph.add_conditional_edges(
            START,
            self._cheack_is_admin,
            {
                True: "analytics_query_validation",
                False: "clarification_validation",
            },
        )

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

        self.state_graph.add_conditional_edges(
            "analytics_query_validation",
            self._should_ask_analytics_inquiry_validation,
            {
                True: "ask_interrupt_questions_for_analytics_inquiry_confirmation",
                False: "analytics_router",
            },
        )

        self.state_graph.add_edge(
            "ask_interrupt_questions_for_analytics_inquiry_confirmation",
            "analytics_query_validation",
        )

        self.state_graph.add_conditional_edges(
            "analytics_router",
            self._check_admin_query,
            {
                AnalyticsRouterAgentEnum.INVENTORY_ANALYSIS: "inventory_analytics",
                AnalyticsRouterAgentEnum.PRODUCT_PERFORMANCE: "product_performance",
                AnalyticsRouterAgentEnum.SALES_ANALYSIS: "sales_analytics",
                AnalyticsRouterAgentEnum.SALES_PREDICTION: "sales_prediction",
            },
        )

        self.state_graph.add_edge("inventory_analytics", END)
        self.state_graph.add_edge("product_performance", END)
        self.state_graph.add_edge("sales_analytics", END)
        self.state_graph.add_edge("sales_prediction", END)

        logger.debug("Graph edges configured")

    def _should_ask_more_questions(self, state: GraphState) -> bool:
        """
        Determine if we need to ask for more information.

        This is a routing function used in conditional edges.

        Args:
            state: Current state of the workflow.

        Returns:
            True if more questions are needed, False otherwise.
        """
        needs_more_questions = not state.get("clarification_validation_completed")
        logger.debug(f"Should ask more questions: {needs_more_questions}")
        return needs_more_questions

    def _should_ask_user_clarification(self, state: GraphState) -> bool:
        """
        Determine if we need to ask for user clarification.

        This is a routing function used in conditional edges.

        Args:
            state: Current state of the workflow.

        Returns:
            True if user clarification is needed, False otherwise.
        """
        needs_user_clarification = not state.get("user_confirmation_completed", False)
        logger.debug(f"Should ask user clarification: {needs_user_clarification}")
        return needs_user_clarification

    def _should_execute_add_to_cart(self, state: GraphState) -> bool:
        """
        Determine if we need to execute add to cart.

        This is a routing function used in conditional edges.

        Args:
            state: Current state of the workflow.

        Returns:
            True if add to cart should be executed, False otherwise.
        """
        should_execute_add_to_cart = state.get("should_execute_add_to_cart", False)
        logger.debug(f"Should execute add to cart: {should_execute_add_to_cart}")
        return should_execute_add_to_cart

    def _should_ask_analytics_inquiry_validation(self, state: GraphState) -> bool:
        """
        Determine if we need to ask for analytics inquiry validation.

        This is a routing function used in conditional edges.

        Args:
            state: Current state of the workflow.

        Returns:
            True if analytics inquiry validation is needed, False otherwise.
        """
        needs_analytics_inquiry_validation = not state.get(
            "analytics_inquiry_validation_completed", False
        )
        logger.debug(
            f"Should ask analytics inquiry validation: {needs_analytics_inquiry_validation}"
        )
        return needs_analytics_inquiry_validation

    def _cheack_is_admin(self, state: GraphState) -> bool:
        """
        Determine if the user is an admin.

        This is a routing function used in conditional edges.

        Args:
            state: Current state of the workflow.

        Returns:
            True if the user is an admin, False otherwise.
        """
        is_admin = state.get("is_admin", False)
        logger.debug(f"Is admin: {is_admin}")
        return is_admin

    def _check_admin_query(self, state: GraphState) -> AnalyticsRouterAgentEnum:
        """
        Determine if the user query is an admin query.

        This is a routing function used in conditional edges.

        Args:
            state: Current state of the workflow.

        Returns:
            True if the user query is an admin query, False otherwise.
        """
        analytics_router_response = state["analytics_router_response"]
        admin_query = analytics_router_response.get("query_type", None)
        logger.debug(f"Is admin query: {admin_query}")
        return admin_query

    def _check_suggest_product_available(self, state: GraphState) -> bool:
        """
        Determine if the suggested product is available.

        This is a routing function used in conditional edges.

        Args:
            state: Current state of the workflow.

        Returns:
            True if the suggested product is available, False otherwise.
        """
        suggest_product_available = state["product_suggestion_response"].get(
            "availability_status", None
        )

        print(f"suggest_product_available: {suggest_product_available}")

        if not suggest_product_available:
            logger.debug("Suggested product availability is not available")
            return False

        if (
            suggest_product_available == ProductRetrievalSuggestionAgentEnum.AVAILABLE
            or suggest_product_available
            == ProductRetrievalSuggestionAgentEnum.ALTERNATIVE_AVAILABLE
        ):
            logger.debug("Suggested product is available")
            return True
        else:
            logger.debug("Suggested product is not available")
            return False

    def build(self) -> StateGraph:
        """
        Build and compile the complete graph.

        This method:
        1. Adds all nodes to the graph
        2. Defines edges and routing logic
        3. Compiles the graph with checkpointing

        Returns:
            The compiled StateGraph ready for execution.
        """
        logger.info("Building graph...")

        self._add_nodes()
        self._add_edges()

        compiled_graph = self.state_graph.compile(checkpointer=self.checkpointer)

        logger.info("Graph built successfully")
        return compiled_graph
