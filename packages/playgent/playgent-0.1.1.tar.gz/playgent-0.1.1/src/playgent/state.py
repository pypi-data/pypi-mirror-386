"""
Global state management for Playgent SDK

This module maintains all global state that was previously managed by PlaygentClient instances.
"""

import contextvars
import threading
from queue import Queue
from typing import List, Optional

from .types import Event

# Configuration (initialized from environment or explicit init)
api_key: Optional[str] = None
server_url: str = "https://run.blaxel.ai/pharmie-agents/agents/playgent"  # Default, can be overridden
batch_size: int = 10

# Session state
session_id: Optional[str] = None
person_id: Optional[str] = None
endpoint: Optional[str] = None

# Thread-safe context variable for session management
_session_context: contextvars.ContextVar = contextvars.ContextVar('playgent_session', default=None)

# Runtime state
is_running: bool = False
events: List[Event] = []
event_queue: Queue = Queue()
sender_thread: Optional[threading.Thread] = None
stop_sender: threading.Event = threading.Event()

# Lock for thread-safe state modifications
_state_lock = threading.Lock()