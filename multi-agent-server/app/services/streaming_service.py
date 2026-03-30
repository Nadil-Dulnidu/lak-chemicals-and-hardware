from typing import AsyncGenerator
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from app.core.graph.state import GraphState
from app.core.graph.graph_executer import get_compiled_graph
from vercel_ai_sdk_langraph_python_adapter import stream_langgraph_to_vercel


async def stream_chat(
    message: str, thread_id: str, user_id: str, is_admin: bool, resume: bool = False
) -> AsyncGenerator[str, None]:
    """
    Stream the travel system using the pluggable adapter.

    This uses the LangGraphToVercelAdapter which provides:
    - Clean separation between graph logic and streaming
    - Works with any LangGraph graph
    - No hardcoded field checks (requirements, itinerary, bookings)
    - Pluggable message extraction

    Args:
        message: User message or resume input
        thread_id: Thread ID for conversation continuity
        resume: Whether to resume from an interrupt

    Yields:
        SSE-formatted strings following Vercel Data Stream Protocol
    """
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 100}

    # checkpointer = await get_postgres_checkpointer()
    graph = get_compiled_graph()

    if resume:
        # Resume execution with user input
        initial_state = Command(resume=message)
    else:
        # Initial invocation
        initial_state = {
            "messages": [HumanMessage(content=message)],
            "is_admin": is_admin,
            "base_user_query": message,
            "user_id": user_id,
        }

    # Stream using the pluggable adapter!
    # No need to specify stream_mode or graph-specific logic
    # Configure custom data fields to stream alongside messages
    async for event in stream_langgraph_to_vercel(
        graph=graph,
        initial_state=initial_state,
        config=config,
        custom_data_fields=[
            "inventory_analytics_response",
            "product_performance_response",
            "sales_analytics_response",
            "sales_prediction_response",
        ],
    ):
        yield event
