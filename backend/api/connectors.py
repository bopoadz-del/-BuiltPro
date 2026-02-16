"""API surface for reporting connector health and status."""

from __future__ import annotations

import json
import os
from typing import Any, Dict

import httpx
from fastapi import APIRouter

from backend.connectors.factory import get_connector_status

router = APIRouter()

_DEFAULT_TIMEOUT = 5.0


@router.get("/connectors/status")
def list_connectors() -> Dict[str, Dict[str, Any]]:
    """
    Get status of all connectors including stub mode information.
    
    Returns connector health, configuration status, and whether
    each connector is running in stub mode.
    """
    return get_connector_status()


@router.get("/connectors/list")
def list_connectors_legacy() -> Dict[str, Dict[str, Any]]:
    """Legacy endpoint - redirects to status."""
    return get_connector_status()
