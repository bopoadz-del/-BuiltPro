"""
Connector factory with automatic stub/production switching.

This module provides a factory pattern for creating connectors
with automatic fallback to stub implementations when:
1. USE_STUB_CONNECTORS environment variable is set to "true"
2. The real service credentials are not configured
3. The real service is unavailable
"""

import os
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

# Environment variable to force stub mode
USE_STUBS = os.getenv("USE_STUB_CONNECTORS", "false").lower() == "true"


class BaseConnector(ABC):
    """Base class for all connectors."""
    
    name: str = "base"
    is_stub: bool = False
    
    @abstractmethod
    def check_health(self) -> Dict[str, Any]:
        """Check connector health status."""
        pass
    
    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """Get connector configuration."""
        pass


# =============================================================================
# Procore Connector
# =============================================================================

class ProcoreConnector(BaseConnector):
    """Real Procore connector."""
    name = "procore"
    
    def __init__(self):
        self.api_key = os.getenv("PROCORE_API_KEY")
        self.base_url = os.getenv("PROCORE_BASE_URL", "https://api.procore.com")
    
    def check_health(self) -> Dict[str, Any]:
        import requests
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            resp = requests.get(f"{self.base_url}/rest/v1.0/me", headers=headers, timeout=10)
            resp.raise_for_status()
            return {"status": "connected", "user": resp.json().get("login")}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def get_config(self) -> Dict[str, Any]:
        return {"base_url": self.base_url, "has_api_key": bool(self.api_key)}


class ProcoreStub(BaseConnector):
    """Stub Procore connector for development/testing."""
    name = "procore"
    is_stub = True
    
    def check_health(self) -> Dict[str, Any]:
        return {"status": "stubbed", "message": "Procore connector in stub mode"}
    
    def get_config(self) -> Dict[str, Any]:
        return {"mode": "stub", "note": "Set PROCORE_API_KEY for real connection"}


# =============================================================================
# Aconex Connector
# =============================================================================

class AconexConnector(BaseConnector):
    """Real Oracle Aconex connector."""
    name = "aconex"
    
    def __init__(self):
        self.api_key = os.getenv("ACONEX_API_KEY")
        self.base_url = os.getenv("ACONEX_BASE_URL")
    
    def check_health(self) -> Dict[str, Any]:
        import requests
        try:
            if not self.api_key:
                raise ValueError("ACONEX_API_KEY not configured")
            headers = {"Authorization": f"Bearer {self.api_key}"}
            resp = requests.get(f"{self.base_url}/api/health", headers=headers, timeout=10)
            resp.raise_for_status()
            return {"status": "connected"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def get_config(self) -> Dict[str, Any]:
        return {"base_url": self.base_url, "has_api_key": bool(self.api_key)}


class AconexStub(BaseConnector):
    """Stub Aconex connector."""
    name = "aconex"
    is_stub = True
    
    def check_health(self) -> Dict[str, Any]:
        return {"status": "stubbed", "message": "Aconex connector in stub mode"}
    
    def get_config(self) -> Dict[str, Any]:
        return {"mode": "stub", "note": "Set ACONEX_API_KEY for real connection"}


# =============================================================================
# Primavera P6 Connector
# =============================================================================

class PrimaveraConnector(BaseConnector):
    """Real Primavera P6 connector."""
    name = "primavera"
    
    def __init__(self):
        self.username = os.getenv("PRIMAVERA_USERNAME")
        self.password = os.getenv("PRIMAVERA_PASSWORD")
        self.base_url = os.getenv("PRIMAVERA_BASE_URL")
    
    def check_health(self) -> Dict[str, Any]:
        import requests
        try:
            if not all([self.username, self.password]):
                raise ValueError("PRIMAVERA credentials not configured")
            resp = requests.get(
                f"{self.base_url}/p6ws/rest/health",
                auth=(self.username, self.password),
                timeout=10
            )
            resp.raise_for_status()
            return {"status": "connected"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def get_config(self) -> Dict[str, Any]:
        return {
            "base_url": self.base_url,
            "has_credentials": bool(self.username and self.password)
        }


class PrimaveraStub(BaseConnector):
    """Stub Primavera P6 connector."""
    name = "primavera"
    is_stub = True
    
    def check_health(self) -> Dict[str, Any]:
        return {"status": "stubbed", "message": "Primavera connector in stub mode"}
    
    def get_config(self) -> Dict[str, Any]:
        return {"mode": "stub", "note": "Set PRIMAVERA_USERNAME/PASSWORD for real connection"}


# =============================================================================
# Google Drive Connector
# =============================================================================

class GoogleDriveConnector(BaseConnector):
    """Real Google Drive connector."""
    name = "google_drive"
    
    def __init__(self):
        self.service_account_file = os.getenv("GOOGLE_SERVICE_ACCOUNT")
    
    def check_health(self) -> Dict[str, Any]:
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            
            if not self.service_account_file:
                raise ValueError("GOOGLE_SERVICE_ACCOUNT not configured")
            
            credentials = service_account.Credentials.from_service_account_file(
                self.service_account_file,
                scopes=["https://www.googleapis.com/auth/drive.readonly"]
            )
            service = build("drive", "v3", credentials=credentials)
            # Test with a simple API call
            service.about().get(fields="user").execute()
            return {"status": "connected"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def get_config(self) -> Dict[str, Any]:
        return {"has_service_account": bool(self.service_account_file)}


class GoogleDriveStub(BaseConnector):
    """Stub Google Drive connector."""
    name = "google_drive"
    is_stub = True
    
    def check_health(self) -> Dict[str, Any]:
        return {"status": "stubbed", "message": "Google Drive connector in stub mode"}
    
    def get_config(self) -> Dict[str, Any]:
        return {"mode": "stub", "note": "Set GOOGLE_SERVICE_ACCOUNT for real connection"}


# =============================================================================
# Slack Connector
# =============================================================================

class SlackConnector(BaseConnector):
    """Real Slack connector."""
    name = "slack"
    
    def __init__(self):
        self.bot_token = os.getenv("SLACK_BOT_TOKEN")
        self.webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    
    def check_health(self) -> Dict[str, Any]:
        import requests
        try:
            if self.bot_token:
                headers = {"Authorization": f"Bearer {self.bot_token}"}
                resp = requests.get("https://slack.com/api/auth.test", headers=headers, timeout=10)
                data = resp.json()
                if data.get("ok"):
                    return {"status": "connected", "team": data.get("team")}
                return {"status": "error", "error": data.get("error")}
            elif self.webhook_url:
                return {"status": "webhook_configured"}
            else:
                raise ValueError("No Slack credentials configured")
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def get_config(self) -> Dict[str, Any]:
        return {
            "has_bot_token": bool(self.bot_token),
            "has_webhook": bool(self.webhook_url)
        }


class SlackStub(BaseConnector):
    """Stub Slack connector."""
    name = "slack"
    is_stub = True
    
    def check_health(self) -> Dict[str, Any]:
        return {"status": "stubbed", "message": "Slack connector in stub mode"}
    
    def get_config(self) -> Dict[str, Any]:
        return {"mode": "stub", "note": "Set SLACK_BOT_TOKEN or SLACK_WEBHOOK_URL"}


# =============================================================================
# OpenAI Connector
# =============================================================================

class OpenAIConnector(BaseConnector):
    """Real OpenAI connector."""
    name = "openai"
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
    
    def check_health(self) -> Dict[str, Any]:
        try:
            import openai
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY not configured")
            client = openai.OpenAI(api_key=self.api_key)
            # Test with a simple models list call
            client.models.list()
            return {"status": "connected"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def get_config(self) -> Dict[str, Any]:
        return {"has_api_key": bool(self.api_key)}


class OpenAIStub(BaseConnector):
    """Stub OpenAI connector."""
    name = "openai"
    is_stub = True
    
    def check_health(self) -> Dict[str, Any]:
        return {"status": "stubbed", "message": "OpenAI connector in stub mode"}
    
    def get_config(self) -> Dict[str, Any]:
        return {"mode": "stub", "note": "Set OPENAI_API_KEY for real connection"}


# =============================================================================
# Connector Factory
# =============================================================================

_CONNECTOR_MAP = {
    "procore": (ProcoreConnector, ProcoreStub),
    "aconex": (AconexConnector, AconexStub),
    "primavera": (PrimaveraConnector, PrimaveraStub),
    "google_drive": (GoogleDriveConnector, GoogleDriveStub),
    "slack": (SlackConnector, SlackStub),
    "openai": (OpenAIConnector, OpenAIStub),
}


def get_connector(name: str) -> BaseConnector:
    """
    Get a connector by name.
    
    Automatically returns a stub if:
    - USE_STUB_CONNECTORS env var is "true"
    - The real connector fails to initialize
    
    Args:
        name: Connector name (procore, aconex, primavera, google_drive, slack, openai)
        
    Returns:
        Connector instance (real or stub)
    """
    if name not in _CONNECTOR_MAP:
        raise ValueError(f"Unknown connector: {name}")
    
    real_class, stub_class = _CONNECTOR_MAP[name]
    
    # Force stub mode via environment variable
    if USE_STUBS:
        return stub_class()
    
    # Try to create real connector
    try:
        connector = real_class()
        # Verify it has necessary configuration
        config = connector.get_config()
        has_config = any(config.values())
        if not has_config:
            return stub_class()
        return connector
    except Exception:
        # Fall back to stub on any error
        return stub_class()


def get_all_connectors() -> Dict[str, BaseConnector]:
    """Get all connectors."""
    return {name: get_connector(name) for name in _CONNECTOR_MAP.keys()}


def get_connector_status() -> Dict[str, Dict[str, Any]]:
    """Get status of all connectors."""
    return {
        name: {
            "health": connector.check_health(),
            "config": connector.get_config(),
            "is_stub": connector.is_stub,
        }
        for name, connector in get_all_connectors().items()
    }
