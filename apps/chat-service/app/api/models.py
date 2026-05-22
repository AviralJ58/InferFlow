"""
Model registry API endpoints.
"""

from fastapi import APIRouter
from typing import List
from pydantic import BaseModel

router = APIRouter(prefix="/models", tags=["Models"])

class ModelSchema(BaseModel):
    id: str
    provider: str
    name: str

# In a production app, this could be fetched from a database or config.
SUPPORTED_MODELS = [
    {"id": "gemini-2.5-flash", "provider": "gemini", "name": "Gemini 2.5 Flash"},
    {"id": "gpt-5-mini", "provider": "openai", "name": "GPT-5 Mini"}
]

@router.get("", response_model=List[ModelSchema])
async def list_models():
    """Get the list of supported LLMs."""
    return SUPPORTED_MODELS
