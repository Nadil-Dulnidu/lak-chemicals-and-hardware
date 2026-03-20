from langchain_community.tools import DuckDuckGoSearchRun
from langchain.tools import tool
from app.configs.logging import get_logger

logger = get_logger(__name__)


@tool(name_or_callable="web_search_tool")
def web_search_tool(query: str) -> DuckDuckGoSearchRun:
    """Search the web for general knowledge, how-to guides, and best practices related to hardware tasks."""
    logger.info(f"Web search tool called with query: {query}")
    web_search = DuckDuckGoSearchRun(
        name="web_search",
        description=(
            "Search the web for general knowledge, how-to guides, and best practices related to hardware tasks. "
            "Use this tool to understand real-world solutions, required tools, materials, and safety considerations. "
            "Do NOT use this tool to find specific store products. "
            "Use it only to gather contextual knowledge to improve reasoning and recommendations."
        ),
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query describing the hardware task or problem (e.g., 'how to install shelves on concrete wall').",
                }
            },
            "required": ["query"],
        },
    )
    return web_search
