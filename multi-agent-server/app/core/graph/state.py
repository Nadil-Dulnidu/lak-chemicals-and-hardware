from langgraph.graph import MessagesState


class GraphState(MessagesState):
    """
    State for the graph.
    """

    user_id: str | None = None
    is_admin: bool = False
