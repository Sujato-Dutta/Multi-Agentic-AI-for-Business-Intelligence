"""Supabase logger — logs ONLY explicit agent events to Supabase, not all Python logs."""

import logging
import os
import threading
import uuid
import time
from collections import deque
from typing import Any

logger = logging.getLogger(__name__)

# ─── Supabase client (singleton) ────────────────────────────────────

_supabase_client = None
_supabase_enabled = False
_supabase_lock = threading.Lock()
_buffer: deque[dict[str, Any]] = deque()
_TABLE = "agent_logs"
_BATCH_SIZE = 5
_FLUSH_INTERVAL = 3.0


def _init_supabase() -> bool:
    """Initialize Supabase client once."""
    global _supabase_client, _supabase_enabled
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_KEY", "")
    if not url or not key:
        logger.info("Supabase logging disabled (SUPABASE_URL/SUPABASE_KEY not set)")
        return False
    try:
        from supabase import create_client
        _supabase_client = create_client(url, key)
        _supabase_enabled = True
        # Start background flush thread
        t = threading.Thread(target=_flush_loop, daemon=True)
        t.start()
        logger.info("Supabase logging enabled")
        return True
    except Exception as e:
        logger.warning("Supabase logging failed to initialize: %s", e)
        return False


def _flush() -> None:
    """Flush buffer to Supabase. Called with lock held."""
    if not _buffer or not _supabase_client:
        return
    batch = list(_buffer)
    _buffer.clear()
    threading.Thread(target=_send_batch, args=(batch,), daemon=True).start()


def _send_batch(batch: list[dict]) -> None:
    """Send a batch of logs to Supabase."""
    try:
        _supabase_client.table(_TABLE).insert(batch).execute()  # type: ignore
    except Exception as e:
        print(f"[SupabaseLogger] Failed to send {len(batch)} logs: {e}")


def _flush_loop() -> None:
    """Background thread that flushes the buffer periodically."""
    while True:
        time.sleep(_FLUSH_INTERVAL)
        with _supabase_lock:
            _flush()


# ─── Session tracking ───────────────────────────────────────────────

_current_session: threading.local = threading.local()


def new_session_id() -> str:
    """Generate a new session ID for a request."""
    sid = str(uuid.uuid4())[:12]
    _current_session.id = sid
    return sid


def get_session_id() -> str:
    """Get the current session ID."""
    return getattr(_current_session, "id", "unknown")


# ─── Public API — the ONLY way to log to Supabase ───────────────────

def log_agent_event(
    *,
    agent: str,
    event: str,
    message: str = "",
    detail: dict | None = None,
    query: str | None = None,
    data_source: str | None = None,
    grounding_score: float | None = None,
    duration_ms: int | None = None,
    level: str = "INFO",
) -> None:
    """
    Log a structured agent event.
    - Always prints to console via standard logging
    - Only sends to Supabase if enabled (env vars set)
    - ONLY this function writes to Supabase — no random Python logs leak through
    """
    global _supabase_enabled

    # Console log (always)
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.log(log_level, "[%s] %s: %s", agent, event, message)

    # Supabase log (only if enabled)
    if not _supabase_enabled:
        return

    row: dict[str, Any] = {
        "session_id": get_session_id(),
        "level": level.upper(),
        "agent": agent,
        "event": event,
        "message": message or f"{agent}: {event}",
    }
    if query is not None:
        row["query"] = query
    if data_source is not None:
        row["data_source"] = data_source
    if grounding_score is not None:
        row["grounding_score"] = grounding_score
    if duration_ms is not None:
        row["duration_ms"] = duration_ms
    if detail is not None:
        row["detail"] = detail

    with _supabase_lock:
        _buffer.append(row)
        if len(_buffer) >= _BATCH_SIZE:
            _flush()
