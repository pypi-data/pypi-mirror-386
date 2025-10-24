"""
Core functionality for Playgent SDK

This module provides all the functions that were previously methods on PlaygentClient.
"""

import atexit
import contextvars
import logging
import os
import threading
import time
import uuid
from queue import Empty, Queue
from typing import Any, Dict, List, Optional, Tuple

from . import state
from .types import EndpointEvent, EvaluationResult, Event, Session

logger = logging.getLogger(__name__)


class SessionContext:
    """Context manager for temporarily setting a session ID in the global context"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.token = None

    def __enter__(self):
        """Set the session ID when entering the context"""
        self.token = state._session_context.set(self.session_id)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Reset the session ID when exiting the context"""
        if self.token is not None:
            state._session_context.reset(self.token)


def init(api_key: Optional[str] = None, server_url: Optional[str] = None):
    """Initialize Playgent with configuration

    Args:
        api_key: API key for authentication. If not provided, reads from PLAYGENT_API_KEY env var
        server_url: Backend server URL. If not provided, uses default or PLAYGENT_SERVER_URL env var

    Raises:
        ValueError: If no API key is provided and PLAYGENT_API_KEY is not set
    """
    # Set API key with thread safety
    with state._state_lock:
        state.api_key = api_key or os.getenv("PLAYGENT_API_KEY")
        if not state.api_key:
            raise ValueError(
                "Playgent API key is required. Either:\n"
                "1. Set PLAYGENT_API_KEY environment variable\n"
                "2. Call playgent.init(api_key='your-key')"
            )

        # Set server URL
        if server_url:
            # Validate server URL starts with https://
            if not server_url.startswith("https://"):
                raise ValueError("Server URL must use HTTPS for security")
            state.server_url = server_url
        else:
            env_server_url = os.getenv("PLAYGENT_SERVER_URL")
            if env_server_url:
                if not env_server_url.startswith("https://"):
                    raise ValueError("Server URL from environment must use HTTPS for security")
                state.server_url = env_server_url

    logger.info(f"Playgent initialized with server URL: {state.server_url}")


def ensure_initialized():
    """Ensure Playgent is initialized, auto-initialize if possible"""
    if state.api_key is None:
        init()  # Will raise if no env var is set


def create_session(person_id: Optional[str] = None, test_case_id: Optional[str] = None) -> str:
    """Create a new session via the backend API

    Args:
        person_id: Optional person ID to associate with the session
        test_case_id: Optional test case ID for test sessions

    Returns:
        The newly created session ID

    Raises:
        Exception: If session creation fails
    """
    ensure_initialized()

    try:
        import httpx
        headers = {
            "Authorization": f"Bearer {state.api_key}",
            "Content-Type": "application/json"
        }

        payload = {}
        if person_id:
            payload["person_id"] = person_id
        if test_case_id:
            payload["test_case_id"] = test_case_id

        response = httpx.post(
            f"{state.server_url}/sessions",
            json=payload,
            headers=headers,
            timeout=5.0
        )

        if response.status_code == 201:
            data = response.json()
            session_id: str = data.get("session_id", "")
            if not session_id:
                raise Exception("Server returned empty session_id")
            # Basic validation: session_id should be alphanumeric with hyphens
            import re
            if not re.match(r'^[a-zA-Z0-9\-_]+$', session_id):
                raise ValueError("Invalid session_id format received from server")
            logger.info(f"Created new session: {session_id}")
            return session_id
        else:
            raise Exception(f"Failed to create session (status {response.status_code})")
    except Exception as e:
        # Never expose API key in errors
        error_msg = str(e).replace(state.api_key, "***") if state.api_key and state.api_key in str(e) else str(e)
        logger.error(f"Failed to create session: {error_msg}")
        raise Exception(f"Failed to create session: {error_msg}") from e


def set_session(session_id: str):
    """Set the session ID for the current context

    This allows you to override the session ID within a decorated function.
    The session ID is stored in a contextvar, making it thread-safe and async-safe.

    Args:
        session_id: The session ID to use for the current context
    """
    state._session_context.set(session_id)


def session(session_id: Optional[str] = None):
    """Context manager for temporarily setting a session ID

    Usage:
        with session("my-session-id"):
            # All calls within this block use the specified session_id
            my_function("Hello")
            my_function("World")

    Args:
        session_id: The session ID to use within the context. If None, creates a new session.

    Returns:
        A context manager that sets and restores the session ID
    """
    if session_id is None:
        session_id = create_session()
    return SessionContext(session_id)


def emit_event(event: Event):
    """Add event to queue for emission"""
    if state.event_queue is not None:
        try:
            # Add session fields with thread safety
            with state._state_lock:
                if state.person_id:
                    event.person_id = state.person_id
                if state.session_id:
                    event.session_id = state.session_id
                if state.endpoint:
                    event.endpoint = state.endpoint
            state.event_queue.put_nowait(event.to_dict())
        except Exception as e:
            logger.debug(f"Event queue full, dropping event: {e}")  # Log but don't expose sensitive data


def event_sender_worker():
    """Background thread worker to send events in batches"""
    import httpx

    client = httpx.Client(timeout=2.0)
    max_batch_size = min(state.batch_size, 100)  # Cap at 100 events per batch

    while not state.stop_sender.is_set():
        batch = []

        # Try to collect up to max_batch_size events
        for _ in range(max_batch_size):
            try:
                # Wait up to 0.5 seconds for each event
                event = state.event_queue.get(timeout=0.5)
                batch.append(event)
            except Empty:
                # No more events available, send what we have
                break

        # Send batch if we collected any events
        if batch:
            try:
                headers = {
                    "Authorization": f"Bearer {state.api_key}"
                }

                client.post(
                    f"{state.server_url}/events",
                    json={"events": batch},
                    headers=headers,
                    timeout=1.0
                )
            except Exception as e:
                # Sanitize error to avoid exposing API key
                error_msg = str(e).replace(state.api_key, "***") if state.api_key and state.api_key in str(e) else str(e)
                logger.error(f"Failed to send events: {error_msg}")

    # Send any remaining events before shutting down
    remaining = []
    while not state.event_queue.empty():
        try:
            remaining.append(state.event_queue.get_nowait())
        except Empty:
            break

    if remaining:
        try:
            headers = {
                "Authorization": f"Bearer {state.api_key}"
            }

            client.post(
                f"{state.server_url}/events",
                json={"events": remaining},
                headers=headers,
                timeout=1.0
            )
        except Exception as e:
            # Sanitize error to avoid exposing API key
            error_msg = str(e).replace(state.api_key, "***") if state.api_key and state.api_key in str(e) else str(e)
            logger.error(f"Failed to send remaining events: {error_msg}")

    client.close()


def start(session_id: Optional[str] = None, person_id: Optional[str] = None, endpoint: Optional[str] = None):
    """Start a Playgent tracking session"""
    ensure_initialized()

    if state.is_running:
        logger.warning("Playgent is already running")
        return

    if not session_id:
        # Get from context or create new
        session_id = state._session_context.get()
        if not session_id:
            try:
                import httpx
                headers = {
                    "Authorization": f"Bearer {state.api_key}",
                    "Content-Type": "application/json"
                }

                payload = {}
                if person_id:
                    payload["person_id"] = person_id

                response = httpx.post(
                    f"{state.server_url}/sessions",
                    json=payload,
                    headers=headers,
                    timeout=5.0
                )

                if response.status_code == 201:
                    data = response.json()
                    session_id = data.get("session_id")
                    logger.info(f"Created new session via API: {session_id}")
                else:
                    # Fallback to UUID if API call fails
                    logger.warning(f"Failed to create session via API (status {response.status_code}), falling back to UUID")
                    session_id = str(uuid.uuid4())
            except Exception as e:
                # Sanitize error to avoid exposing API key
                error_msg = str(e).replace(state.api_key, "***") if state.api_key and state.api_key in str(e) else str(e)
                logger.warning(f"Failed to create session via API: {error_msg}, falling back to UUID")
                session_id = str(uuid.uuid4())

    # Use lock for thread-safe state modification
    with state._state_lock:
        state.session_id = session_id
        state.person_id = person_id  # Can be None
        state.endpoint = endpoint  # Can be None

        # Start event sender thread
        state.stop_sender.clear()
        state.sender_thread = threading.Thread(target=event_sender_worker, daemon=True)
        state.sender_thread.start()
    logger.info(f"Event emission enabled - sending to {state.server_url}")
    logger.info(f"Session ID: {state.session_id}")
    if state.person_id:
        logger.info(f"Person ID: {state.person_id}")

    # Register shutdown handler to ensure cleanup
    atexit.register(shutdown)


    state.is_running = True
    logger.info("🎯 Playgent SDK started - All OpenAI API calls will be logged")


def stop():
    """End the current Playgent tracking session"""
    if not state.is_running:
        logger.warning("Playgent is not running")
        return

    if state.session_id:
        try:
            import httpx
            headers = {
                "Authorization": f"Bearer {state.api_key}",
                "Content-Type": "application/json"
            }

            response = httpx.patch(
                f"{state.server_url}/sessions/{state.session_id}",
                json={"status": "completed"},
                headers=headers,
                timeout=5.0
            )

            if response.status_code == 200:
                logger.info(f"Session {state.session_id} marked as completed")
            else:
                logger.warning(f"Failed to update session status (status {response.status_code})")
        except Exception as e:
            logger.warning(f"Failed to update session status: {e}")


    # Shutdown event sender if running
    shutdown()

    state.is_running = False
    logger.info("🚫 Playgent SDK stopped")


def shutdown():
    """Gracefully shutdown the event sender and flush remaining events"""
    if state.sender_thread and state.sender_thread.is_alive():
        logger.info("Shutting down Playgent event sender...")
        state.stop_sender.set()
        max_wait = 2.0
        start_time = time.time()

        while not state.event_queue.empty() and (time.time() - start_time) < max_wait:
            time.sleep(0.1)

        if not state.event_queue.empty():
            remaining = state.event_queue.qsize()
            logger.warning(f"Queue still has {remaining} events after {max_wait}s timeout")

        state.sender_thread.join(timeout=1.0)

        if state.sender_thread.is_alive():
            logger.warning("Event sender thread did not stop gracefully")
        else:
            logger.info("✅ Playgent event sender shut down successfully")


def get_session_events(session_id: str) -> List[EndpointEvent]:
    """Get all events for a session, properly typed

    Args:
        session_id: The session ID to fetch events from

    Returns:
        List of EndpointEvent objects with 'arguments' attribute
    """
    ensure_initialized()

    import httpx
    client = httpx.Client(timeout=10.0)

    try:
        headers = {
            "Authorization": f"Bearer {state.api_key}"
        }

        # Fetch all endpoint events for this session
        response = client.get(
            f"{state.server_url}/events",
            params={
                "session_id": session_id,
                "event_type": "endpoint",
                "limit": 1000
            },
            headers=headers
        )

        if response.status_code != 200:
            raise Exception(f"Failed to fetch events (status {response.status_code})")

        result = response.json()
        events = result.get("events", [])

        # Sort by timestamp to ensure correct order
        events.sort(key=lambda e: e.get("timestamp", ""))

        # Transform to EndpointEvent objects
        endpoint_events = []
        for event in events:
            data = event.get("data", {})

            # Parse data if it's a JSON string
            if isinstance(data, str):
                import json
                try:
                    data = json.loads(data)
                except (json.JSONDecodeError, ValueError) as e:
                    logger.error(f"Failed to parse event data as JSON: {e}")
                    data = {}  # Use empty dict as fallback

            endpoint_event = EndpointEvent(
                name=data.get("name", ""),
                arguments=data.get("kwargs", {}),
                function_key=data.get("function_key", ""),
                timestamp=event.get("timestamp", ""),
                id=event.get("id", "")
            )
            endpoint_events.append(endpoint_event)

        logger.info(f"Retrieved {len(endpoint_events)} endpoint events from session {session_id}")
        return endpoint_events

    finally:
        client.close()


def get_session(session_id: str) -> Session:
    """Get session details from backend

    Args:
        session_id: The session ID to fetch

    Returns:
        Session object with all details including eval_output
    """
    ensure_initialized()

    import httpx
    client = httpx.Client(timeout=10.0)

    try:
        headers = {
            "Authorization": f"Bearer {state.api_key}"
        }

        response = client.get(
            f"{state.server_url}/sessions/{session_id}/status",
            headers=headers
        )

        if response.status_code == 404:
            raise Exception(f"Session {session_id} not found")
        elif response.status_code != 200:
            raise Exception(f"Failed to fetch session (status {response.status_code})")

        session_data = response.json()
        return Session.from_dict(session_data)

    finally:
        client.close()


class ReplayTestContext:
    """Context manager for replay_test function"""

    def __init__(self, test_case_id: str):
        self.test_case_id = test_case_id
        self.session_id: Optional[str] = None
        self.endpoint_events: List[EndpointEvent] = []
        self.client: Optional[Any] = None  # Will be httpx.Client
        self.headers: Optional[Dict[str, str]] = None

    def __enter__(self) -> Tuple[str, List[EndpointEvent]]:
        """Enter context - create session and fetch events"""
        ensure_initialized()

        import httpx
        self.client = httpx.Client(timeout=10.0)
        self.headers = {
            "Authorization": f"Bearer {state.api_key}"
        }

        # Fetch test case to get annotated_session
        assert self.client is not None, "Client should be initialized"
        assert self.headers is not None, "Headers should be initialized"
        response = self.client.get(
            f"{state.server_url}/tests/{self.test_case_id}",
            headers=self.headers
        )

        if response.status_code != 200:
            raise Exception(f"Failed to fetch test case (status {response.status_code})")

        test_case = response.json()
        annotated_session_id = test_case.get("annotated_session")

        if not annotated_session_id:
            raise Exception(f"Test case {self.test_case_id} has no annotated_session configured")

        logger.info(f"Using annotated_session {annotated_session_id} from test case {self.test_case_id}")

        # Create new session for this test run
        self.session_id = create_session(test_case_id=self.test_case_id)

        # Update session status to "running"
        assert self.client is not None, "Client should be initialized"
        assert self.headers is not None, "Headers should be initialized"
        self.client.patch(
            f"{state.server_url}/sessions/{self.session_id}",
            json={"status": "running"},
            headers=self.headers
        )

        # Get endpoint events from the annotated session
        self.endpoint_events = get_session_events(annotated_session_id)

        # Set session context
        state._session_context.set(self.session_id)

        assert self.session_id is not None, "Session ID should be created"
        return self.session_id, self.endpoint_events

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context - cleanup"""
        # Clear session context
        state._session_context.set(None)

        if self.client:
            self.client.close()


def replay_test(test_case_id: str) -> ReplayTestContext:
    """Context manager for replaying a test case

    Creates a new session and fetches endpoint events from the test's annotated session.

    Usage:
        with replay_test(test_case_id) as (session_id, endpoint_events):
            for event in endpoint_events:
                my_func(**event.arguments)

            result = evaluate(test_case_id, session_id)
            assert result.score > 3

    Args:
        test_case_id: The test case ID to replay

    Returns:
        Context manager that yields (session_id, endpoint_events)
    """
    return ReplayTestContext(test_case_id)


def evaluate(test_case_id: str, session_id: str, wait: bool = True, max_wait: int = 30) -> EvaluationResult:
    """Get or trigger evaluation for a session

    Args:
        test_case_id: The test case ID
        session_id: The session ID to evaluate
        wait: Whether to wait for evaluation to complete (default True)
        max_wait: Maximum seconds to wait for evaluation (default 30)

    Returns:
        EvaluationResult with score, passed status, and criteria details
    """
    ensure_initialized()

    import time

    import httpx

    client = httpx.Client(timeout=10.0)

    try:
        headers = {
            "Authorization": f"Bearer {state.api_key}"
        }

        # First, check if evaluation already exists
        session = get_session(session_id)

        if session.eval_output:
            # Evaluation already exists, return it
            logger.info(f"Found existing evaluation for session {session_id}")
            return EvaluationResult.from_eval_output(
                session.eval_output,
                session_id=session_id,
                test_case_id=test_case_id
            )

        # No evaluation yet, trigger it
        logger.info(f"Triggering evaluation for session {session_id}")

        # Update session status to evaluating
        client.patch(
            f"{state.server_url}/sessions/{session_id}",
            json={"status": "evaluating"},
            headers=headers
        )

        # Trigger evaluation
        response = client.get(
            f"{state.server_url}/tests/{test_case_id}/sessions/{session_id}/evaluate",
            headers=headers
        )

        if response.status_code != 202:
            raise Exception(f"Failed to trigger evaluation (status {response.status_code})")

        if not wait:
            # Return empty result if not waiting
            return EvaluationResult(
                score=0,
                passed=False,
                average_score=0,
                criteria=[],
                session_id=session_id,
                test_case_id=test_case_id
            )

        # Wait for evaluation to complete
        start_time = time.time()
        while (time.time() - start_time) < max_wait:
            time.sleep(2)  # Poll every 2 seconds

            session = get_session(session_id)
            if session.eval_output:
                logger.info(f"Evaluation complete for session {session_id}")
                return EvaluationResult.from_eval_output(
                    session.eval_output,
                    session_id=session_id,
                    test_case_id=test_case_id
                )

            if session.status == "complete":
                # Session is complete but no eval_output
                logger.warning(f"Session {session_id} complete but no evaluation found")
                break

        # Timeout or no evaluation
        logger.warning(f"Evaluation did not complete within {max_wait} seconds")
        return EvaluationResult(
            score=0,
            passed=False,
            average_score=0,
            criteria=[],
            session_id=session_id,
            test_case_id=test_case_id
        )

    finally:
        client.close()


def reset():
    """Reset all global state (useful for testing)"""
    with state._state_lock:
        state.api_key = None
        state.server_url = "http://localhost:1338"
        state.batch_size = 10
        state.session_id = None
        state.person_id = None
        state.endpoint = None
        state.is_running = False
        state.events = []
        state.event_queue = Queue()
        state.sender_thread = None
        state.stop_sender.clear()
        # Reset context var
        state._session_context = contextvars.ContextVar('playgent_session', default=None)