from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

from app.api.conversations import repo  # reusing the same memory repo instance
from app.schemas.chat import StreamChatRequest
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])

def get_chat_service() -> ChatService:
    return ChatService(repo)

@router.post("/stream")
async def stream_chat(
    request: StreamChatRequest,
    service: ChatService = Depends(get_chat_service)
):
    """
    Stream an LLM response for a given chat message.
    
    Returns Server-Sent Events (SSE).
    """
    generator = service.stream_message(request)
    return EventSourceResponse(generator)

@router.post("/cancel/{conversation_id}")
async def cancel_stream(
    conversation_id: str,
    service: ChatService = Depends(get_chat_service)
):
    """Cancel an active stream for a conversation."""
    cancelled = service.cancel_stream(conversation_id)
    return {"status": "success", "cancelled": cancelled}
