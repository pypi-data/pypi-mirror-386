"""Test that the package imports correctly."""



def test_package_imports():
    """Test that the main package can be imported."""
    import playgent
    assert playgent is not None


def test_version_exists():
    """Test that the package version is defined."""
    import playgent
    assert hasattr(playgent, '__version__')
    assert playgent.__version__ == "0.1.0"


def test_core_imports():
    """Test that core functions can be imported."""
    from playgent import (
        create_session,
        evaluate,
        get_session,
        get_session_events,
        init,
        replay_test,
        reset,
        session,
    )

    assert init is not None
    assert session is not None
    assert reset is not None
    assert create_session is not None
    assert get_session_events is not None
    assert get_session is not None
    assert replay_test is not None
    assert evaluate is not None


def test_decorator_imports():
    """Test that decorators can be imported."""
    from playgent import record
    assert record is not None


def test_type_imports():
    """Test that data types can be imported."""
    from playgent import EndpointEvent, EvaluationResult, Session, TestCase

    assert EndpointEvent is not None
    assert Session is not None
    assert TestCase is not None
    assert EvaluationResult is not None


def test_openai_client_imports():
    """Test that the OpenAI client replacements can be imported."""
    from playgent.openai import OpenAI
    assert OpenAI is not None

    # AsyncOpenAI might not be available if using older OpenAI versions
    try:
        from playgent.openai import AsyncOpenAI
        assert AsyncOpenAI is not None
    except ImportError:
        pass  # It's okay if AsyncOpenAI is not available