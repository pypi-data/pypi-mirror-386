"""Basic functionality tests for Playgent SDK."""

import os
from unittest.mock import MagicMock, patch

import pytest

from playgent import create_session, init, reset, state


class TestInitialization:
    """Test SDK initialization."""

    def setup_method(self):
        """Reset state before each test."""
        reset()

    def test_init_with_parameters(self):
        """Test initialization with explicit parameters."""
        api_key = "test-api-key"
        server_url = "https://test.server.com"

        init(api_key=api_key, server_url=server_url)

        assert state.api_key == api_key
        assert state.server_url == server_url

    @patch.dict(os.environ, {
        'PLAYGENT_API_KEY': 'env-api-key',
        'PLAYGENT_SERVER_URL': 'https://env.server.com'
    })
    def test_init_from_environment(self):
        """Test initialization from environment variables."""
        init()

        assert state.api_key == 'env-api-key'
        assert state.server_url == 'https://env.server.com'

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        init(api_key="test-key")

        assert state.api_key == "test-key"
        assert state.server_url == "http://localhost:1338"  # Default value from state.py
        assert state.batch_size == 10  # Default value from state.py

    def test_reset(self):
        """Test that reset clears the state."""
        init(api_key="test-key", server_url="https://test.com")
        assert state.api_key == "test-key"

        reset()

        assert state.api_key is None
        assert state.server_url == "http://localhost:1338"  # Reset sets to default
        assert state.session_id is None


class TestSessionManagement:
    """Test session creation and management."""

    def setup_method(self):
        """Initialize SDK before each test."""
        reset()
        init(api_key="test-key")

    @patch('httpx.post')
    def test_create_session(self, mock_post):
        """Test session creation."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "session_id": "test-session-123",
            "person_id": "user-123"
        }
        mock_post.return_value = mock_response

        session_id = create_session(person_id="user-123")

        assert session_id == "test-session-123"

        # Verify the API was called correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://localhost:1338/sessions"  # Using default server URL

    @patch('httpx.post')
    def test_create_session_with_test_case(self, mock_post):
        """Test session creation with test case ID."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "session_id": "test-session-456",
            "test_case_id": "test-case-789"
        }
        mock_post.return_value = mock_response

        session_id = create_session(test_case_id="test-case-789")

        assert session_id == "test-session-456"


class TestRecordDecorator:
    """Test the @record decorator."""

    def setup_method(self):
        """Initialize SDK before each test."""
        reset()
        init(api_key="test-key")

    @patch('playgent.core.create_session')
    def test_record_decorator_sync(self, mock_create_session):
        """Test @record decorator with synchronous function."""
        from playgent import record

        mock_create_session.return_value = "test-session-789"

        @record
        def test_function(x, y):
            return x + y

        result = test_function(2, 3)

        assert result == 5
        mock_create_session.assert_called_once()

    @patch('playgent.core.create_session')
    @pytest.mark.asyncio
    async def test_record_decorator_async(self, mock_create_session):
        """Test @record decorator with asynchronous function."""
        from playgent import record

        mock_create_session.return_value = "test-session-async"

        @record
        async def async_test_function(x, y):
            return x * y

        result = await async_test_function(4, 5)

        assert result == 20
        mock_create_session.assert_called_once()


class TestStateManagement:
    """Test global state management."""

    def test_context_variables(self):
        """Test that context variables work correctly."""
        from playgent import state

        # Set initial values using the context variable
        state._session_context.set("session-1")

        # In a different context, values should be isolated
        import contextvars

        def isolated_function():
            assert state._session_context.get() == "session-1"
            state._session_context.set("session-2")
            assert state._session_context.get() == "session-2"

        # Run in isolated context
        ctx = contextvars.copy_context()
        ctx.run(isolated_function)

        # Original context should be unchanged
        assert state._session_context.get() == "session-1"