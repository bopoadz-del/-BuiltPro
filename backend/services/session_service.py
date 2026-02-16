"""
Long-Session Mode (Smart Context) Service

Manages conversation sessions with capacity tracking for extended
context windows.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import json

from sqlalchemy.orm import Session

from backend.database import ConversationSession


class SessionService:
    """Service for managing conversation sessions."""
    
    DEFAULT_CAPACITY_MAX = 100000  # Default max tokens/context size
    SESSION_TTL_DAYS = 30  # Sessions expire after 30 days
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_session(
        self,
        user_id: int,
        title: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None,
        capacity_max: int = DEFAULT_CAPACITY_MAX,
    ) -> ConversationSession:
        """Create a new conversation session."""
        expires_at = datetime.utcnow() + timedelta(days=self.SESSION_TTL_DAYS)
        
        session = ConversationSession(
            user_id=user_id,
            title=title or f"Session {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            context_data=json.dumps(context_data) if context_data else None,
            capacity_used=0,
            capacity_max=capacity_max,
            is_active=True,
            expires_at=expires_at,
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def get_session(self, session_id: int, user_id: int) -> Optional[ConversationSession]:
        """Get a session by ID, verifying user ownership."""
        return self.db.query(ConversationSession).filter(
            ConversationSession.id == session_id,
            ConversationSession.user_id == user_id,
            ConversationSession.is_active == True,
        ).first()
    
    def list_user_sessions(
        self,
        user_id: int,
        active_only: bool = True,
    ) -> List[ConversationSession]:
        """List all sessions for a user."""
        query = self.db.query(ConversationSession).filter(
            ConversationSession.user_id == user_id
        )
        
        if active_only:
            query = query.filter(ConversationSession.is_active == True)
        
        return query.order_by(ConversationSession.updated_at.desc()).all()
    
    def update_session(
        self,
        session_id: int,
        user_id: int,
        title: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[ConversationSession]:
        """Update session details."""
        session = self.get_session(session_id, user_id)
        if not session:
            return None
        
        if title is not None:
            session.title = title
        
        if context_data is not None:
            session.context_data = json.dumps(context_data)
        
        session.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def update_capacity(
        self,
        session_id: int,
        user_id: int,
        capacity_used: int,
    ) -> Optional[ConversationSession]:
        """Update session capacity usage."""
        session = self.get_session(session_id, user_id)
        if not session:
            return None
        
        session.capacity_used = capacity_used
        session.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def deactivate_session(
        self,
        session_id: int,
        user_id: int,
    ) -> bool:
        """Deactivate (soft delete) a session."""
        session = self.get_session(session_id, user_id)
        if not session:
            return False
        
        session.is_active = False
        session.updated_at = datetime.utcnow()
        self.db.commit()
        return True
    
    def get_capacity_status(self, session_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Get capacity status for a session."""
        session = self.get_session(session_id, user_id)
        if not session:
            return None
        
        return {
            "session_id": session.id,
            "capacity_used": session.capacity_used,
            "capacity_max": session.capacity_max,
            "capacity_remaining": session.capacity_max - session.capacity_used,
            "percent_used": (session.capacity_used / session.capacity_max) * 100,
            "is_full": session.capacity_used >= session.capacity_max,
        }
    
    def add_to_context(
        self,
        session_id: int,
        user_id: int,
        key: str,
        value: Any,
        tokens_used: int = 0,
    ) -> Optional[ConversationSession]:
        """Add data to session context."""
        session = self.get_session(session_id, user_id)
        if not session:
            return None
        
        # Parse existing context
        context = {}
        if session.context_data:
            try:
                context = json.loads(session.context_data)
            except json.JSONDecodeError:
                context = {}
        
        # Add new data
        context[key] = {
            "value": value,
            "added_at": datetime.utcnow().isoformat(),
        }
        
        session.context_data = json.dumps(context)
        session.capacity_used = min(session.capacity_used + tokens_used, session.capacity_max)
        session.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def cleanup_expired_sessions(self) -> int:
        """Deactivate expired sessions. Returns count deactivated."""
        now = datetime.utcnow()
        expired = self.db.query(ConversationSession).filter(
            ConversationSession.is_active == True,
            ConversationSession.expires_at < now,
        ).all()
        
        for session in expired:
            session.is_active = False
        
        self.db.commit()
        return len(expired)
