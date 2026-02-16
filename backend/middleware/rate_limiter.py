"""
Rate limiting utilities for the Blank App.

This module sets up a global rate limiter using SlowAPI with Redis
backend for distributed rate limiting across multiple workers.
"""

import os
from slowapi import Limiter
from slowapi.util import get_remote_address

# Get Redis URL for distributed rate limiting
REDIS_URL = os.getenv("REDIS_URL")

# Storage URI - use Redis if available, otherwise memory (for single instance)
if REDIS_URL:
    # Use Redis for distributed rate limiting
    storage_uri = REDIS_URL
else:
    # Fallback to memory storage (only works for single instance)
    storage_uri = "memory://"

# Initialise a Limiter that keys off the client's IP address.
# Uses Redis storage when REDIS_URL is configured for distributed deployments.
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=storage_uri,
)
