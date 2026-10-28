from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List


class ChatSessionResponse(BaseModel):
    id: int 
    session_active: bool
    started_at: datetime
    ended_at: datetime | None

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: int
    message_sender_role: str
    content: str
    translated_content: Optional[str] = None  # optional for non-English translations
    detected_language: str
    created_at: datetime
    was_translated: bool
    class Config:
        from_attributes = True


class ChatReply(BaseModel):
    chat_session_id: int
    user_message: MessageResponse
    assistant_message: Optional[MessageResponse] = None
    note_ready: bool
    missing_slots: List[str]

    class Config:
        from_attributes = True

class ChatSessionListItem(BaseModel):
    id: int
    session_active: bool
    started_at: datetime
    ended_at: Optional[datetime] = None
    title: str
    last_message: Optional[str] = None
    last_message_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class StartChatSessionRequest(BaseModel):
    content: str

class StartChatSessionResponse(BaseModel):
    chat_session_id: int
    user_message: MessageResponse
    assistant_message: Optional[MessageResponse] = None
    note_ready: bool = False
    missing_slots: List[str] = []

    class Config:
        from_attributes = True