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
            "ask_interrupt_questions": AskInterruptQuestionsNode(),
            "product_intelligence": ProductIntelligenceAgentNode(
                product_intelligence_agent
            ),
            "product_suggestion": ProductSuggestionAgentNode(product_suggestion_agent),
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
        self.state_graph.add_edge(START, "clarification_validation")

        self.state_graph.add_conditional_edges(
            "clarification_validation",
            self._should_ask_more_questions,
            {
                True: "ask_interrupt_questions",
                False: "product_intelligence",
            },
        )

        self.state_graph.add_edge("ask_interrupt_questions", "clarification_validation")

        self.state_graph.add_edge("product_intelligence", "product_suggestion")

        self.state_graph.add_edge("product_suggestion", END)

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
        needs_more_questions = not state.get(
            "clarification_validation_completed", False
        )
        logger.debug(f"Should ask more questions: {needs_more_questions}")
        return needs_more_questions

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
