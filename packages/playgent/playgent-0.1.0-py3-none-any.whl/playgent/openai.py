"""Wrapped OpenAI clients that integrate with Playgent tracking"""

import functools
import logging

from openai import AsyncOpenAI as BaseAsyncOpenAI
from openai import OpenAI as BaseOpenAI

from . import core, state
from .types import parse_openai_input_item, parse_openai_response_item

logger = logging.getLogger(__name__)


class OpenAI(BaseOpenAI):
    """
    Drop-in replacement for OpenAI client with automatic Playgent tracking.

    Usage:
        from playgent.openai import OpenAI
        from playgent import record

        client = OpenAI()  # Use exactly like regular OpenAI

        @record  # Decorator handles all tracking
        def my_function():
            response = client.responses.create(...)
            return response
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Wrap the responses.create method
        self._wrap_responses_create()

    def _wrap_responses_create(self):
        """Wrap the responses.create method to track events"""
        original_create = self.responses.create

        @functools.wraps(original_create)
        def wrapped_create(*args, **kwargs):
            # Check if Playgent tracking is active via global state
            if state.is_running:
                try:
                    inputs = kwargs.get("input", [])
                    instructions = kwargs.get("instructions", "")

                    # Create and emit input event
                    input_event = parse_openai_input_item(inputs, instructions)

                    # Add session fields from global state
                    if state.person_id:
                        input_event.person_id = state.person_id
                    if state.session_id:
                        input_event.session_id = state.session_id
                    if state.endpoint:
                        input_event.endpoint = state.endpoint

                    # Track and emit
                    state.events.append(input_event)
                    core.emit_event(input_event)

                    # Call original method
                    result = original_create(*args, **kwargs)

                    # Process output events
                    if hasattr(result, "output"):
                        for item in getattr(result, "output", []):
                            typed_event = parse_openai_response_item(item, input_event.id)
                            if typed_event is not None:
                                # Add session fields from global state
                                if state.person_id:
                                    typed_event.person_id = state.person_id
                                if state.session_id:
                                    typed_event.session_id = state.session_id
                                if state.endpoint:
                                    typed_event.endpoint = state.endpoint

                                state.events.append(typed_event)
                                core.emit_event(typed_event)

                    return result

                except Exception as e:
                    logger.error(f"Error in Playgent tracking: {str(e)}")
                    # Still call original even if tracking fails
                    return original_create(*args, **kwargs)
            else:
                # No active session, just call original
                return original_create(*args, **kwargs)

        self.responses.create = wrapped_create


class AsyncOpenAI(BaseAsyncOpenAI):
    """
    Drop-in replacement for AsyncOpenAI client with automatic Playgent tracking.

    Usage:
        from playgent.openai import AsyncOpenAI
        from playgent import record

        client = AsyncOpenAI()  # Use exactly like regular AsyncOpenAI

        @record  # Decorator handles all tracking
        async def my_function():
            response = await client.responses.create(...)
            return response
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Wrap the responses.create method
        self._wrap_responses_create()

    def _wrap_responses_create(self):
        """Wrap the async responses.create method to track events"""
        original_create = self.responses.create

        @functools.wraps(original_create)
        async def wrapped_create(*args, **kwargs):
            # Check if Playgent tracking is active via global state
            if state.is_running:
                try:
                    inputs = kwargs.get("input", [])
                    instructions = kwargs.get("instructions", "")

                    # Create and emit input event
                    input_event = parse_openai_input_item(inputs, instructions)

                    # Add session fields from global state
                    if state.person_id:
                        input_event.person_id = state.person_id
                    if state.session_id:
                        input_event.session_id = state.session_id
                    if state.endpoint:
                        input_event.endpoint = state.endpoint

                    # Track and emit
                    state.events.append(input_event)
                    core.emit_event(input_event)

                    # Call original method
                    result = await original_create(*args, **kwargs)

                    # Process output events
                    if hasattr(result, "output"):
                        for item in getattr(result, "output", []):
                            typed_event = parse_openai_response_item(item, input_event.id)
                            if typed_event is not None:
                                # Add session fields from global state
                                if state.person_id:
                                    typed_event.person_id = state.person_id
                                if state.session_id:
                                    typed_event.session_id = state.session_id
                                if state.endpoint:
                                    typed_event.endpoint = state.endpoint

                                state.events.append(typed_event)
                                core.emit_event(typed_event)

                    return result

                except Exception as e:
                    logger.error(f"Error in Playgent tracking: {str(e)}")
                    # Still call original even if tracking fails
                    return await original_create(*args, **kwargs)
            else:
                # No active session, just call original
                return await original_create(*args, **kwargs)

        self.responses.create = wrapped_create