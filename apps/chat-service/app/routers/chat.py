"""
Chat router — handles conversation and message endpoints.

Architecture:
  POST /chat    → ChatService.handle_message() → SSE stream
  GET  /chat    → List conversations (future)
  GET  /chat/:id → Get conversation history (future)

SSE streaming:
  The /chat endpoint returns a Server-Sent Events stream.
  Each token from the LLM is sent as an SSE event, enabling
  real-time streaming in the frontend without WebSocket overhead.

Event publishing:
  After inference completes, the service publishes the full
  inference event to Redis Streams (fire-and-forget). This
  decouples persistence and monitoring from the inference path.
"""

from fastapi import APIRouter

from app.schemas import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter(tags=["chat"])
chat_service = ChatService()


@router.post("/chat", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    Handle an incoming chat message.

    Future: this will return an SSE stream using sse-starlette.
    For now, returns a placeholder response.
    """
    return await chat_service.handle_message(request)


# Future endpoints:
# @router.get("/conversations")
# async def list_conversations(): ...
#
# @router.get("/conversations/{conversation_id}")
# async def get_conversation(conversation_id: str): ...
#
# @router.post("/chat/stream")
# async def stream_message(request: ChatRequest):
#     """SSE streaming endpoint using sse-starlette."""
#     async def event_generator():
#         async for token in chat_service.stream_message(request):
#             yield {"data": token}
#     return EventSourceResponse(event_generator())
