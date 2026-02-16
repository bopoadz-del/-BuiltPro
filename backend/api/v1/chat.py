"""
Chat API v1 endpoint

Full implementation for conversation management and messaging.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status

from backend.db import get_db
from backend.models.auth import User
from backend.core.security import get_current_user

router = APIRouter(prefix="/chat", tags=["chat-v1"])


# Schemas
class MessageCreate(BaseModel):
    content: str
    conversation_id: Optional[int] = None


class MessageResponse(BaseModel):
    id: int
    content: str
    role: str
    created_at: datetime
    conversation_id: int
    
    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    title: Optional[str] = None
    project_id: Optional[int] = None


class ConversationResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    project_id: Optional[int] = None
    message_count: int = 0
    
    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None
    context: Optional[dict] = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: int
    message_id: int


# In-memory storage for demo (replace with database models in production)
_conversations = {}
_messages = {}
_message_id = 0
_conversation_id = 0


def _get_next_conversation_id() -> int:
    global _conversation_id
    _conversation_id += 1
    return _conversation_id


def _get_next_message_id() -> int:
    global _message_id
    _message_id += 1
    return _message_id


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    payload: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new conversation."""
    conv_id = _get_next_conversation_id()
    now = datetime.utcnow()
    conversation = {
        "id": conv_id,
        "title": payload.title or f"Conversation {conv_id}",
        "created_at": now,
        "updated_at": now,
        "project_id": payload.project_id,
        "user_id": current_user.id,
        "message_count": 0,
    }
    _conversations[conv_id] = conversation
    return ConversationResponse(**conversation)


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all conversations for the current user."""
    user_conversations = [
        ConversationResponse(**conv) 
        for conv in _conversations.values() 
        if conv.get("user_id") == current_user.id
    ]
    return sorted(user_conversations, key=lambda x: x.updated_at, reverse=True)


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific conversation."""
    conv = _conversations.get(conversation_id)
    if not conv or conv.get("user_id") != current_user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationResponse(**conv)


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a conversation and its messages."""
    conv = _conversations.get(conversation_id)
    if not conv or conv.get("user_id") != current_user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Delete associated messages
    messages_to_delete = [
        msg_id for msg_id, msg in _messages.items() 
        if msg.get("conversation_id") == conversation_id
    ]
    for msg_id in messages_to_delete:
        del _messages[msg_id]
    
    del _conversations[conversation_id]
    return {"message": "Conversation deleted"}


@router.post("/messages", response_model=MessageResponse)
async def create_message(
    payload: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new message in a conversation."""
    if payload.conversation_id:
        conv = _conversations.get(payload.conversation_id)
        if not conv or conv.get("user_id") != current_user.id:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        # Create new conversation if none provided
        conv_response = await create_conversation(
            ConversationCreate(), current_user, db
        )
        payload.conversation_id = conv_response.id
        conv = _conversations[payload.conversation_id]
    
    msg_id = _get_next_message_id()
    now = datetime.utcnow()
    message = {
        "id": msg_id,
        "content": payload.content,
        "role": "user",
        "created_at": now,
        "conversation_id": payload.conversation_id,
        "user_id": current_user.id,
    }
    _messages[msg_id] = message
    
    # Update conversation
    conv["updated_at"] = now
    conv["message_count"] = conv.get("message_count", 0) + 1
    
    return MessageResponse(**message)


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all messages in a conversation."""
    conv = _conversations.get(conversation_id)
    if not conv or conv.get("user_id") != current_user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    messages = [
        MessageResponse(**msg) 
        for msg in _messages.values() 
        if msg.get("conversation_id") == conversation_id
    ]
    return sorted(messages, key=lambda x: x.created_at)


@router.post("/send", response_model=ChatResponse)
async def send_chat_message(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message and get AI response."""
    # Create or use existing conversation
    if payload.conversation_id:
        conv = _conversations.get(payload.conversation_id)
        if not conv or conv.get("user_id") != current_user.id:
            raise HTTPException(status_code=404, detail="Conversation not found")
        conv_id = payload.conversation_id
    else:
        conv_response = await create_conversation(
            ConversationCreate(), current_user, db
        )
        conv_id = conv_response.id
        conv = _conversations[conv_id]
    
    # Store user message
    user_msg_id = _get_next_message_id()
    now = datetime.utcnow()
    _messages[user_msg_id] = {
        "id": user_msg_id,
        "content": payload.message,
        "role": "user",
        "created_at": now,
        "conversation_id": conv_id,
        "user_id": current_user.id,
    }
    
    # Generate AI response (placeholder for actual AI integration)
    ai_response = _generate_ai_response(payload.message, payload.context)
    ai_msg_id = _get_next_message_id()
    _messages[ai_msg_id] = {
        "id": ai_msg_id,
        "content": ai_response,
        "role": "assistant",
        "created_at": datetime.utcnow(),
        "conversation_id": conv_id,
        "user_id": None,
    }
    
    # Update conversation
    conv["updated_at"] = datetime.utcnow()
    conv["message_count"] = conv.get("message_count", 0) + 2
    
    return ChatResponse(
        response=ai_response,
        conversation_id=conv_id,
        message_id=ai_msg_id,
    )


def _generate_ai_response(message: str, context: Optional[dict]) -> str:
    """Generate AI response (placeholder for actual AI integration)."""
    # This is a placeholder - in production, this would call OpenAI or similar
    responses = [
        f"I understand you're asking about: {message[:50]}...",
        "That's an interesting question. Let me help you with that.",
        "I can assist you with that. Here's what I found:",
        "Based on your query, here are my thoughts:",
    ]
    import random
    return random.choice(responses) + "\n\n(This is a demo response - integrate with OpenAI for real responses)"
