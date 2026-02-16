"""
Long-Session Mode (Smart Context) API Endpoints

Provides full CRUD for conversation sessions with capacity tracking.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status

from backend.db import get_db
from backend.models.auth import User
from backend.core.security import get_current_user
from backend.services.session_service import SessionService

router = APIRouter(prefix="/sessions", tags=["sessions-v1"])


# Schemas
class SessionCreate(BaseModel):
    title: Optional[str] = None
    context_data: Optional[Dict[str, Any]] = None
    capacity_max: int = 100000


class SessionUpdate(BaseModel):
    title: Optional[str] = None
    context_data: Optional[Dict[str, Any]] = None


class ContextAdd(BaseModel):
    key: str
    value: Any
    tokens_used: int = 0


class SessionResponse(BaseModel):
    id: int
    user_id: int
    title: str
    capacity_used: int
    capacity_max: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    expires_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class SessionDetailResponse(SessionResponse):
    context_data: Optional[Dict[str, Any]]


class CapacityStatus(BaseModel):
    session_id: int
    capacity_used: int
    capacity_max: int
    capacity_remaining: int
    percent_used: float
    is_full: bool


@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(
    payload: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new conversation session."""
    service = SessionService(db)
    session = service.create_session(
        user_id=current_user.id,
        title=payload.title,
        context_data=payload.context_data,
        capacity_max=payload.capacity_max,
    )
    return session


@router.get("", response_model=List[SessionResponse])
async def list_sessions(
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all sessions for the current user."""
    service = SessionService(db)
    sessions = service.list_user_sessions(current_user.id, active_only=active_only)
    return sessions


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific session with full details."""
    service = SessionService(db)
    session = service.get_session(session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: int,
    payload: SessionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update session details."""
    service = SessionService(db)
    session = service.update_session(
        session_id=session_id,
        user_id=current_user.id,
        title=payload.title,
        context_data=payload.context_data,
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/{session_id}")
async def deactivate_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Deactivate a session."""
    service = SessionService(db)
    success = service.deactivate_session(session_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session deactivated"}


@router.get("/{session_id}/capacity", response_model=CapacityStatus)
async def get_capacity(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get capacity status for a session."""
    service = SessionService(db)
    status = service.get_capacity_status(session_id, current_user.id)
    if not status:
        raise HTTPException(status_code=404, detail="Session not found")
    return status


@router.post("/{session_id}/context")
async def add_to_context(
    session_id: int,
    payload: ContextAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add data to session context."""
    service = SessionService(db)
    session = service.add_to_context(
        session_id=session_id,
        user_id=current_user.id,
        key=payload.key,
        value=payload.value,
        tokens_used=payload.tokens_used,
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Context updated", "session_id": session.id}


@router.post("/{session_id}/toggle")
async def toggle_session_active(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Toggle session active status."""
    service = SessionService(db)
    session = service.get_session(session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Toggle status
    if session.is_active:
        service.deactivate_session(session_id, current_user.id)
        return {"message": "Session deactivated", "is_active": False}
    else:
        session.is_active = True
        db.commit()
        return {"message": "Session activated", "is_active": True}


@router.post("/cleanup")
async def cleanup_expired(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Clean up expired sessions (admin only in production)."""
    # TODO: Add admin check
    service = SessionService(db)
    count = service.cleanup_expired_sessions()
    return {"message": f"Cleaned up {count} expired sessions", "count": count}
