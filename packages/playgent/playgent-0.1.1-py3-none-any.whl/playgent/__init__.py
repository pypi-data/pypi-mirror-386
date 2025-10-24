"""Playgent SDK for tracking OpenAI API calls"""

__version__ = "0.1.1"

from .core import (
    create_session,
    evaluate,
    get_session,
    get_session_events,
    init,
    replay_test,
    reset,
    session,
)
from .decorators import record
from .types import EndpointEvent, EvaluationResult, Session, TestCase

# Main exports
__all__ = [
    # Core functions
    "init",
    "record",
    "session",
    "create_session",
    "reset",
    # New testing functions
    "get_session_events",
    "get_session",
    "replay_test",
    "evaluate",
    # Data models
    "EndpointEvent",
    "Session",
    "TestCase",
    "EvaluationResult"
]