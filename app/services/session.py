"""Redis-backed session storage for per-user conversation state.

Each WhatsApp user gets a JSON blob in Redis keyed by their sender ID.
Sessions auto-expire after `session_ttl` seconds.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

import redis.asyncio as redis

from app.config import settings
from app.models.schemas import SessionState, TriageState

_redis: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """Return the shared Redis connection, creating it on first call."""
    global _redis
    if _redis is None:
        _redis = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def close_redis() -> None:
    """Close the shared Redis connection on app shutdown."""
    global _redis
    if _redis is not None:
        await _redis.close()
        _redis = None


def _session_key(user_id: str) -> str:
    """Build the Redis key for a user's session."""
    return f"roadsos:session:{user_id}"


async def load_session(user_id: str) -> SessionState:
    """Load a user's session from Redis, or create a fresh one.

    Args:
        user_id: Twilio sender identifier (e.g. 'whatsapp:+1234567890').

    Returns:
        The user's SessionState, either restored or newly created.
    """
    r = await get_redis()
    key = _session_key(user_id)
    raw = await r.get(key)
    if raw is not None:
        data = json.loads(raw)
        return SessionState(**data)
    return SessionState(user_id=user_id, triage_state=TriageState.ACTIVATION)


async def save_session(session: SessionState) -> None:
    """Persist a session to Redis with TTL.

    Args:
        session: The SessionState to save.
    """
    session.last_activity = datetime.utcnow()
    r = await get_redis()
    key = _session_key(session.user_id)
    await r.set(key, session.model_dump_json(), ex=settings.session_ttl)
