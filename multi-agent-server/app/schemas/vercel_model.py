from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class VercelChatRequest(BaseModel):
    """
    Vercel AI SDK request format.
    Accepts the standard UI messages format and transforms internally.
    """

    id: str  # Conversation ID from frontend
    messages: List[Dict[str, Any]]  # UI messages array
    trigger: str  # "submit-message" or other triggers
    thread_id: Optional[str] = None  # Optional override for thread_id
    resume: Optional[bool] = False
    user_name: Optional[str] = None
