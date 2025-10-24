"""
Standalone decorators for Playgent
"""
import functools
import inspect
import logging
import uuid
from typing import Callable, Dict

from .types import parse_endpoint_event

logger = logging.getLogger(__name__)

# Global function registry for replay testing
# Stores the wrapped functions for replay
_function_registry: Dict[str, Callable] = {}


def record(func):
    """
    Decorator to record function calls for replay testing.

    This decorator records function calls and their arguments, automatically
    managing sessions and emitting events to the Playgent backend.

    Usage:
        from playgent import record

        @record
        def my_function(arg1, arg2):
            ...

    The decorator automatically:
    - Initializes Playgent from environment variables if needed
    - Creates sessions as needed
    - Records function calls with their arguments
    - Manages OpenAI event tracking

    Args:
        func: The function to decorate

    Returns:
        A wrapped version of the function that records calls
    """
    from . import core, state

    # Get function name and create registry key
    func_name = func.__name__
    function_key = f"{func.__module__}:{func_name}"

    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Ensure Playgent is initialized
            core.ensure_initialized()

            # Convert args to kwargs using function signature
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            all_kwargs = dict(bound_args.arguments)

            # Get session ID from global context
            effective_session_id = state._session_context.get()

            # If no session_id exists, create one
            if not effective_session_id:
                effective_session_id = core.create_session()
                logger.info(f"No session_id found, created new session: {effective_session_id}")

            # Generate unique endpoint identifier
            endpoint_id = f"{func_name}_{uuid.uuid4()}"

            # Always start (enables OpenAI event emission)
            core.start(session_id=effective_session_id, endpoint=endpoint_id)

            # Emit endpoint event with all kwargs and function_key
            endpoint_event = parse_endpoint_event(
                name=func_name,
                kwargs=all_kwargs,
                function_key=function_key
            )
            # Set unique endpoint identifier
            endpoint_event.endpoint = endpoint_id
            core.emit_event(endpoint_event)

            try:
                # Execute the wrapped function
                response = await func(*args, **kwargs)
                return response
            finally:
                # Always stop (disables OpenAI event emission)
                core.stop()

        # Register the WRAPPED function in global registry
        _function_registry[function_key] = async_wrapper
        return async_wrapper
    else:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Ensure Playgent is initialized
            core.ensure_initialized()

            # Convert args to kwargs using function signature
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            all_kwargs = dict(bound_args.arguments)

            # Get session ID from global context
            effective_session_id = state._session_context.get()

            # If no session_id exists, create one
            if not effective_session_id:
                effective_session_id = core.create_session()
                logger.info(f"No session_id found, created new session: {effective_session_id}")

            # Generate unique endpoint identifier
            endpoint_id = f"{func_name}_{uuid.uuid4()}"

            # Always start (enables OpenAI event emission)
            core.start(session_id=effective_session_id, endpoint=endpoint_id)

            # Emit endpoint event with all kwargs and function_key
            endpoint_event = parse_endpoint_event(
                name=func_name,
                kwargs=all_kwargs,
                function_key=function_key
            )
            # Set unique endpoint identifier
            endpoint_event.endpoint = endpoint_id
            core.emit_event(endpoint_event)

            try:
                # Execute the wrapped function
                response = func(*args, **kwargs)
                return response
            finally:
                # Always stop (disables OpenAI event emission)
                core.stop()

        # Register the WRAPPED function in global registry
        _function_registry[function_key] = sync_wrapper
        return sync_wrapper


def get_function_registry():
    """Get the global function registry for debugging/testing"""
    return _function_registry