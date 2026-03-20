"""
Thread-safe, singleton-based agent creation and management for the LAK Chemicals
and Hardware multi-agent server.

Currently exposes one agent:
    - sales_analytics_agent  - analyses sales data using the get_sales_report tool
      and returns a SalesAnalyticsAgentResponse structured output.
      Uses the normal GenAI model (gemini-2.5-flash).
"""

import logging
import threading
from typing import Any, Sequence

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy

from app.configs.logging import get_logger
from app.core.llm import get_genai_model, get_genai_reasoning_model
from app.core.agents.prompts import (
    SALES_ANALYTICS_AGENT_PROMPT,
    ANALYTICS_ROUTER_AGENT_PROMPT,
    SALES_PREDICTION_AGENT_PROMPT,
    INVENTORY_ANALYTICS_AGENT_PROMPT,
    PRODUCT_PERFORMANCE_AGENT_PROMPT,
)
from app.core.agents.schemas import (
    SalesAnalyticsAgentResponse,
    AnalyticsRouterAgentResponse,
    SalesPredictionAgentResponse,
    InventoryAnalyticsAgentResponse,
    ProductPerformanceAgentResponse,
)
from app.exceptions.agents_exceptions import (
    AgentConfigurationError,
    AgentInitializationError,
)
from app.core.agents.tools import (
    get_sales_report,
    get_inventory_report,
    get_product_performance_report,
)

logger = get_logger(__name__)


class Agent:
    """
    Wraps a LangChain chat model into a LangGraph agent via create_agent.

    The resulting runnable can be used directly as a LangGraph node.

    Raises:
        AgentConfigurationError: If required constructor arguments are missing.
        AgentInitializationError: If the underlying agent cannot be built.
    """

    def __init__(
        self,
        model: BaseChatModel,
        name: str,
        tools: Sequence[BaseTool | Any] | None = None,
        prompt: str | None = None,
        response_format: type | None = None,
    ) -> None:
        self._validate_config(model, name, response_format)

        self.name = name
        self.model = model
        self.tools: list = list(tools or [])
        self.prompt = prompt or ""
        self.response_format = response_format

        logger.info(
            "Agent '%s' initialised with %d tool(s).", self.name, len(self.tools)
        )

    @staticmethod
    def _validate_config(
        model: BaseChatModel | None,
        name: str | None,
        response_format: type | None,
    ) -> None:
        """Validate that all required constructor arguments are present."""
        if not model:
            raise AgentConfigurationError("'model' is required to create an Agent.")
        if not name:
            raise AgentConfigurationError("'name' is required to create an Agent.")
        if response_format is None:
            raise AgentConfigurationError(
                "'response_format' is required to create an Agent."
            )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def create_agent(self):
        """
        Build and return a LangGraph agent using create_agent.

        Returns:
            Compiled LangGraph agent (CompiledGraph).

        Raises:
            AgentInitializationError: If agent creation fails.
        """
        try:
            logger.info(f"Creating agent '{self.name}'")
            agent = create_agent(
                model=self.model,
                tools=self.tools,
                response_format=ToolStrategy(self.response_format),
                system_prompt=self.prompt,
                name=self.name,
            )
            logger.info(f"Agent '{self.name}' created successfully")
            return agent
        except Exception as e:
            logger.error(f"Failed to create agent '{self.name}': {str(e)}")
            raise AgentInitializationError(
                f"Failed to create agent '{self.name}': {str(e)}"
            ) from e


class AgentManager:
    """
    Thread-safe singleton that lazily creates and caches all agent instances.

    Two LLMs are supported:
        - GenAI normal   (gemini-2.5-flash)   → used for sales_analytics_agent
        - GenAI reasoning (gemini-2.5-pro)    → reserved for future agents

    Usage:
        manager = AgentManager()
        agent   = manager.get_sales_analytics_agent()
    """

    _instance = None
    _lock = threading.RLock()

    def __new__(cls) -> "AgentManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        with self._lock:
            if not self._initialized:
                # Cached agent instances
                self._sales_analytics_agent = None
                self._analytics_router_agent = None
                self._sales_prediction_agent = None
                self._inventory_analytics_agent = None
                self._product_performance_agent = None

                # Cached model instances
                self._genai_model = None
                self._genai_reasoning_model = None

                self._initialized = True
                logger.info("AgentManager initialised.")

    def _get_genai_model(self) -> BaseChatModel:
        """Lazy-load the normal GenAI model (gemini-2.5-flash)."""
        if self._genai_model is None:
            with self._lock:
                if self._genai_model is None:
                    try:
                        logger.info("Initialising GenAI normal model.")
                        self._genai_model = get_genai_model(streaming=False)
                        logger.info("GenAI normal model initialised successfully.")
                    except Exception as exc:
                        logger.error("Failed to initialise GenAI normal model: %s", exc)
                        raise AgentInitializationError(
                            f"Failed to initialise GenAI normal model: {exc}"
                        ) from exc
        return self._genai_model

    def _get_genai_reasoning_model(self) -> BaseChatModel:
        """Lazy-load the GenAI reasoning model (gemini-2.5-pro)."""
        if self._genai_reasoning_model is None:
            with self._lock:
                if self._genai_reasoning_model is None:
                    try:
                        logger.info("Initialising GenAI reasoning model.")
                        self._genai_reasoning_model = get_genai_reasoning_model(
                            streaming=False
                        )
                        logger.info("GenAI reasoning model initialised successfully.")
                    except Exception as exc:
                        logger.error(
                            "Failed to initialise GenAI reasoning model: %s", exc
                        )
                        raise AgentInitializationError(
                            f"Failed to initialise GenAI reasoning model: {exc}"
                        ) from exc
        return self._genai_reasoning_model

    def get_sales_analytics_agent(self):
        """
        Get (or lazily create) the sales analytics agent singleton.

        Uses the normal GenAI model and the get_sales_report tool.
        Returns a SalesAnalyticsAgentResponse as structured output.

        Returns:
            Compiled LangGraph agent (CompiledGraph).

        Raises:
            AgentInitializationError: If agent creation fails.
        """
        if self._sales_analytics_agent is None:
            with self._lock:
                if self._sales_analytics_agent is None:
                    try:
                        logger.info("Creating sales analytics agent.")
                        self._sales_analytics_agent = Agent(
                            model=self._get_genai_reasoning_model(),
                            name="sales_analytics_agent",
                            tools=[get_sales_report],
                            prompt=SALES_ANALYTICS_AGENT_PROMPT,
                            response_format=SalesAnalyticsAgentResponse,
                        ).create_agent()
                        logger.info("Sales analytics agent created successfully.")
                    except Exception as exc:
                        logger.error("Failed to create sales analytics agent: %s", exc)
                        raise
        return self._sales_analytics_agent

    def get_analytics_router_agent(self):
        """
        Get (or lazily create) the analytics router agent singleton.

        Uses the reasoning GenAI model and the route_analytics_query tool.
        Returns an AnalyticsRouterAgentResponse as structured output.

        Returns:
            Compiled LangGraph agent (CompiledGraph).

        Raises:
            AgentInitializationError: If agent creation fails.
        """
        if self._analytics_router_agent is None:
            with self._lock:
                if self._analytics_router_agent is None:
                    try:
                        logger.info("Creating analytics router agent.")
                        self._analytics_router_agent = Agent(
                            model=self._get_genai_model(),
                            name="analytics_router_agent",
                            tools=[get_sales_report],
                            prompt=ANALYTICS_ROUTER_AGENT_PROMPT,
                            response_format=AnalyticsRouterAgentResponse,
                        ).create_agent()
                        logger.info("Analytics router agent created successfully.")
                    except Exception as exc:
                        logger.error("Failed to create analytics router agent: %s", exc)
                        raise
        return self._analytics_router_agent

    def get_sales_prediction_agent(self):
        """
        Get (or lazily create) the sales prediction agent singleton.

        Uses the reasoning GenAI model and the route_analytics_query tool.
        Returns an AnalyticsRouterAgentResponse as structured output.

        Returns:
            Compiled LangGraph agent (CompiledGraph).

        Raises:
            AgentInitializationError: If agent creation fails.
        """
        if self._sales_prediction_agent is None:
            with self._lock:
                if self._sales_prediction_agent is None:
                    try:
                        logger.info("Creating sales prediction agent.")
                        self._sales_prediction_agent = Agent(
                            model=self._get_genai_reasoning_model(),
                            name="sales_prediction_agent",
                            tools=[get_sales_report],
                            prompt=SALES_PREDICTION_AGENT_PROMPT,
                            response_format=SalesPredictionAgentResponse,
                        ).create_agent()
                        logger.info("Sales prediction agent created successfully.")
                    except Exception as exc:
                        logger.error("Failed to create sales prediction agent: %s", exc)
                        raise

        return self._sales_prediction_agent

    def get_inventory_analytics_agent(self):
        """
        Get (or lazily create) the inventory analytics agent singleton.

        Uses the reasoning GenAI model and the route_analytics_query tool.
        Returns an AnalyticsRouterAgentResponse as structured output.

        Returns:
            Compiled LangGraph agent (CompiledGraph).

        Raises:
            AgentInitializationError: If agent creation fails.
        """
        if self._inventory_analytics_agent is None:
            with self._lock:
                if self._inventory_analytics_agent is None:
                    try:
                        logger.info("Creating inventory analytics agent.")
                        self._inventory_analytics_agent = Agent(
                            model=self._get_genai_reasoning_model(),
                            name="inventory_analytics_agent",
                            tools=[get_inventory_report],
                            prompt=INVENTORY_ANALYTICS_AGENT_PROMPT,
                            response_format=InventoryAnalyticsAgentResponse,
                        ).create_agent()
                        logger.info("Inventory analytics agent created successfully.")
                    except Exception as exc:
                        logger.error(
                            "Failed to create inventory analytics agent: %s", exc
                        )
                        raise

        return self._inventory_analytics_agent

    def get_product_performance_agent(self):
        """
        Get (or lazily create) the product performance agent singleton.

        Uses the reasoning GenAI model and the route_analytics_query tool.
        Returns an AnalyticsRouterAgentResponse as structured output.

        Returns:
            Compiled LangGraph agent (CompiledGraph).

        Raises:
            AgentInitializationError: If agent creation fails.
        """
        if self._product_performance_agent is None:
            with self._lock:
                if self._product_performance_agent is None:
                    try:
                        logger.info("Creating product performance agent.")
                        self._product_performance_agent = Agent(
                            model=self._get_genai_reasoning_model(),
                            name="product_performance_agent",
                            tools=[get_product_performance_report],
                            prompt=PRODUCT_PERFORMANCE_AGENT_PROMPT,
                            response_format=ProductPerformanceAgentResponse,
                        ).create_agent()
                        logger.info("Product performance agent created successfully.")
                    except Exception as exc:
                        logger.error(
                            "Failed to create product performance agent: %s", exc
                        )
                        raise

        return self._product_performance_agent

    def reset(self) -> None:
        """
        Discard all cached agents and models so they are recreated on next access.
        Useful for testing or after a configuration change.
        """
        with self._lock:
            logger.warning("AgentManager: resetting all agents and models.")
            self._sales_analytics_agent = None
            self._genai_model = None
            self._genai_reasoning_model = None
            logger.info("AgentManager: reset complete.")


_manager = AgentManager()


def get_sales_analytics_agent():
    """
    Return the sales analytics agent singleton.

    The agent accepts a user message and returns a SalesAnalyticsAgentResponse.

    Example::

        from langchain_core.messages import HumanMessage
        agent = get_sales_analytics_agent()
        result = agent.invoke(
            {"messages": [HumanMessage(content="Show me sales for March 2026")]}
        )

    Returns:
        Compiled LangGraph agent (CompiledGraph).

    Raises:
        AgentInitializationError: If the agent cannot be created.
    """
    return _manager.get_sales_analytics_agent()


def get_analytics_router_agent():
    """
    Return the analytics router agent singleton.

    The agent accepts a user message and returns an AnalyticsRouterAgentResponse.

    Example::

        from langchain_core.messages import HumanMessage
        agent = get_analytics_router_agent()
        result = agent.invoke(
            {"messages": [HumanMessage(content="Show me sales for March 2026")]}
        )

    Returns:
        Compiled LangGraph agent (CompiledGraph).

    Raises:
        AgentInitializationError: If the agent cannot be created.
    """
    return _manager.get_analytics_router_agent()


def get_sales_prediction_agent():
    """
    Return the sales prediction agent singleton.

    The agent accepts a user message and returns a SalesPredictionAgentResponse.

    Example::

        from langchain_core.messages import HumanMessage
        agent = get_sales_prediction_agent()
        result = agent.invoke(
            {"messages": [HumanMessage(content="Predict sales for next month")]}
        )

    Returns:
        Compiled LangGraph agent (CompiledGraph).

    Raises:
        AgentInitializationError: If the agent cannot be created.
    """
    return _manager.get_sales_prediction_agent()


def get_inventory_analytics_agent():
    """
    Return the inventory analytics agent singleton.

    The agent accepts a user message and returns an InventoryAnalyticsAgentResponse.

    Example::

        from langchain_core.messages import HumanMessage
        agent = get_inventory_analytics_agent()
        result = agent.invoke(
            {"messages": [HumanMessage(content="Show me inventory for March 2026")]}
        )

    Returns:
        Compiled LangGraph agent (CompiledGraph).

    Raises:
        AgentInitializationError: If the agent cannot be created.
    """
    return _manager.get_inventory_analytics_agent()


def get_product_performance_agent():
    """
    Return the product performance agent singleton.

    The agent accepts a user message and returns a ProductPerformanceAgentResponse.

    Example::

        from langchain_core.messages import HumanMessage
        agent = get_product_performance_agent()
        result = agent.invoke(
            {"messages": [HumanMessage(content="Show me product performance for March 2026")]}
        )

    Returns:
        Compiled LangGraph agent (CompiledGraph).

    Raises:
        AgentInitializationError: If the agent cannot be created.
    """
    return _manager.get_product_performance_agent()


def reset_agents() -> None:
    """
    Reset all cached agents and models.
    Forces recreation on next access – useful for testing.
    """
    _manager.reset()


if __name__ == "__main__":
    from langchain_core.messages import HumanMessage

    # agent = get_sales_analytics_agent()
    # result = agent.invoke(
    #     {"messages": [HumanMessage(content="Show me sales for March 2026")]}
    # )
    # print(result)

    # agent = get_analytics_router_agent()
    # result = agent.invoke(
    #     {
    #         "messages": [
    #             HumanMessage(
    #                 content="Based on the sales data for March 2026, predict the sales for April 2026"
    #             )
    #         ]
    #     }
    # )
    # print(result)

    # agent = get_sales_prediction_agent()
    # result = agent.invoke(
    #     {
    #         "messages": [
    #             HumanMessage(
    #                 content="Based on the sales data for March 2026, predict the sales for April 2026"
    #             )
    #         ]
    #     }
    # )
    # print(result)

    agent = get_inventory_analytics_agent()
    result = agent.invoke(
        {"messages": [HumanMessage(content="Show me inventory for March 2026")]}
    )
    print(result)
