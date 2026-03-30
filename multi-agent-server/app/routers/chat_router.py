from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status, Depends
from app.schemas.vercel_model import VercelChatRequest
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from app.services.streaming_service import stream_chat
from app.configs.logging import get_logger
from vercel_ai_sdk_langraph_python_adapter import (
    extract_user_message,
    patch_vercel_headers,
)
from app.security.jwt import verify_clerk_token, is_admin

logger = get_logger(__name__)

chat_router = APIRouter(
    prefix="/api/v1",
    tags=["Chat"],
)


@chat_router.post("/chat", status_code=status.HTTP_200_OK)
async def chat_endpoint(
    payload: VercelChatRequest,
    token: dict = Depends(verify_clerk_token),
):
    """
    Endpoint for processing user queries using the Vercel AI SDK format.

    Args:
        payload (VercelChatRequest): The request payload containing user messages and thread ID.
        token (_type_, optional): The authentication token. Defaults to Depends(verify_clerk_token).

    Raises:
        HTTPException: If user ID is not found in token.
        HTTPException: If no documents found. Please upload a document before asking questions.
        HTTPException: If file is not a PDF.

    Returns:
        StreamingResponse: A streaming response containing the AI's response to the user query.
    """
    # Extract user ID from token
    user_id = token.get("sub")

    # Check if user ID is present in token
    if not user_id:
        logger.warning(
            "QA request rejected: User ID not found in token",
            extra={"action": "qa_request_unauthorized"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in token",
        )

    # Extract user message
    message = extract_user_message(payload.messages)

    # Delegate to the service layer which runs the multi-agent QA graph
    thread_id = payload.thread_id or payload.id

    is_admin_user = is_admin(token)

    logger.info(
        "QA request received",
        extra={
            "user": user_id,
            "action": "qa_request_start",
            "thread_id": payload.thread_id or payload.id,
        },
    )
    response = StreamingResponse(
        stream_chat(
            message=message,
            thread_id=thread_id,
            user_id=user_id,
            is_admin=is_admin_user,
            resume=payload.resume or False,
        ),
        media_type="text/event-stream",
    )

    return patch_vercel_headers(response)
