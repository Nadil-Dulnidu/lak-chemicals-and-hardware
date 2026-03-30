from typing import AsyncGenerator
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from app.core.graph.state import GraphState
from app.core.graph.graph_executer import get_compiled_graph
from app.core.observability.langfuse_tracing import langfuse, sanitize_state
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
        flow_type = "resume"
    else:
        # Initial invocation
        initial_state = {
            "messages": [HumanMessage(content=message)],
            "is_admin": is_admin,
            "base_user_query": message,
            "user_id": user_id,
        }
        flow_type = "admin" if is_admin else "customer"

    # Stream using the pluggable adapter!
    # No need to specify stream_mode or graph-specific logic
    # Configure custom data fields to stream alongside messages
    with langfuse.start_as_current_observation(
        name="langgraph_execution",
        as_type="span",
        metadata={
            "flow_type": flow_type,
            "graph": "main_graph",
        },
    ) as trace:
        trace.update(input={"state": sanitize_state(initial_state)})
        try:
            async for event in stream_langgraph_to_vercel(
                graph=graph,
                initial_state=initial_state,
                config=config,
            ):
                yield event
        except Exception as e:
            trace.update(level="ERROR", status_message=str(e))
            raise
