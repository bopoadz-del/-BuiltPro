"""
Auditor API v1 endpoint

Full implementation for audit logging and compliance monitoring.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status, Query

from backend.db import get_db
from backend.models.auth import User
from backend.core.security import get_current_user

router = APIRouter(prefix="/auditor", tags=["auditor-v1"])


# Enums
class AuditLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditCategory(str, Enum):
    AUTH = "authentication"
    DATA = "data_access"
    SYSTEM = "system"
    SECURITY = "security"
    COMPLIANCE = "compliance"
    USER = "user_action"


# Schemas
class AuditLogCreate(BaseModel):
    action: str
    level: AuditLevel = AuditLevel.INFO
    category: AuditCategory = AuditCategory.USER
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class AuditLogResponse(BaseModel):
    id: int
    timestamp: datetime
    user_id: Optional[int]
    username: Optional[str]
    action: str
    level: str
    category: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    details: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    
    class Config:
        from_attributes = True


class AuditStats(BaseModel):
    total_logs: int
    by_level: Dict[str, int]
    by_category: Dict[str, int]
    recent_errors: int
    period_hours: int


class ComplianceCheck(BaseModel):
    check_name: str
    status: str  # pass, fail, warning
    description: str
    last_checked: datetime
    details: Optional[Dict[str, Any]] = None


# In-memory storage (replace with database in production)
_audit_logs = {}
_log_id = 0


def _get_next_log_id() -> int:
    global _log_id
    _log_id += 1
    return _log_id


def _create_audit_log(
    action: str,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    level: AuditLevel = AuditLevel.INFO,
    category: AuditCategory = AuditCategory.USER,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AuditLogResponse:
    """Internal function to create audit log entry."""
    global _log_id
    _log_id += 1
    
    log_entry = {
        "id": _log_id,
        "timestamp": datetime.utcnow(),
        "user_id": user_id,
        "username": username,
        "action": action,
        "level": level.value,
        "category": category.value,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "details": details or {},
        "ip_address": ip_address,
    }
    _audit_logs[_log_id] = log_entry
    return AuditLogResponse(**log_entry)


@router.post("/logs", response_model=AuditLogResponse, status_code=201)
async def create_audit_log(
    payload: AuditLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new audit log entry."""
    return _create_audit_log(
        action=payload.action,
        user_id=current_user.id,
        username=getattr(current_user, 'username', None),
        level=payload.level,
        category=payload.category,
        resource_type=payload.resource_type,
        resource_id=payload.resource_id,
        details=payload.details,
        ip_address=payload.ip_address,
        user_agent=payload.user_agent,
    )


@router.get("/logs", response_model=List[AuditLogResponse])
async def list_audit_logs(
    level: Optional[AuditLevel] = None,
    category: Optional[AuditCategory] = None,
    user_id: Optional[int] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    search: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Query audit logs with filtering and pagination."""
    logs = list(_audit_logs.values())
    
    # Apply filters
    if level:
        logs = [l for l in logs if l.get("level") == level.value]
    if category:
        logs = [l for l in logs if l.get("category") == category.value]
    if user_id:
        logs = [l for l in logs if l.get("user_id") == user_id]
    if resource_type:
        logs = [l for l in logs if l.get("resource_type") == resource_type]
    if resource_id:
        logs = [l for l in logs if l.get("resource_id") == resource_id]
    if start_date:
        logs = [l for l in logs if l.get("timestamp") >= start_date]
    if end_date:
        logs = [l for l in logs if l.get("timestamp") <= end_date]
    if search:
        search_lower = search.lower()
        logs = [
            l for l in logs 
            if search_lower in l.get("action", "").lower()
            or search_lower in str(l.get("details", "")).lower()
        ]
    
    # Sort by timestamp descending
    logs.sort(key=lambda x: x.get("timestamp", datetime.min), reverse=True)
    
    # Apply pagination
    total = len(logs)
    logs = logs[offset:offset + limit]
    
    return [AuditLogResponse(**log) for log in logs]


@router.get("/logs/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific audit log entry."""
    log = _audit_logs.get(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    return AuditLogResponse(**log)


@router.get("/stats", response_model=AuditStats)
async def get_audit_stats(
    period_hours: int = Query(24, ge=1, le=720),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get audit log statistics for a time period."""
    cutoff = datetime.utcnow() - timedelta(hours=period_hours)
    
    recent_logs = [l for l in _audit_logs.values() if l.get("timestamp", datetime.min) >= cutoff]
    
    by_level = {}
    by_category = {}
    recent_errors = 0
    
    for log in recent_logs:
        level = log.get("level", "unknown")
        category = log.get("category", "unknown")
        
        by_level[level] = by_level.get(level, 0) + 1
        by_category[category] = by_category.get(category, 0) + 1
        
        if level in ["error", "critical"]:
            recent_errors += 1
    
    return AuditStats(
        total_logs=len(recent_logs),
        by_level=by_level,
        by_category=by_category,
        recent_errors=recent_errors,
        period_hours=period_hours,
    )


@router.get("/compliance/checks", response_model=List[ComplianceCheck])
async def run_compliance_checks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Run compliance checks and return results."""
    now = datetime.utcnow()
    checks = []
    
    # Check 1: Authentication audit logging
    auth_logs = [l for l in _audit_logs.values() 
                 if l.get("category") == "authentication" 
                 and l.get("timestamp", datetime.min) >= now - timedelta(hours=24)]
    checks.append(ComplianceCheck(
        check_name="authentication_logging",
        status="pass" if len(auth_logs) > 0 else "warning",
        description="Authentication events are being logged",
        last_checked=now,
        details={"events_logged": len(auth_logs)},
    ))
    
    # Check 2: Error monitoring
    error_logs = [l for l in _audit_logs.values() 
                  if l.get("level") in ["error", "critical"]
                  and l.get("timestamp", datetime.min) >= now - timedelta(hours=24)]
    checks.append(ComplianceCheck(
        check_name="error_monitoring",
        status="pass" if len(error_logs) < 10 else "warning" if len(error_logs) < 50 else "fail",
        description="Monitor error rates",
        last_checked=now,
        details={"errors_24h": len(error_logs)},
    ))
    
    # Check 3: Data access logging
    data_logs = [l for l in _audit_logs.values() 
                 if l.get("category") == "data_access"
                 and l.get("timestamp", datetime.min) >= now - timedelta(hours=24)]
    checks.append(ComplianceCheck(
        check_name="data_access_logging",
        status="pass" if len(data_logs) > 0 else "warning",
        description="Data access events are being logged",
        last_checked=now,
        details={"access_events_24h": len(data_logs)},
    ))
    
    return checks


@router.delete("/logs/cleanup")
async def cleanup_old_logs(
    days: int = Query(90, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clean up audit logs older than specified days."""
    # In production, this should require admin privileges
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    to_delete = [log_id for log_id, log in _audit_logs.items() 
                 if log.get("timestamp", datetime.utcnow()) < cutoff]
    
    for log_id in to_delete:
        del _audit_logs[log_id]
    
    return {
        "message": f"Cleaned up {len(to_delete)} old audit logs",
        "deleted_count": len(to_delete),
        "older_than_days": days,
    }


# Auto-log endpoint access for auditing
@router.get("/health")
async def auditor_health():
    """Health check endpoint for the auditor service."""
    return {
        "status": "ok",
        "total_logs": len(_audit_logs),
        "service": "auditor-v1",
    }
