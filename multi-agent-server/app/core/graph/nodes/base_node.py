"""
Base node class for LangGraph nodes.

This module provides an abstract base class that all graph nodes should inherit from.
It ensures a consistent interface and allows for shared functionality across all nodes.
"""

from app.configs.logging import get_logger
from abc import ABC, abstractmethod
from typing import Any, Dict

from app.core.graph.state import GraphState


class BaseNode(ABC):
    """
    Abstract base class for all graph nodes.

    This class provides a common interface for all nodes in the interview coach graph.
    Each node should implement the execute method to define its specific behavior.

    Attributes:
        logger (logging.Logger): Logger instance for this node.
        node_name (str): Name of the node for logging purposes.
    """

    def __init__(self, node_name: str):
        """
        Initialize the base node.

        Args:
            node_name: Name of the node for identification and logging.
        """
        self.node_name = node_name
        self.logger = get_logger(f"{__name__}.{node_name}")

    @abstractmethod
    def execute(self, state: GraphState) -> GraphState:
        """
        Execute the node's logic.

        This method must be implemented by all concrete node classes.
        It defines the core business logic for the node.

        Args:
            state: The current state of the interview coach workflow.

        Returns:
            The updated state after executing the node's logic.

        Raises:
            NotImplementedError: If the subclass doesn't implement this method.
        """
        raise NotImplementedError("Subclasses must implement the execute method")

    def _log_start(self) -> None:
        """Log the start of node execution."""
        self.logger.info(f"[{self.node_name.upper()}] Node started")

    def _log_end(self, additional_info: str = "") -> None:
        """
        Log the end of node execution.

        Args:
            additional_info: Optional additional information to include in the log.
        """
        message = f"[{self.node_name.upper()}] Node ended"
        if additional_info:
            message += f" - {additional_info}"
        self.logger.info(message)

    def _log_error(self, error: Exception) -> None:
        """
        Log an error that occurred during node execution.

        Args:
            error: The exception that was raised.
        """
        self.logger.error(
            f"[{self.node_name.upper()}] Error in node: {error}", exc_info=True
        )

    def _create_safe_error_state(
        self,
        state: GraphState,
        error_message: str = "Sorry, I encountered an error. Could you try again?",
    ) -> Dict[str, Any]:
        """
        Create a safe error state when something goes wrong.

        Args:
            state: The current state.
            error_message: The error message to show to the user.

        Returns:
            A safe state dictionary with error handling.
        """
        return {
            "messages": state.get("messages", []),
            "requirements": None,
            "requirements_completed": False,
            "intruption_question": error_message,
        }
