"""Data models for Mia21 SDK."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ChatMessage(BaseModel):
    """A chat message."""
    role: str = Field(..., description="Message role: 'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message content")


class Space(BaseModel):
    """A space configuration."""
    id: str = Field(..., description="Space ID")
    name: str = Field(..., description="Space display name")
    description: str = Field(..., description="Space description")
    type: str = Field(..., description="Space type: 'preset' or 'user'")


class InitializeResponse(BaseModel):
    """Response from initialize_chat."""
    app_id: str
    message: Optional[str] = None
    space_id: Optional[str] = None
    is_new_user: Optional[bool] = None


class ChatResponse(BaseModel):
    """Response from chat."""
    message: str
    app_id: str
    tool_calls: Optional[List[Dict[str, Any]]] = None

