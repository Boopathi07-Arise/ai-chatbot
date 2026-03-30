from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ── Request Schemas ──────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    model: str = "gemini"  # Default model: "gemini", "gpt", or "claude"


class ConversationRenameRequest(BaseModel):
    title: str


# ── Response Schemas ─────────────────────────────────────────────
class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationDetailResponse(ConversationResponse):
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    response: str
    conversation_id: str


class ErrorResponse(BaseModel):
    error: str
