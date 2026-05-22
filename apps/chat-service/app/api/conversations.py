
from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_conversation_repository
from app.schemas.conversation import ConversationSchema, CreateConversationRequest
from app.services.conversation_service import ConversationService
from app.repositories.base import ConversationRepository

def get_conversation_service(repo: ConversationRepository = Depends(get_conversation_repository)) -> ConversationService:
    return ConversationService(repo)

router = APIRouter(prefix="/conversations", tags=["conversations"])

@router.post("", response_model=ConversationSchema)
async def create_conversation(
    request: CreateConversationRequest,
    service: ConversationService = Depends(get_conversation_service)
):
    """Create a new conversation."""
    return await service.create(title=request.title)

@router.get("", response_model=list[ConversationSchema])
async def list_conversations(
    service: ConversationService = Depends(get_conversation_service)
):
    """List all conversations."""
    return await service.get_all()

@router.get("/{conversation_id}", response_model=ConversationSchema)
async def get_conversation(
    conversation_id: str,
    service: ConversationService = Depends(get_conversation_service)
):
    """Get a specific conversation by ID."""
    conversation = await service.get_by_id(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation

@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    service: ConversationService = Depends(get_conversation_service)
):
    """Delete a conversation."""
    deleted = await service.delete(conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "success"}
